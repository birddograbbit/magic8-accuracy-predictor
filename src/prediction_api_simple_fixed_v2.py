#!/usr/bin/env python3
"""
Fixed Magic8 Prediction API with proper market data management.
Version 2: Persistent subscriptions, no double cancellation.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from contextlib import asynccontextmanager
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
import warnings

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
active_tickers = {}  # Track active market data subscriptions

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
    'TSLA': 200.0,
    'XSP': 585.0
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

def init_ib_connection():
    """Initialize IB connection at module level."""
    global ib, ib_connected
    
    try:
        logger.info("Connecting to IB Gateway on port 7497...")
        ib = IB()
        ib.connect('127.0.0.1', 7497, clientId=99)
        
        if ib.isConnected():
            ib_connected = True
            logger.info("✓ Connected to IB Gateway")
            return True
        else:
            logger.info("✗ Failed to connect to IB Gateway")
            return False
            
    except Exception as e:
        logger.info(f"IB connection failed: {e}")
        ib_connected = False
        return False

def setup_market_data_subscriptions():
    """Set up persistent market data subscriptions for all symbols."""
    global active_tickers
    
    if not ib_connected or not ib or not ib.isConnected():
        logger.info("Skipping market data setup - no IB connection")
        return
    
    symbols = ['SPX', 'SPY', 'XSP', 'NDX', 'QQQ', 'RUT', 'AAPL', 'TSLA', 'VIX']
    
    for symbol in symbols:
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
            
            # Request persistent market data
            ticker = ib.reqMktData(contract, '', False, False)
            active_tickers[symbol] = ticker
            logger.info(f"✓ Set up market data for {symbol}")
            
        except Exception as e:
            logger.warning(f"Failed to set up market data for {symbol}: {e}")

def get_ib_price(symbol: str) -> float:
    """Get price from existing market data subscription."""
    global active_tickers
    
    if symbol not in active_tickers:
        raise Exception(f"No active subscription for {symbol}")
    
    ticker = active_tickers[symbol]
    
    # Wait briefly for updated data
    timeout = 1.0
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if ticker.last and not math.isnan(ticker.last):
            return float(ticker.last)
        elif ticker.close and not math.isnan(ticker.close):
            return float(ticker.close)
        time.sleep(0.1)
    
    # If no live data, try using cached values
    if ticker.close and not math.isnan(ticker.close):
        return float(ticker.close)
    
    raise Exception(f"No price data available for {symbol}")

# Connect at module import time
init_ib_connection()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global ib, ib_connected
    
    # Startup
    logger.info("Starting Magic8 Prediction API (Fixed v2)...")
    
    # Load model and features
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, module="xgboost")
        warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
        
        if not load_model_and_features():
            logger.error("Failed to load model/features")
    
    # Set up persistent market data subscriptions
    if ib_connected:
        setup_market_data_subscriptions()
        logger.info("✓ Ready with IB connection and market data")
    else:
        logger.warning("✗ Running without IB - will use mock data")
    
    yield  # Application runs here
    
    # Shutdown - Clean cancellation of active subscriptions only
    logger.info("Shutting down...")
    
    if ib and ib.isConnected():
        try:
            # Cancel only our tracked active subscriptions
            for symbol, ticker in active_tickers.items():
                try:
                    ib.cancelMktData(ticker)
                    logger.debug(f"Cancelled market data for {symbol}")
                except Exception as e:
                    logger.debug(f"Error cancelling {symbol}: {e}")
            
            active_tickers.clear()
            ib.disconnect()
            logger.info("✓ Disconnected from IB")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    ib_connected = False
    logger.info("Shutdown complete")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Magic8 Prediction API (Fixed v2)",
    description="Fixed prediction API with proper market data management",
    version="3.2.0",
    lifespan=lifespan
)

def get_market_data(symbol: str) -> Dict:
    """Get market data with caching and improved error handling."""
    global market_data_cache
    
    with cache_lock:
        # Check cache
        if symbol in market_data_cache:
            cache_entry = market_data_cache[symbol]
            age = time.time() - cache_entry['timestamp']
            if age < CACHE_TTL_SECONDS:
                return cache_entry['data']
    
    # Try to get live price from persistent subscription
    try:
        price = get_ib_price(symbol)
        data = {
            'price': price,
            'volatility': 0.20,  # Default volatility
            'source': 'ibkr'
        }
        logger.debug(f"Got live price for {symbol}: {price}")
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
    
    model_paths = [
        'models/xgboost_phase1_model.pkl',
        'models/phase1/xgboost_model.pkl'
    ]
    
    for model_path in model_paths:
        if os.path.exists(model_path):
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=UserWarning, module="xgboost")
                    warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
                    
                    model = joblib.load(model_path)
                    logger.info(f"✓ Loaded model from {model_path}")
                    
                    # Verify model compatibility
                    if hasattr(model, 'predict_proba'):
                        dummy_df = pd.DataFrame([[0.0] * 74])
                        _ = model.predict_proba(dummy_df)
                        logger.info("✓ Model compatibility verified")
                    
                    break
            except Exception as e:
                logger.error(f"Error loading model from {model_path}: {e}")
                continue
    
    if model is None:
        logger.error("✗ No valid model found")
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

@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "model_loaded": model is not None,
        "features_loaded": feature_names is not None,
        "ib_connected": ib_connected,
        "active_subscriptions": len(active_tickers),
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
            "ib_connection": "connected" if ib_connected else "disconnected",
            "market_data": f"{len(active_tickers)} active subscriptions"
        }
    }

def build_features(request: TradeRequest) -> pd.DataFrame:
    """Build feature vector from trade request."""
    # Get current time info
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    day_of_week = now.weekday()
    
    # Calculate temporal features
    hour_angle = 2 * np.pi * hour / 24
    hour_sin = np.sin(hour_angle)
    hour_cos = np.cos(hour_angle)
    
    # Market hours (9:30 AM - 4:00 PM ET)
    market_open_time = now.replace(hour=9, minute=30, second=0)
    market_close_time = now.replace(hour=16, minute=0, second=0)
    is_market_open = market_open_time <= now <= market_close_time
    is_open_30min = market_open_time <= now <= market_open_time.replace(minute=0, hour=10)
    is_close_30min = now >= market_close_time.replace(minute=30, hour=15)
    
    # Minutes to close
    if is_market_open:
        minutes_to_close = (market_close_time - now).seconds / 60
    else:
        minutes_to_close = 0
    
    # Get market data for all symbols
    symbols = ['SPX', 'SPY', 'XSP', 'NDX', 'QQQ', 'RUT', 'AAPL', 'TSLA']
    market_data = {}
    for symbol in symbols:
        market_data[symbol] = get_market_data(symbol)
    
    # Get VIX data
    vix_data = get_market_data('VIX')
    vix_level = vix_data['price']
    
    # Build complete feature dict
    features = {
        # Temporal features
        'hour': hour,
        'minute': minute,
        'day_of_week': day_of_week,
        'hour_sin': hour_sin,
        'hour_cos': hour_cos,
        'is_market_open': int(is_market_open),
        'is_open_30min': int(is_open_30min),
        'is_close_30min': int(is_close_30min),
        'minutes_to_close': minutes_to_close,
    }
    
    # Price features for each symbol
    for symbol in symbols:
        price = market_data[symbol]['price']
        volatility = market_data[symbol]['volatility']
        
        # Calculate technical indicators (simplified)
        features[f'{symbol}_close'] = price
        features[f'{symbol}_sma_20'] = price  # Approximate with current price
        features[f'{symbol}_momentum_5'] = 0.0  # Neutral momentum
        features[f'{symbol}_volatility_20'] = volatility
        features[f'{symbol}_rsi'] = 50.0  # Neutral RSI
        features[f'{symbol}_price_position'] = 0.5  # Middle of range
    
    # VIX features
    features['vix'] = vix_level
    features['vix_vix_sma_20'] = vix_level
    features['vix_vix_change'] = 0.0
    
    # VIX regime features
    features['vix_regime_low'] = int(vix_level < 12)
    features['vix_regime_normal'] = int(12 <= vix_level < 20)
    features['vix_regime_elevated'] = int(20 <= vix_level < 30)
    features['vix_regime_high'] = int(vix_level >= 30)
    
    # Strategy features (one-hot encoding)
    features['strategy_Butterfly'] = int(request.strategy == 'Butterfly')
    features['strategy_Iron Condor'] = int(request.strategy == 'Iron Condor')
    features['strategy_Sonar'] = int(request.strategy == 'Sonar')
    features['strategy_Vertical'] = int(request.strategy == 'Vertical')
    
    # Trade features
    spx_price = market_data['SPX']['price']
    features['premium_normalized'] = request.premium / spx_price
    
    # Risk/reward ratio
    risk = request.risk if request.risk else request.premium
    reward = request.reward if request.reward else request.premium * 3
    features['risk_reward_ratio'] = (reward / risk) if risk > 0 else 3.0
    
    # Add predicted price features
    features['pred_predicted'] = request.predicted_price
    features['pred_price'] = spx_price
    features['pred_difference'] = abs(request.predicted_price - spx_price)
    features['prof_premium'] = request.premium
    
    # Create DataFrame
    df = pd.DataFrame([features])
    
    # Ensure all features are present in correct order
    missing_features = set(feature_names) - set(df.columns)
    if missing_features:
        logger.warning(f"Missing features: {missing_features}")
        for feat in missing_features:
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
        
        # Log feature summary for debugging
        non_zero_features = (features_df != 0).sum(axis=1).values[0]
        logger.info(f"Non-zero features: {non_zero_features}/{len(feature_names)}")
        
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