#!/usr/bin/env python3
"""FastAPI service using real-time feature generator and DataManager."""

import os
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from data_manager import DataManager
from feature_engineering.real_time_features import RealTimeFeatureGenerator
from models.hierarchical_predictor import HierarchicalPredictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_PATH = "models/xgboost_phase1_model.pkl"
FEATURE_INFO_PATH = "data/phase1_processed/feature_info.json"
CONFIG_PATH = "config/config.yaml"

class TradeRequest(BaseModel):
    strategy: str
    symbol: str
    premium: float
    predicted_price: float
    risk: Optional[float] = None
    reward: Optional[float] = None

class PredictionResponse(BaseModel):
    timestamp: str
    symbol: str
    strategy: str
    win_probability: float
    prediction: str
    data_source: str
    n_features: int

model = None
predictor: HierarchicalPredictor | None = None
thresholds_individual: dict = {}
thresholds_grouped: dict = {}
feature_gen: RealTimeFeatureGenerator
manager: DataManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global model, feature_gen, manager, predictor
    
    # Load config
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    manager = DataManager(cfg.get("data_source", {}))
    await manager.connect()
    
    feature_gen = RealTimeFeatureGenerator(manager, feature_info_path=FEATURE_INFO_PATH)

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

@app.post("/predict", response_model=PredictionResponse)
async def predict(req: TradeRequest):
    if model is None and predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    order = req.model_dump()
    features, names = await feature_gen.generate_features(req.symbol, order)
    X = np.array([features])
    if predictor:
        proba = predictor.predict_proba(req.symbol, req.strategy, X)[0][1]

        threshold = 0.5
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
        threshold = 0.5
    data = await manager.get_market_data(req.symbol)

    return PredictionResponse(
        timestamp=datetime.now().isoformat(),
        symbol=req.symbol,
        strategy=req.strategy,
        win_probability=float(proba),
        prediction="WIN" if proba >= threshold else "LOSS",
        data_source=data["source"],
        n_features=len(features),
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
