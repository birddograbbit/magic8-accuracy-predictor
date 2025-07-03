#!/usr/bin/env python3
"""
Optimized Magic8 Prediction API for improved performance.
Key optimizations:
- Parallel market data fetching
- Persistent market data subscriptions
- Pre-computed features
- Connection pooling
- Timing instrumentation
"""

import sys
import os

# Disable MallocStackLogging on macOS to prevent warnings
if sys.platform == 'darwin':
    os.environ['MallocStackLogging'] = '0'

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
import time
import threading
import math
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

# IB imports
from ib_insync import IB, Stock, Index, util, Contract

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
active_tickers = {}  # Persistent ticker subscriptions
ticker_lock = threading.Lock()
executor = ThreadPoolExecutor(max_workers=8)  # For parallel operations

# Constants
CACHE_TTL_SECONDS = 60  # Increased cache TTL
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

# Pre-computed features that don't change frequently
STATIC_FEATURES = {
    'SPX_momentum_5': 0.0,
    'SPY_momentum_5': 0.0,
    'XSP_momentum_5': 0.0,
    'NDX_momentum_5': 0.0,
    'QQQ_momentum_5': 0.0,
    'RUT_momentum_5': 0.0,
    'AAPL_momentum_5': 0.0,
    'TSLA_momentum_5': 0.0,
    'SPX_rsi': 50.0,
    'SPY_rsi': 50.0,
    'XSP_rsi': 50.0,
    'NDX_rsi': 50.0,
    'QQQ_rsi': 50.0,
    'RUT_rsi': 50.0,
    'AAPL_rsi': 50.0,
    'TSLA_rsi': 50.0,
    'SPX_price_position': 0.5,
    'SPY_price_position': 0.5,
    'XSP_price_position': 0.5,
    'NDX_price_position': 0.5,
    'QQQ_price_position': 0.5,
    'RUT_price_position': 0.5,
    'AAPL_price_position': 0.5,
    'TSLA_price_position': 0.5,
    'vix_vix_change': 0.0,
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
    processing_time_ms: float  # Added timing info

def init_ib_connection():
    """Initialize IB connection at module level, before FastAPI starts."""
    global ib, ib_connected
    
    try:
        print("Connecting to IB Gateway on port 7497...")
        ib = IB()
        ib.connect('127.0.0.1', 7497, clientId=99)
        
        if ib.isConnected():
            ib_connected = True
            print("✓ Connected to IB Gateway")
            # Pre-subscribe to common symbols
            pre_subscribe_symbols()
            return True
        else:
            print("✗ Failed to connect to IB Gateway")
            return False
            
    except Exception as e:
        print(f"IB connection failed: {e}")
        ib_connected = False
        return False

def pre_subscribe_symbols():
    """Pre-subscribe to commonly used symbols for faster data access."""
    symbols = ['SPX', 'SPY', 'VIX', 'XSP', 'NDX', 'QQQ', 'RUT']
    
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
            
            # Subscribe to market data
            ticker = ib.reqMktData(contract, '', False, False)
            with ticker_lock:
                active_tickers[symbol] = ticker
            logger.info(f"Pre-subscribed to {symbol}")
            
        except Exception as e:
            logger.warning(f"Failed to pre-subscribe to {symbol}: {e}")

# Connect at module import time
init_ib_connection()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global ib, ib_connected
    
    # Startup
    logger.info("Starting Optimized Magic8 Prediction API...")
    
    # Suppress ML library warnings during startup
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, module="xgboost")
        warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
        
        # Load model and features
        if not load_model_and_features():
            logger.error("Failed to load model/features")
    
    # Warm up the model
    await warm_up_model()
    
    if ib_connected:
        logger.info("✓ Ready with IB connection and pre-subscribed data")
    else:
        logger.warning("✗ Running without IB - will use mock data")
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down...")
    
    # Cancel all active subscriptions
    with ticker_lock:
        for symbol, ticker in active_tickers.items():
            try:
                ib.cancelMktData(ticker)
            except:
                pass
        active_tickers.clear()
    
    if ib and ib.isConnected():
        try:
            ib.disconnect()
            logger.info("✓ Disconnected from IB")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    executor.shutdown(wait=True)
    ib_connected = False
    logger.info("Shutdown complete")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Optimized Magic8 Prediction API",
    description="High-performance prediction API with sub-5s response times",
    version="4.0.0",
    lifespan=lifespan
)

def get_ib_price_fast(symbol: str) -> float:
    """Get price from pre-subscribed ticker or cache."""
    global active_tickers
    
    # Check if we have an active ticker
    with ticker_lock:
        ticker = active_tickers.get(symbol)
    
    if ticker:
        # Use pre-subscribed data - much faster!
        if ticker.last and not math.isnan(ticker.last):
            return float(ticker.last)
        elif ticker.close and not math.isnan(ticker.close):
            return float(ticker.close)
    
    # Fallback to regular method
    return get_ib_price(symbol)

def get_ib_price(symbol: str) -> float:
    """Get price from IB - with improved error handling."""
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
        
        # Shorter timeout for faster fallback
        timeout = 1.0
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if ticker.last and not math.isnan(ticker.last):
                price = ticker.last
                break
            elif ticker.close and not math.isnan(ticker.close):
                price = ticker.close
                break
            time.sleep(0.05)  # Smaller sleep interval
        else:
            ib.cancelMktData(ticker)
            raise Exception(f"Timeout getting price for {symbol}")
        
        ib.cancelMktData(ticker)
        return float(price)
        
    except Exception as e:
        logger.debug(f"Error getting IB price for {symbol}: {e}")
        raise

def get_market_data_batch(symbols: List[str]) -> Dict[str, Dict]:
    """Get market data for multiple symbols in parallel."""
    results = {}
    
    # Check cache first
    uncached_symbols = []
    with cache_lock:
        for symbol in symbols:
            if symbol in market_data_cache:
                cache_entry = market_data_cache[symbol]
                age = time.time() - cache_entry['timestamp']
                if age < CACHE_TTL_SECONDS:
                    results[symbol] = cache_entry['data']
                else:
                    uncached_symbols.append(symbol)
            else:
                uncached_symbols.append(symbol)
    
    # Fetch uncached symbols in parallel
    if uncached_symbols and ib_connected:
        def fetch_single(symbol):
            try:
                price = get_ib_price_fast(symbol)
                return symbol, {
                    'price': price,
                    'volatility': 0.20,
                    'source': 'ibkr'
                }
            except:
                return symbol, {
                    'price': MOCK_PRICES.get(symbol, 100.0),
                    'volatility': 0.30 if symbol == 'VIX' else 0.20,
                    'source': 'mock'
                }
        
        # Use ThreadPoolExecutor for parallel fetching
        futures = {executor.submit(fetch_single, symbol): symbol 
                  for symbol in uncached_symbols}
        
        for future in as_completed(futures):
            symbol, data = future.result()
            results[symbol] = data
            
            # Update cache
            with cache_lock:
                market_data_cache[symbol] = {
                    'data': data,
                    'timestamp': time.time()
                }
    else:
        # Use mock data for uncached symbols
        for symbol in uncached_symbols:
            data = {
                'price': MOCK_PRICES.get(symbol, 100.0),
                'volatility': 0.30 if symbol == 'VIX' else 0.20,
                'source': 'mock'
            }
            results[symbol] = data
    
    return results

def load_model_and_features():
    """Load model and feature configuration."""
    global model, feature_names
    
    # Load model with warning suppression
    model_paths = [
        'models/xgboost_phase1_model.pkl',
        'models/phase1/xgboost_model.pkl'
    ]
    
    for model_path in model_paths:
        if os.path.exists(model_path):
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=UserWarning)
                    
                    model = joblib.load(model_path)
                    logger.info(f"✓ Loaded model from {model_path}")
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

async def warm_up_model():
    """Warm up the model with a dummy prediction."""
    try:
        dummy_request = TradeRequest(
            strategy="Butterfly",
            symbol="SPX",
            premium=1.0,
            predicted_price=5850.0
        )
        
        # Build features and make prediction
        features_df = build_features_fast(dummy_request)
        _ = model.predict_proba(features_df)
        logger.info("✓ Model warmed up successfully")
    except Exception as e:
        logger.warning(f"Model warm-up failed: {e}")

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
            "active_subscriptions": len(active_tickers),
            "cache_entries": len(market_data_cache)
        }
    }

def build_features_fast(request: TradeRequest) -> pd.DataFrame:
    """Optimized feature building with parallel data fetching."""
    start_time = time.time()
    
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
    minutes_to_close = ((market_close_time - now).seconds / 60) if is_market_open else 0
    
    # Get all market data in parallel
    symbols = ['SPX', 'SPY', 'XSP', 'NDX', 'QQQ', 'RUT', 'AAPL', 'TSLA', 'VIX']
    market_data = get_market_data_batch(symbols)
    
    # Build feature dict starting with static features
    features = STATIC_FEATURES.copy()
    
    # Add temporal features
    features.update({
        'hour': hour,
        'minute': minute,
        'day_of_week': day_of_week,
        'hour_sin': hour_sin,
        'hour_cos': hour_cos,
        'is_market_open': int(is_market_open),
        'is_open_30min': int(is_open_30min),
        'is_close_30min': int(is_close_30min),
        'minutes_to_close': minutes_to_close,
    })
    
    # Add price features
    vix_level = market_data['VIX']['price']
    
    for symbol in ['SPX', 'SPY', 'XSP', 'NDX', 'QQQ', 'RUT', 'AAPL', 'TSLA']:
        price = market_data[symbol]['price']
        volatility = market_data[symbol]['volatility']
        
        features[f'{symbol}_close'] = price
        features[f'{symbol}_sma_20'] = price  # Approximation
        features[f'{symbol}_volatility_20'] = volatility
    
    # VIX features
    features.update({
        'vix': vix_level,
        'vix_vix_sma_20': vix_level,
        'vix_regime_low': int(vix_level < 12),
        'vix_regime_normal': int(12 <= vix_level < 20),
        'vix_regime_elevated': int(20 <= vix_level < 30),
        'vix_regime_high': int(vix_level >= 30),
    })
    
    # Strategy features (one-hot)
    features.update({
        'strategy_Butterfly': int(request.strategy == 'Butterfly'),
        'strategy_Iron Condor': int(request.strategy == 'Iron Condor'),
        'strategy_Sonar': int(request.strategy == 'Sonar'),
        'strategy_Vertical': int(request.strategy == 'Vertical'),
    })
    
    # Trade features
    spx_price = market_data['SPX']['price']
    risk = request.risk if request.risk else request.premium
    reward = request.reward if request.reward else request.premium * 3
    
    features.update({
        'premium_normalized': request.premium / spx_price,
        'risk_reward_ratio': (reward / risk) if risk > 0 else 3.0,
        'pred_predicted': request.predicted_price,
        'pred_price': spx_price,
        'pred_difference': abs(request.predicted_price - spx_price),
        'prof_premium': request.premium,
    })
    
    # Create DataFrame
    df = pd.DataFrame([features])
    
    # Ensure all features are present
    missing_features = set(feature_names) - set(df.columns)
    for feat in missing_features:
        df[feat] = 0
    
    # Ensure correct column order
    df = df[feature_names]
    
    logger.debug(f"Feature building took {(time.time() - start_time)*1000:.1f}ms")
    
    return df

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: TradeRequest):
    """Make a prediction with performance tracking."""
    start_time = time.time()
    
    if not model or not feature_names:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Build features (optimized)
        features_df = build_features_fast(request)
        
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
        
        # Calculate metrics
        confidence = abs(win_probability - 0.5) * 2
        risk_score = 1.0 - win_probability
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Prediction completed in {processing_time_ms:.1f}ms")
        
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
            risk_score=risk_score,
            processing_time_ms=processing_time_ms
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/{symbol}")
async def get_market_data_endpoint(symbol: str):
    """Get current market data for a symbol."""
    try:
        start_time = time.time()
        
        # Use batch method for single symbol
        data = get_market_data_batch([symbol.upper()])[symbol.upper()]
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return {
            "symbol": symbol.upper(),
            "price": data['price'],
            "volatility": data['volatility'],
            "source": data['source'],
            "timestamp": datetime.now().isoformat(),
            "processing_time_ms": processing_time_ms
        }
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)