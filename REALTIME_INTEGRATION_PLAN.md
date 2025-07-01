# Real-Time Integration Architecture Plan

## Overview
This document outlines the integration architecture for combining magic8-accuracy-predictor with existing systems (Magic8-Companion, MLOptionTrading, DiscordTrading) while avoiding IBKR conflicts and rate limits.

## Core Problem
- IBKR allows only one connection per user/client ID
- Strict rate limits (60 requests per 10 minutes for historical data)
- Multiple systems need the same market data
- Need flexible on/off configuration for different predictors

## Solution: Centralized Market Data Service (MDS)

### Architecture Components

#### 1. Market Data Service (Core Hub)
Single service managing all IBKR interactions:
- **Single IBKR Connection**: Prevents session conflicts
- **Data Caching**: Redis for real-time data storage
- **Distribution**: WebSocket + REST API for data access
- **Rate Limiting**: Intelligent request management
- **Subscription Management**: Tracks what data each service needs

#### 2. Service Integration Pattern
```
IBKR API → Market Data Service → Redis Cache
                ↓
        WebSocket Server
         ↙     ↓     ↘
   Magic8-AP  MLOT  Magic8-Companion
```

### Implementation Phases

## Phase 1: Foundation (Week 1)

### 1.1 Extend Magic8-Companion IB Manager
Create a standalone market data service from Magic8-Companion's IB connection:

```python
# market_data_service.py
class MarketDataService:
    def __init__(self):
        self.ib_client = IBClient()  # From Magic8-Companion
        self.redis_client = redis.Redis()
        self.subscribers = {}
        self.rate_limiter = RateLimiter(60, 600)  # 60 req/10min
        
    def subscribe_symbol(self, symbol, client_id):
        """Subscribe to real-time data for a symbol"""
        
    def get_historical_data(self, symbol, duration, bar_size):
        """Get historical data with caching"""
        
    def broadcast_update(self, symbol, data):
        """Send updates to all subscribers"""
```

### 1.2 Redis Cache Layer
```python
# cache_manager.py
class CacheManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = {
            'realtime': 10,      # 10 seconds
            'historical': 300,   # 5 minutes
            'technical': 60      # 1 minute
        }
    
    def get_market_data(self, symbol):
        """Get cached market data"""
        
    def store_market_data(self, symbol, data, data_type='realtime'):
        """Store with appropriate TTL"""
```

### 1.3 WebSocket Server
```python
# websocket_server.py
from fastapi import FastAPI, WebSocket
import asyncio

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def broadcast_market_data(self, data: dict):
        """Broadcast to all connected clients"""
        
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            await websocket.receive_text()
    except:
        manager.disconnect(client_id)
```

## Phase 2: Magic8 Accuracy Predictor Integration (Week 2)

### 2.1 Real-Time Feature Generator
```python
# src/realtime_feature_generator.py
import pandas as pd
from typing import Dict, List
import asyncio
import websockets

class RealtimeFeatureGenerator:
    def __init__(self, mds_url: str):
        self.mds_url = mds_url
        self.feature_columns = self._load_feature_columns()
        self.market_data_buffer = {}
        self.technical_indicators = {}
        
    async def connect_to_mds(self):
        """Connect to Market Data Service via WebSocket"""
        async with websockets.connect(f"{self.mds_url}/ws/magic8-ap") as ws:
            await self._subscribe_symbols(ws)
            async for message in ws:
                await self._process_market_update(message)
    
    def generate_features(self, order: Dict) -> pd.DataFrame:
        """Generate features matching training pipeline"""
        features = {}
        
        # Temporal features
        features.update(self._get_temporal_features(order['timestamp']))
        
        # Price features for symbol
        symbol = order['symbol']
        features.update(self._get_price_features(symbol))
        
        # VIX features
        features.update(self._get_vix_features())
        
        # Strategy features
        features.update(self._get_strategy_features(order['strategy']))
        
        # Trade features
        features.update(self._get_trade_features(order))
        
        return pd.DataFrame([features])[self.feature_columns]
    
    def _calculate_technical_indicators(self, symbol: str, data: pd.DataFrame):
        """Calculate RSI, SMA, momentum etc."""
        # Match exactly what phase1_data_preparation.py does
        pass
```

### 2.2 Prediction Service
```python
# src/prediction_service.py
import xgboost as xgb
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()

class PredictionRequest(BaseModel):
    orders: List[Dict]
    
class PredictionResponse(BaseModel):
    predictions: List[Dict]

class Magic8Predictor:
    def __init__(self):
        self.model = self._load_model()
        self.preprocessor = self._load_preprocessor()
        self.feature_generator = RealtimeFeatureGenerator("ws://localhost:8000")
        
    def _load_model(self):
        model = xgb.XGBClassifier()
        model.load_model('models/phase1/xgboost_model.json')
        return model
        
    def _load_preprocessor(self):
        return joblib.load('models/phase1/preprocessor.pkl')
    
    async def predict_batch(self, orders: List[Dict]) -> List[Dict]:
        """Predict win probability for batch of orders"""
        predictions = []
        
        for order in orders:
            # Generate features
            features = self.feature_generator.generate_features(order)
            
            # Preprocess
            features_scaled = self.preprocessor.transform(features)
            
            # Predict
            prob = self.model.predict_proba(features_scaled)[0]
            
            predictions.append({
                'order_id': order['id'],
                'symbol': order['symbol'],
                'strategy': order['strategy'],
                'win_probability': float(prob[1]),
                'confidence': float(max(prob)),
                'recommendation': 'EXECUTE' if prob[1] > 0.7 else 'SKIP'
            })
            
        return predictions

predictor = Magic8Predictor()

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    predictions = await predictor.predict_batch(request.orders)
    return PredictionResponse(predictions=predictions)
```

### 2.3 Order Processing Pipeline
```python
# src/order_processor.py
import asyncio
from typing import Dict
import aiohttp

class OrderProcessor:
    def __init__(self, discord_trading_url: str, prediction_api_url: str):
        self.discord_url = discord_trading_url
        self.prediction_url = prediction_api_url
        self.order_queue = asyncio.Queue()
        
    async def listen_for_orders(self):
        """Connect to DiscordTrading for Magic8 orders"""
        async with aiohttp.ClientSession() as session:
            while True:
                # Poll or subscribe to DiscordTrading
                orders = await self._fetch_new_orders(session)
                for order in orders:
                    await self.order_queue.put(order)
                await asyncio.sleep(5)  # Check every 5 seconds
    
    async def process_orders(self):
        """Process orders through prediction pipeline"""
        batch = []
        while True:
            try:
                # Collect orders for batch processing
                order = await asyncio.wait_for(
                    self.order_queue.get(), 
                    timeout=1.0
                )
                batch.append(order)
                
                # Process batch if size or time threshold reached
                if len(batch) >= 10 or self._should_process_batch():
                    await self._process_batch(batch)
                    batch = []
                    
            except asyncio.TimeoutError:
                if batch:
                    await self._process_batch(batch)
                    batch = []
```

## Phase 3: Integration & Configuration (Week 3)

### 3.1 Configuration Management
```python
# config/integration_config.py
from pydantic import BaseSettings

class IntegrationConfig(BaseSettings):
    # Market Data Service
    mds_host: str = "localhost"
    mds_port: int = 8000
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    # Predictors - Feature flags
    enable_magic8_accuracy: bool = True
    enable_ml_option_trading: bool = True
    enable_magic8_companion: bool = True
    
    # Thresholds
    min_win_probability: float = 0.7
    min_confidence: float = 0.8
    
    # Rate limits
    max_requests_per_minute: int = 60
    
    class Config:
        env_file = ".env"
```

### 3.2 Recommendation Aggregator
```python
# src/recommendation_aggregator.py
from typing import List, Dict
import numpy as np

class RecommendationAggregator:
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.weights = {
            'magic8_accuracy': 0.5,
            'ml_option_trading': 0.3,
            'magic8_companion': 0.2
        }
    
    async def aggregate_recommendations(self, order: Dict) -> Dict:
        """Combine predictions from all enabled sources"""
        recommendations = []
        
        if self.config.enable_magic8_accuracy:
            rec = await self._get_magic8_accuracy_prediction(order)
            recommendations.append((rec, self.weights['magic8_accuracy']))
            
        if self.config.enable_ml_option_trading:
            rec = await self._get_ml_option_trading_prediction(order)
            recommendations.append((rec, self.weights['ml_option_trading']))
            
        if self.config.enable_magic8_companion:
            rec = await self._get_magic8_companion_recommendation(order)
            recommendations.append((rec, self.weights['magic8_companion']))
        
        # Weighted average
        final_score = self._calculate_weighted_score(recommendations)
        
        return {
            'order_id': order['id'],
            'final_score': final_score,
            'recommendation': 'EXECUTE' if final_score > self.config.min_win_probability else 'SKIP',
            'sources': [r[0]['source'] for r in recommendations],
            'details': recommendations
        }
```

### 3.3 Docker Compose Setup
```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  market-data-service:
    build: ./market-data-service
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
      - IB_GATEWAY_HOST=${IB_GATEWAY_HOST}
      - IB_GATEWAY_PORT=${IB_GATEWAY_PORT}
    depends_on:
      - redis

  magic8-accuracy-predictor:
    build: ./magic8-accuracy-predictor
    ports:
      - "8001:8001"
    environment:
      - MDS_URL=ws://market-data-service:8000
      - REDIS_HOST=redis
    depends_on:
      - market-data-service
      - redis
    volumes:
      - ./models:/app/models

  recommendation-api:
    build: ./recommendation-api
    ports:
      - "8002:8002"
    environment:
      - ENABLE_MAGIC8_ACCURACY=true
      - ENABLE_ML_OPTION_TRADING=true
      - ENABLE_MAGIC8_COMPANION=true
    depends_on:
      - magic8-accuracy-predictor

volumes:
  redis_data:
```

## Monitoring & Feedback Loop

### Monitoring Dashboard
```python
# src/monitoring/dashboard.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
prediction_counter = Counter('predictions_total', 'Total predictions', ['strategy', 'symbol'])
prediction_accuracy = Gauge('prediction_accuracy', 'Current accuracy', ['strategy'])
prediction_latency = Histogram('prediction_latency_seconds', 'Prediction latency')

class PredictionMonitor:
    def __init__(self):
        self.predictions = []
        self.outcomes = []
        
    def record_prediction(self, order_id: str, prediction: Dict):
        """Store prediction for later comparison"""
        self.predictions.append({
            'order_id': order_id,
            'timestamp': time.time(),
            'prediction': prediction
        })
        
        # Update metrics
        prediction_counter.labels(
            strategy=prediction['strategy'],
            symbol=prediction['symbol']
        ).inc()
    
    def record_outcome(self, order_id: str, actual_result: bool):
        """Record actual trade outcome"""
        # Match with prediction and calculate accuracy
        pass
```

## Priority Implementation Steps

### Week 1: Foundation
1. **Day 1-2**: Modify Magic8-Companion to expose IB connection via API
2. **Day 3-4**: Build Market Data Service with Redis cache
3. **Day 5-7**: Create WebSocket server and test data distribution

### Week 2: Prediction Pipeline  
1. **Day 1-2**: Build real-time feature generator
2. **Day 3-4**: Create prediction service with XGBoost model
3. **Day 5-7**: Integrate with order processing

### Week 3: Production Ready
1. **Day 1-2**: Add configuration management
2. **Day 3-4**: Build recommendation aggregator
3. **Day 5-7**: Deploy with Docker, add monitoring

## Key Benefits
1. **No IBKR Conflicts**: Single connection managed centrally
2. **Rate Limit Compliance**: Intelligent caching and request management
3. **Flexible Configuration**: Easy on/off for each predictor
4. **Scalable**: Can add more predictors without changing architecture
5. **Real-time**: WebSocket ensures low-latency data distribution
6. **Reliable**: Redis persistence, connection retry logic
7. **Monitorable**: Built-in metrics and accuracy tracking

---

This architecture ensures smooth integration while maintaining flexibility and performance. The Market Data Service acts as the single source of truth, preventing conflicts and enabling efficient data distribution to all prediction systems.