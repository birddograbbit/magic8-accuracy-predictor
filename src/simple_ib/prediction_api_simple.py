#!/usr/bin/env python3
"""
Simplified FastAPI service for Magic8 predictions.
Uses simple synchronous IB connection.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Set
import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
from datetime import datetime
import json
import logging
import os
import threading
import time

from src.simple_ib import SimpleDataManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
model = None
feature_config = None
feature_names = None
data_manager = None
update_thread = None
stop_updates = False

class TradeRequest(BaseModel):
    """Request model for trade prediction"""
    strategy: str
    symbol: str
    premium: float
    predicted_price: float
    risk: Optional[float] = None
    reward: Optional[float] = None
    
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

# Create FastAPI app
app = FastAPI(
    title="Magic8 Prediction API (Simplified)",
    description="Real-time ML predictions with simple IB connection",
    version="2.0.0"
)

def update_market_data_thread():
    """Background thread to update market data."""
    global data_manager, stop_updates
    symbols = ['SPX', 'VIX']  # Start with just the essentials
    
    while not stop_updates:
        try:
            # Update each symbol
            for symbol in symbols:
                if stop_updates:
                    break
                try:
                    data = data_manager.get_market_data(symbol)
                    logger.debug(f"Updated {symbol}: ${data['price']:.2f}")
                except Exception as e:
                    logger.debug(f"Failed to update {symbol}: {e}")
                    
            # Sleep between updates
            time.sleep(5)  # Update every 5 seconds
            
        except Exception as e:
            logger.error(f"Error in update thread: {e}")
            time.sleep(5)
            
    logger.info("Market data update thread stopped")

@app.on_event("startup")
def startup_event():
    """Initialize on startup."""
    global model, feature_config, feature_names, data_manager, update_thread
    
    logger.info("Starting Magic8 Prediction API (Simplified)...")
    
    # Load model
    model_path = 'models/xgboost_phase1_model.pkl'
    if os.path.exists(model_path):
        model = joblib.load(model_path)
        logger.info(f"✓ Loaded model from {model_path}")
    else:
        logger.error(f"✗ Model not found at {model_path}")
        
    # Load feature configuration  
    feature_config_path = 'data/phase1_processed/feature_info.json'
    if os.path.exists(feature_config_path):
        with open(feature_config_path, 'r') as f:
            feature_config = json.load(f)
        feature_names = feature_config['feature_names']
        logger.info(f"✓ Loaded {len(feature_names)} features")
    else:
        logger.error(f"✗ Feature config not found at {feature_config_path}")
        
    # Initialize data manager with simple config
    config = {
        'ib': {
            'host': '127.0.0.1',
            'port': 7497,
            'client_id': 99
        }
    }
    
    data_manager = SimpleDataManager(config)
    
    # Try to connect to IB
    try:
        if data_manager.connect():
            logger.info("✓ Connected to IB Gateway")
            
            # Start background update thread
            update_thread = threading.Thread(target=update_market_data_thread, daemon=True)
            update_thread.start()
            logger.info("✓ Started market data updates")
        else:
            logger.warning("✗ Could not connect to IB - will use mock data")
    except Exception as e:
        logger.error(f"✗ IB connection error: {e}")
        logger.warning("Will continue with mock data")

@app.on_event("shutdown")
def shutdown_event():
    """Cleanup on shutdown."""
    global stop_updates, data_manager
    
    logger.info("Shutting down...")
    
    # Stop update thread
    stop_updates = True
    if update_thread:
        update_thread.join(timeout=2)
        
    # Disconnect from IB
    if data_manager:
        data_manager.disconnect()
        logger.info("✓ Disconnected from IB")
        
    logger.info("Shutdown complete")

@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "model_loaded": model is not None,
        "features_loaded": feature_names is not None,
        "ib_connected": data_manager.is_connected() if data_manager else False,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health():
    """Detailed health check."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "model": "loaded" if model else "not_loaded",
            "features": f"{len(feature_names)} features" if feature_names else "not_loaded",
            "ib_connection": "connected" if data_manager and data_manager.is_connected() else "disconnected"
        }
    }
    
    # Check if any component is unhealthy
    if not model or not feature_names:
        health_status["status"] = "degraded"
        
    return health_status

def build_features(request: TradeRequest) -> pd.DataFrame:
    """Build feature vector from trade request."""
    global data_manager
    
    # Get market data
    spx_data = data_manager.get_market_data('SPX')
    vix_data = data_manager.get_market_data('VIX')
    
    # Build feature dict (simplified version)
    features = {
        # Basic features
        'premium': request.premium,
        'predicted_price': request.predicted_price,
        'current_price': spx_data['price'],
        'price_distance': abs(request.predicted_price - spx_data['price']),
        'price_distance_pct': abs(request.predicted_price - spx_data['price']) / spx_data['price'],
        
        # VIX features
        'vix_level': vix_data['price'],
        'vix_high': vix_data['price'] > 20,
        'vix_low': vix_data['price'] < 15,
        
        # Strategy features (one-hot encoding)
        'strategy_Butterfly': 1 if request.strategy == 'Butterfly' else 0,
        'strategy_Iron Condor': 1 if request.strategy == 'Iron Condor' else 0,
        'strategy_Vertical': 1 if request.strategy == 'Vertical' else 0,
        'strategy_Sonar': 1 if request.strategy == 'Sonar' else 0,
        
        # Risk/Reward
        'risk': request.risk if request.risk else request.premium,
        'reward': request.reward if request.reward else request.premium * 3,
        'risk_reward_ratio': (request.reward / request.risk) if request.risk and request.risk > 0 else 3.0,
        
        # Market regime  
        'volatility': spx_data['volatility'],
        'high_volatility': spx_data['volatility'] > 0.25,
    }
    
    # Create DataFrame with all required features
    df = pd.DataFrame([features])
    
    # Add any missing features with default values
    for feat in feature_names:
        if feat not in df.columns:
            df[feat] = 0
            
    # Ensure correct column order
    df = df[feature_names]
    
    return df

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: TradeRequest):
    """Make a prediction for a single trade."""
    
    if not model or not feature_names:
        raise HTTPException(status_code=503, detail="Model not loaded")
        
    try:
        # Build features
        features_df = build_features(request)
        
        # Make prediction
        y_pred_proba = model.predict_proba(features_df)[0]
        win_probability = float(y_pred_proba[1])
        
        # Determine recommendation
        if win_probability >= 0.70:
            recommendation = "STRONG BUY"
        elif win_probability >= 0.55:
            recommendation = "BUY"
        elif win_probability >= 0.45:
            recommendation = "HOLD"
        else:
            recommendation = "AVOID"
            
        # Calculate confidence (distance from 0.5)
        confidence = abs(win_probability - 0.5) * 2
        
        # Simple risk score
        risk_score = 1.0 - win_probability
        
        return PredictionResponse(
            timestamp=datetime.now().isoformat(),
            strategy=request.strategy,
            symbol=request.symbol,
            premium=request.premium,
            predicted_price=request.predicted_price,
            win_probability=win_probability,
            prediction="WIN" if win_probability >= 0.55 else "LOSS",
            confidence=confidence,
            recommendation=recommendation,
            risk_score=risk_score
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/{symbol}")
async def get_market_data(symbol: str):
    """Get current market data for a symbol."""
    if not data_manager:
        raise HTTPException(status_code=503, detail="Data manager not initialized")
        
    try:
        data = data_manager.get_market_data(symbol.upper())
        return {
            "symbol": symbol.upper(),
            "price": data['price'],
            "volatility": data['volatility'],
            "source": data['source'],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
