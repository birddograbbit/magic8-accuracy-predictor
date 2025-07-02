#!/usr/bin/env python3
"""
Simple Magic8 Prediction API with direct IB connection.
No complex modules, just direct IB usage like the sample scripts.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
import json
import logging
import os
import time
import threading
import math
import asyncio

# IB imports
from ib_insync import IB, Stock, Index, util

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress IB logging noise
util.logToConsole(logging.WARNING)

# Global variables
model = None
feature_names = None
ib = None
ib_connected = False
market_data_cache = {}
cache_lock = threading.Lock()

# Constants
CACHE_TTL_SECONDS = 30
MOCK_PRICES = {
    'SPX': 5850.0,
    'SPY': 585.0,
    'VIX': 15.0,
    'RUT': 2300.0,
    'QQQ': 500.0,
    'NDX': 20000.0,
    'AAPL': 220.0,
    'TSLA': 200.0
}

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
    title="Magic8 Prediction API",
    description="Simple prediction API with direct IB connection",
    version="3.0.0"
)

def connect_ib_sync():
    """Connect to IB Gateway - handle async properly in thread."""
    global ib, ib_connected
    
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        ib = IB()
        logger.info("Connecting to IB Gateway on port 7497...")
        
        # Use util.run to handle the connection properly
        def do_connect():
            ib.connect('127.0.0.1', 7497, clientId=99)
            return ib.isConnected()
        
        # Run the connection
        connected = util.run(do_connect)
        
        if connected:
            ib_connected = True
            logger.info("✓ Connected to IB Gateway")
            return True
        else:
            logger.error("Failed to connect to IB Gateway")
            return False
            
    except Exception as e:
        logger.error(f"IB connection error: {e}")
        ib_connected = False
        return False

def get_ib_price(symbol: str) -> float:
    """Get price from IB - simple and direct."""
    global ib, ib_connected
    
    if not ib_connected or not ib or not ib.isConnected():
        raise Exception("Not connected to IB")
    
    try:
        # Create contract
        if symbol in ['SPX', 'VIX', 'XSP']:
            contract = Index(symbol, 'CBOE', 'USD')
        elif symbol == 'RUT':
            contract = Index('RUT', 'RUSSELL', 'USD')
        elif symbol == 'NDX':
            contract = Index('NDX', 'NASDAQ', 'USD')
        else:
            contract = Stock(symbol, 'SMART', 'USD')
        
        # Request market data
        ticker = ib.reqMktData(contract, '', False, False)
        
        # Wait for price with timeout
        timeout = 2.0
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if ticker.last and not math.isnan(ticker.last):
                price = ticker.last
                break
            elif ticker.close and not math.isnan(ticker.close):
                price = ticker.close
                break
            time.sleep(0.1)
        else:
            ib.cancelMktData(ticker)
            raise Exception(f"Timeout getting price for {symbol}")
        
        # Cancel market data
        ib.cancelMktData(ticker)
        
        return float(price)
        
    except Exception as e:
        logger.debug(f"Error getting IB price for {symbol}: {e}")
        raise

def get_market_data(symbol: str) -> Dict:
    """Get market data with caching."""
    global market_data_cache
    
    with cache_lock:
        # Check cache
        if symbol in market_data_cache:
            cache_entry = market_data_cache[symbol]
            age = time.time() - cache_entry['timestamp']
            if age < CACHE_TTL_SECONDS:
                return cache_entry['data']
    
    # Try to get live price
    try:
        price = get_ib_price(symbol)
        data = {
            'price': price,
            'volatility': 0.20,  # Default volatility
            'source': 'ibkr'
        }
    except Exception as e:
        logger.debug(f"Using mock data for {symbol}: {e}")
        # Use mock data
        data = {
            'price': MOCK_PRICES.get(symbol, 100.0),
            'volatility': 0.30 if symbol == 'VIX' else 0.20,
            'source': 'mock'
        }
    
    # Update cache
    with cache_lock:
        market_data_cache[symbol] = {
            'data': data,
            'timestamp': time.time()
        }
    
    return data

def load_model_and_features():
    """Load model and feature configuration."""
    global model, feature_names
    
    # Load model
    model_path = 'models/xgboost_phase1_model.pkl'
    if os.path.exists(model_path):
        model = joblib.load(model_path)
        logger.info(f"✓ Loaded model from {model_path}")
    else:
        logger.error(f"✗ Model not found at {model_path}")
        return False
    
    # Load feature configuration
    feature_config_path = 'data/phase1_processed/feature_info.json'
    if os.path.exists(feature_config_path):
        with open(feature_config_path, 'r') as f:
            feature_config = json.load(f)
        feature_names = feature_config['feature_names']
        logger.info(f"✓ Loaded {len(feature_names)} features")
    else:
        logger.error(f"✗ Feature config not found at {feature_config_path}")
        return False
    
    return True

@app.on_event("startup")
def startup_event():
    """Initialize on startup."""
    logger.info("Starting Magic8 Prediction API...")
    
    # Load model and features
    if not load_model_and_features():
        logger.error("Failed to load model/features")
    
    # Try to connect to IB in a separate thread to avoid event loop issues
    def connect_thread():
        connect_ib_sync()
    
    thread = threading.Thread(target=connect_thread)
    thread.start()
    thread.join(timeout=5)
    
    if ib_connected:
        logger.info("✓ Ready with IB connection")
    else:
        logger.warning("✗ Running without IB - will use mock data")

@app.on_event("shutdown")
def shutdown_event():
    """Cleanup on shutdown."""
    global ib, ib_connected
    
    logger.info("Shutting down...")
    
    if ib and ib.isConnected():
        try:
            # Cancel any active market data
            for ticker in ib.tickers():
                try:
                    ib.cancelMktData(ticker)
                except:
                    pass
            ib.disconnect()
            logger.info("✓ Disconnected from IB")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    ib_connected = False
    logger.info("Shutdown complete")

@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "model_loaded": model is not None,
        "features_loaded": feature_names is not None,
        "ib_connected": ib_connected,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health():
    """Detailed health check."""
    return {
        "status": "healthy" if model and feature_names else "degraded",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "model": "loaded" if model else "not_loaded",
            "features": f"{len(feature_names)} features" if feature_names else "not_loaded",
            "ib_connection": "connected" if ib_connected else "disconnected"
        }
    }

def build_features(request: TradeRequest) -> pd.DataFrame:
    """Build feature vector from trade request."""
    # Get market data
    spx_data = get_market_data('SPX')
    vix_data = get_market_data('VIX')
    
    # Build feature dict
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
        
        # Calculate confidence
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
async def get_market_data_endpoint(symbol: str):
    """Get current market data for a symbol."""
    try:
        data = get_market_data(symbol.upper())
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
