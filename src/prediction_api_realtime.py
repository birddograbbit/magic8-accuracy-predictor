#!/usr/bin/env python3
"""FastAPI service using real-time feature generator and DataManager."""

import os
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "prediction_api.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

import joblib
import numpy as np
import yaml
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from data_manager import DataManager
from feature_engineering.real_time_features import RealTimeFeatureGenerator
from models.hierarchical_predictor import HierarchicalPredictor
from risk_reward_calculator import RiskRewardCalculator
from cache_manager import CacheManager
from utils.prediction_logger import PredictionLogger

MODEL_PATH = "models/xgboost_phase1_model.pkl"
FEATURE_INFO_PATH = "data/phase1_processed/feature_info.json"
CONFIG_PATH = "config/config.yaml"

class TradeRequest(BaseModel):
    strategy: str
    symbol: str
    premium: float
    predicted_price: float
    short_term: Optional[float] = None
    long_term: Optional[float] = None
    strikes: Optional[List[float]] = Field(default_factory=list)
    action: Optional[str] = None
    option_type: Optional[str] = None
    quantity: int = 1
    risk: Optional[float] = None
    reward: Optional[float] = None


class TradeInstruction(BaseModel):
    symbol: str
    strategy: str
    strikes: List[float]
    premium: float
    action: str
    quantity: int = 1
    option_type: Optional[str] = None

class PredictionResponse(BaseModel):
    timestamp: str
    symbol: str
    strategy: str
    win_probability: float
    prediction: str
    data_source: str
    n_features: int


class BatchTradeRequest(BaseModel):
    requests: List[TradeRequest]
    share_market_data: bool = True


class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
    batch_metrics: Dict[str, int]

model = None
predictor: HierarchicalPredictor | None = None
thresholds_individual: dict = {}
thresholds_grouped: dict = {}
feature_gen: RealTimeFeatureGenerator
manager: DataManager
cache_manager: CacheManager
batch_max_size: int = 10
prediction_logger: PredictionLogger | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global model, feature_gen, manager, predictor
    
    # Load config
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    perf_cfg = cfg.get("performance", {}).get("cache", {})
    manager = DataManager({**cfg.get("data_source", {}), "performance": {"cache": perf_cfg}})
    await manager.connect()

    feature_gen = RealTimeFeatureGenerator(manager, feature_info_path=FEATURE_INFO_PATH)
    global cache_manager
    cache_manager = CacheManager(
        feature_ttl=perf_cfg.get("feature_ttl", 60),
        prediction_ttl=perf_cfg.get("prediction_ttl", 300),
        max_size=perf_cfg.get("max_size", 1000),
    )
    global batch_max_size
    batch_cfg = cfg.get("performance", {}).get("batch_predictions", {})
    batch_max_size = batch_cfg.get("max_batch_size", 10)

    monitor_cfg = cfg.get("integration", {}).get("monitoring", {})
    if monitor_cfg.get("enabled") and monitor_cfg.get("track_predictions") and monitor_cfg.get("save_to_file"):
        log_file = monitor_cfg.get("predictions_file", "logs/predictions.jsonl")
        global prediction_logger
        prediction_logger = PredictionLogger(log_file)

    # Multi-model configuration
    model_map = cfg.get('models')
    symbol_strategy_dir = cfg.get('symbol_strategy_models', {}).get('dir')

    if model_map:
        # Load symbol-strategy models if present
        symbol_strategy_paths = {}
        if symbol_strategy_dir:
            for p in Path(symbol_strategy_dir).glob('*_model.pkl'):
                key = p.stem.replace('_model', '')
                symbol_strategy_paths[key] = str(p)

        predictor = HierarchicalPredictor(
            symbol_strategy_paths=symbol_strategy_paths,
            symbol_paths={k: v for k, v in model_map.items() if k != 'default'},
            default_path=model_map.get('default'),
        )
        logger.info(
            "Loaded %d symbol-strategy models, %d symbol models",
            len(predictor.symbol_strategy_models),
            len(predictor.symbol_models),
        )

        # Load thresholds for individual models
        threshold_path = Path("models/individual/thresholds.json")
        if threshold_path.exists():
            with open(threshold_path) as f:
                thresholds_individual.update(json.load(f))
            logger.info("Loaded individual thresholds for %d symbols", len(thresholds_individual))

        # Load thresholds for grouped models
        grouped_threshold_path = Path("models/grouped/thresholds_grouped.json")
        if grouped_threshold_path.exists():
            with open(grouped_threshold_path) as f:
                thresholds_grouped.update(json.load(f))
            logger.info("Loaded grouped thresholds for %d groups", len(thresholds_grouped))
    else:
        model = joblib.load(MODEL_PATH)
        logger.info("Model loaded, feature generator ready")
    
    yield
    
    # Shutdown
    await manager.disconnect()

app = FastAPI(title="Magic8 Real-Time Prediction API", lifespan=lifespan)

@app.get("/market/{symbol}")
async def market(symbol: str):
    data = await manager.get_market_data(symbol.upper())
    return {
        "symbol": symbol.upper(),
        "price": data["price"],
        "volatility": data["volatility"],
        "source": data["source"],
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/calculate_risk_reward")
async def calculate_risk_reward(request: TradeInstruction):
    """Return risk/reward metrics for a trade instruction."""
    calc = RiskRewardCalculator()

    if request.strategy == "Butterfly":
        result = calc.calculate_butterfly(
            request.strikes, request.premium, request.action, request.quantity
        )
    elif request.strategy in ["Iron Condor", "Sonar"]:
        result = calc.calculate_iron_condor(
            request.strikes, request.premium, request.action, request.quantity
        )
    elif request.strategy == "Vertical":
        result = calc.calculate_vertical(
            request.strikes,
            request.premium,
            request.action,
            request.option_type or "CALL",
            request.quantity,
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {request.strategy}")

    return {
        "symbol": request.symbol,
        "strategy": request.strategy,
        "risk": result["max_loss"],
        "reward": result["max_profit"],
        "risk_reward_ratio": result["risk_reward_ratio"],
        "breakevens": {k: v for k, v in result.items() if "breakeven" in k},
    }


async def _predict_trade(req: TradeRequest) -> PredictionResponse:
    if model is None and predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    order = req.model_dump()
    ts = time.time()
    feat_key = cache_manager.get_feature_key(req.symbol, ts)
    features = cache_manager.get_feature(feat_key)
    if features is None:
        features, _ = await feature_gen.generate_features(req.symbol, order)
        cache_manager.set_feature(feat_key, features)

    pred_key = cache_manager.get_prediction_key(req.symbol, req.strategy, features)
    proba = cache_manager.get_prediction(pred_key)

    threshold = 0.5
    if proba is None:
        X = np.array([features])
        if predictor:
            proba = predictor.predict_proba(req.symbol, req.strategy, X)[0][1]

            if req.symbol in predictor.symbol_models or f"{req.symbol}_{req.strategy}" in predictor.symbol_strategy_models:
                sym_thresh = thresholds_individual.get(req.symbol, {})
                threshold = sym_thresh.get(req.strategy, 0.5)
            else:
                for group_name, group_thresholds in thresholds_grouped.items():
                    if req.symbol in group_name.split('_'):
                        threshold = group_thresholds.get(req.symbol, {}).get(req.strategy, 0.5)
                        break
        else:
            proba = model.predict_proba(X)[0][1]
        cache_manager.set_prediction(pred_key, proba)

    data = await manager.get_market_data(req.symbol)

    if (req.risk is None or req.reward is None) and req.strikes:
        calc = RiskRewardCalculator()
        if req.strategy == "Butterfly":
            rr = calc.calculate_butterfly(req.strikes, req.premium, req.action or "BUY", req.quantity)
        elif req.strategy in ["Iron Condor", "Sonar"]:
            rr = calc.calculate_iron_condor(req.strikes, req.premium, req.action or "SELL", req.quantity)
        elif req.strategy == "Vertical":
            rr = calc.calculate_vertical(
                req.strikes,
                req.premium,
                req.action or "SELL",
                req.option_type or "CALL",
                req.quantity,
            )
        else:
            rr = None
        if rr:
            req.risk = rr["max_loss"]
            req.reward = rr["max_profit"]

    response = PredictionResponse(
        timestamp=datetime.now().isoformat(),
        symbol=req.symbol,
        strategy=req.strategy,
        win_probability=float(proba),
        prediction="WIN" if proba >= threshold else "LOSS",
        data_source=data["source"],
        n_features=len(features),
    )

    if prediction_logger:
        await prediction_logger.log_prediction(order, response, threshold)

    return response

@app.post("/predict", response_model=PredictionResponse)
async def predict(req: TradeRequest):
    return await _predict_trade(req)


@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchTradeRequest):
    trades = request.requests[:batch_max_size]
    results = [await _predict_trade(trade) for trade in trades]
    metrics = cache_manager.stats()
    return BatchPredictionResponse(predictions=results, batch_metrics=metrics)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
