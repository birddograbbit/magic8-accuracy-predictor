#!/usr/bin/env python3
"""FastAPI service using real-time feature generator and DataManager."""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import joblib
import numpy as np
import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from data_manager import DataManager
from feature_engineering.real_time_features import RealTimeFeatureGenerator
from models.multi_model import SymbolModelStrategy, MultiModelPredictor

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
predictor: MultiModelPredictor | None = None
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
    if model_map:
        strategy = SymbolModelStrategy(model_map)
        predictor = MultiModelPredictor(strategy)
        predictor.load_models()
        logger.info("Loaded %d symbol specific models", len(predictor.models))
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
        proba = predictor.predict_proba(req.symbol, X)[0][1]
    else:
        proba = model.predict_proba(X)[0][1]
    data = await manager.get_market_data(req.symbol)

    return PredictionResponse(
        timestamp=datetime.now().isoformat(),
        symbol=req.symbol,
        strategy=req.strategy,
        win_probability=float(proba),
        prediction="WIN" if proba >= 0.5 else "LOSS",
        data_source=data["source"],
        n_features=len(features),
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
