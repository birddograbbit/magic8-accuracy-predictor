#!/usr/bin/env python3
"""
FastAPI service for Magic8 predictions
Provides REST API for real-time trade predictions
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
from datetime import datetime, time
import json
import logging
import os
import asyncio
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for model and features
model = None
feature_config = None
feature_names = None
market_data_cache = {}

class TradeRequest(BaseModel):
    """Request model for trade prediction"""
    strategy: str
    symbol: str
    premium: float
    predicted_price: float
    risk: Optional[float] = None
    reward: Optional[float] = None
    
class BatchTradeRequest(BaseModel):
    """Request model for batch predictions"""
    trades: List[TradeRequest]
    
class PredictionResponse(BaseModel):
    """Response model for predictions"""
    timestamp: str
    strategy: str
    symbol: str
    premium: float
    predicted_price: float
    win_probability: float
    prediction: str
    confidence: float
    recommendation: str
    risk_score: float

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    global model, feature_config, feature_names
    
    # Load model
    model_path = 'models/xgboost_phase1.pkl'
    if os.path.exists(model_path):
        model = joblib.load(model_path)
        logger.info(f"Loaded model from {model_path}")
    else:
        logger.warning(f"Model not found at {model_path}")
    
    # Load feature configuration
    feature_config_path = 'data/phase1_processed/feature_info.json'
    if os.path.exists(feature_config_path):
        with open(feature_config_path, 'r') as f:
            feature_config = json.load(f)
        feature_names = feature_config['feature_names']
        logger.info(f"Loaded {len(feature_names)} features")
    else:
        logger.warning(f"Feature config not found at {feature_config_path}")
    
    # Start background tasks
    asyncio.create_task(update_market_data())
    
    yield
    
    # Shutdown
    logger.info("Shutting down prediction service")

# Create FastAPI app
app = FastAPI(
    title="Magic8 Prediction API",
    description="Real-time ML predictions for Magic8 trading system",
    version="1.0.0",
    lifespan=lifespan
)

async def update_market_data():
    """Background task to update market data cache"""
    while True:
        try:
            # In production, this would fetch real market data
            # For now, simulate with random walk
            symbols = ['SPX', 'SPY', 'RUT', 'QQQ', 'XSP', 'NDX', 'AAPL', 'TSLA', 'VIX']
            
            for symbol in symbols:
                if symbol not in market_data_cache:
                    # Initialize with reasonable values
                    if symbol == 'SPX':
                        market_data_cache[symbol] = {'price': 5850.0, 'volatility': 0.15}
                    elif symbol == 'VIX':
                        market_data_cache[symbol] = {'price': 15.0, 'volatility': 0.30}
                    else:
                        market_data_cache[symbol] = {'price': 100.0, 'volatility': 0.20}
                else:
                    # Random walk update
                    current = market_data_cache[symbol]['price']
                    change = np.random.normal(0, current * 0.001)
                    market_data_cache[symbol]['price'] = current + change
                    
        except Exception as e:
            logger.error(f"Error updating market data: {e}")
            
        await asyncio.sleep(60)  # Update every minute

def calculate_features_for_prediction(trade: TradeRequest) -> pd.DataFrame:
    """Calculate features for a single trade prediction"""
    features = pd.DataFrame(index=[0])
    
    # Time features
    now = datetime.now()
    features['hour'] = now.hour
    features['minute'] = now.minute
    features['day_of_week'] = now.weekday()
    
    # Cyclical encoding
    features['hour_sin'] = np.sin(2 * np.pi * now.hour / 24)
    features['hour_cos'] = np.cos(2 * np.pi * now.hour / 24)
    features['minute_sin'] = np.sin(2 * np.pi * now.minute / 60)
    features['minute_cos'] = np.cos(2 * np.pi * now.minute / 60)
    
    # Market session
    current_time = now.time()
    features['is_open_hour'] = int(time(9, 30) <= current_time <= time(10, 30))
    features['is_close_hour'] = int(time(15, 0) <= current_time <= time(16, 0))
    features['minutes_to_close'] = max(0, (16 * 60) - (now.hour * 60 + now.minute))
    
    # Get current market data
    current_price = market_data_cache.get(
        trade.symbol, 
        {'price': trade.predicted_price}
    )['price']
    
    # Price features for all symbols
    symbols = ['SPX', 'SPY', 'RUT', 'QQQ', 'XSP', 'NDX', 'AAPL', 'TSLA']
    for symbol in symbols:
        if symbol == trade.symbol:
            # Active symbol features
            features[f'{symbol}_price'] = current_price
            features[f'{symbol}_sma_20'] = current_price  # Simplified
            features[f'{symbol}_momentum_5'] = 0
            features[f'{symbol}_volatility_20'] = market_data_cache.get(
                symbol, {'volatility': 0.20}
            )['volatility']
            features[f'{symbol}_rsi_14'] = 50
            features[f'{symbol}_price_position'] = 0.5
        else:
            # Zero out other symbols
            features[f'{symbol}_price'] = 0
            features[f'{symbol}_sma_20'] = 0
            features[f'{symbol}_momentum_5'] = 0
            features[f'{symbol}_volatility_20'] = 0
            features[f'{symbol}_rsi_14'] = 0
            features[f'{symbol}_price_position'] = 0
    
    # VIX features
    vix_data = market_data_cache.get('VIX', {'price': 15.0})
    vix_level = vix_data['price']
    features['vix_level'] = vix_level
    features['vix_sma_20'] = vix_level
    features['vix_change_1d'] = 0
    features['vix_change_5d'] = 0
    
    # VIX regime
    for regime in ['low', 'normal', 'elevated', 'high']:
        features[f'vix_regime_{regime}'] = 0
    
    if vix_level < 12:
        features['vix_regime_low'] = 1
    elif vix_level < 20:
        features['vix_regime_normal'] = 1
    elif vix_level < 30:
        features['vix_regime_elevated'] = 1
    else:
        features['vix_regime_high'] = 1
    
    # Strategy encoding
    strategies = ['Butterfly', 'Iron Condor', 'Vertical', 'Sonar']
    for strategy in strategies:
        features[f'strategy_{strategy}'] = int(trade.strategy == strategy)
    
    # Trade features
    features['premium'] = trade.premium
    features['premium_pct_of_price'] = (trade.premium / current_price) * 100
    features['predicted_move'] = trade.predicted_price - current_price
    features['predicted_move_pct'] = (
        (trade.predicted_price - current_price) / current_price
    ) * 100
    
    # Risk/reward
    if trade.risk and trade.reward:
        features['risk_reward_ratio'] = trade.risk / max(trade.reward, 0.01)
    else:
        # Default based on strategy
        if trade.strategy == 'Iron Condor':
            features['risk_reward_ratio'] = 10.0
        elif trade.strategy == 'Butterfly':
            features['risk_reward_ratio'] = 1.0
        else:
            features['risk_reward_ratio'] = 5.0
    
    features['trade_probability'] = 0.5  # Default
    
    # Ensure all features are present
    for feature in feature_names:
        if feature not in features.columns:
            features[feature] = 0
            
    return features[feature_names]

def calculate_risk_score(trade: TradeRequest, win_probability: float) -> float:
    """Calculate risk score for the trade"""
    # Risk factors
    risk_score = 0.0
    
    # High VIX increases risk
    vix = market_data_cache.get('VIX', {'price': 15})['price']
    if vix > 30:
        risk_score += 0.3
    elif vix > 20:
        risk_score += 0.2
    elif vix < 12:
        risk_score += 0.1
    
    # Low win probability increases risk
    risk_score += (1 - win_probability) * 0.4
    
    # Strategy-specific risk
    if trade.strategy == 'Iron Condor':
        risk_score += 0.2  # Higher risk strategy
    elif trade.strategy == 'Butterfly':
        risk_score += 0.1
    
    # Time decay risk for 0DTE
    now = datetime.now()
    minutes_to_close = (16 * 60) - (now.hour * 60 + now.minute)
    if minutes_to_close < 120:  # Last 2 hours
        risk_score += 0.2
    
    return min(risk_score, 1.0)

def get_recommendation(win_probability: float, risk_score: float) -> str:
    """Generate trade recommendation based on probability and risk"""
    if win_probability >= 0.7 and risk_score < 0.4:
        return "STRONG BUY"
    elif win_probability >= 0.6 and risk_score < 0.5:
        return "BUY"
    elif win_probability >= 0.5 and risk_score < 0.6:
        return "HOLD"
    elif win_probability < 0.4 or risk_score > 0.7:
        return "AVOID"
    else:
        return "CAUTION"

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "model_loaded": model is not None,
        "features_loaded": feature_names is not None,
        "market_data_symbols": list(market_data_cache.keys())
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict_single_trade(trade: TradeRequest):
    """Predict outcome for a single trade"""
    
    if model is None or feature_names is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Calculate features
        features = calculate_features_for_prediction(trade)
        
        # Make prediction
        win_probability = float(model.predict_proba(features)[0, 1])
        prediction = "WIN" if win_probability >= 0.5 else "LOSS"
        confidence = max(win_probability, 1 - win_probability)
        
        # Calculate risk score
        risk_score = calculate_risk_score(trade, win_probability)
        
        # Get recommendation
        recommendation = get_recommendation(win_probability, risk_score)
        
        response = PredictionResponse(
            timestamp=datetime.now().isoformat(),
            strategy=trade.strategy,
            symbol=trade.symbol,
            premium=trade.premium,
            predicted_price=trade.predicted_price,
            win_probability=win_probability,
            prediction=prediction,
            confidence=confidence,
            recommendation=recommendation,
            risk_score=risk_score
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/batch")
async def predict_batch_trades(request: BatchTradeRequest):
    """Predict outcomes for multiple trades"""
    
    if model is None or feature_names is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    predictions = []
    
    for trade in request.trades:
        try:
            pred = await predict_single_trade(trade)
            predictions.append(pred.dict())
        except Exception as e:
            logger.error(f"Error predicting trade {trade}: {e}")
            predictions.append({
                "error": str(e),
                "trade": trade.dict()
            })
    
    return {
        "predictions": predictions,
        "total": len(predictions),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/market-data/{symbol}")
async def get_market_data(symbol: str):
    """Get current market data for a symbol"""
    
    if symbol not in market_data_cache:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    
    return {
        "symbol": symbol,
        "data": market_data_cache[symbol],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/feature-importance")
async def get_feature_importance():
    """Get feature importance from the model"""
    
    if model is None or not hasattr(model, 'feature_importances_'):
        raise HTTPException(status_code=503, detail="Feature importance not available")
    
    importances = model.feature_importances_
    feature_importance = [
        {"feature": feature_names[i], "importance": float(importances[i])}
        for i in np.argsort(importances)[-20:][::-1]
    ]
    
    return {
        "top_features": feature_importance,
        "total_features": len(feature_names)
    }

if __name__ == "__main__":
    import uvicorn
    
    # Run the FastAPI server
    uvicorn.run(
        "prediction_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
