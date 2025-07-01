# Real-Time Integration Plan for Magic8 Accuracy Predictor

## Overview

This document outlines the integration strategy for building a real-time prediction pipeline that works seamlessly with DiscordTrading, Magic8-Companion, and MLOptionTrading without creating IBKR session conflicts or hitting rate limits.

## Current Architecture Analysis

### System Components

1. **DiscordTrading**
   - Downloads Magic8 orders from Discord (~5 min intervals)
   - Executes trades via IBKR (own connection)
   - Supports multiple symbols (SPX, SPY, RUT, QQQ, etc.)
   - Optional Magic8-Companion integration for filtering

2. **Magic8-Companion**
   - Centralized IB connection manager (IBConnectionSingleton)
   - Provides recommendations based on rules + ML
   - Shares IB connection with MLOptionTrading
   - Runs at scheduled times (10:30, 11:00, 12:30, 14:45 ET)

3. **MLOptionTrading**
   - Uses Magic8-Companion's IB connection
   - Provides ML predictions for direction/volatility
   - Integration partially complete

4. **magic8-accuracy-predictor** (NEW)
   - Needs real-time IBKR data for feature generation
   - Predicts win/loss probability for Magic8 orders
   - Must integrate without connection conflicts

## Integration Strategy

### Core Principle: Centralized Data Service

Magic8-Companion will serve as the central IBKR connection manager, distributing data to all systems through a flexible API layer.

### Architecture Design

```
                    ┌─────────────────┐
                    │   Discord       │
                    │   Channels      │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ DiscordTrading  │
                    │                 │
                    └────────┬────────┘
                             │ New Orders
                    ┌────────▼────────────┐
                    │ Magic8 Accuracy     │
                    │ Predictor           │
                    │ (Real-time)        │
                    └────────┬────────────┘
                             │ Predictions
                    ┌────────▼────────┐
                    │ Order Decision  │
                    │ Engine          │
                    └─────────────────┘
                    
    ┌─────────────────────────────────────┐
    │       Magic8-Companion              │
    │  ┌─────────────────────────────┐   │
    │  │ IBConnectionSingleton       │   │
    │  │ (Central IBKR Connection)   │   │
    │  └──────────┬─────────────────┘   │
    │             │                      │
    │  ┌──────────▼─────────────────┐   │
    │  │ Data Distribution Layer    │   │
    │  │ - HTTP API                 │   │
    │  │ - WebSocket                │   │
    │  │ - Redis Pub/Sub (optional) │   │
    │  └─────────────────────────────┘   │
    └─────────────────────────────────────┘
                    │
         ┌──────────┼──────────┐
         │          │          │
    ┌────▼───┐ ┌───▼────┐ ┌──▼──────┐
    │ML      │ │Magic8  │ │Discord  │
    │Option  │ │Accuracy│ │Trading  │
    │Trading │ │Predictor│          │
    └────────┘ └────────┘ └─────────┘
```

## Implementation Plan

### Phase 1: Core Infrastructure (Priority 1)

#### 1.1 Create Real-Time Predictor Module

**File**: `src/real_time_predictor.py`

```python
class Magic8Predictor:
    def __init__(self, model_path, data_provider):
        self.model = self.load_model(model_path)
        self.feature_generator = RealTimeFeatureGenerator(data_provider)
        self.cache = {}
        
    async def predict_order(self, order):
        """Predict win/loss probability for a Magic8 order"""
        features = await self.feature_generator.generate_features(
            symbol=order['symbol'],
            order_details=order
        )
        
        # Get prediction
        probability = self.model.predict_proba([features])[0]
        
        return {
            'symbol': order['symbol'],
            'strategy': order['strategy'],
            'win_probability': float(probability[1]),
            'loss_probability': float(probability[0]),
            'confidence': abs(probability[1] - 0.5) * 2,
            'timestamp': datetime.now().isoformat()
        }
```

#### 1.2 Data Abstraction Layer

**Directory**: `src/data_providers/`

1. **Base Interface** (`base_provider.py`):
```python
class BaseDataProvider(ABC):
    @abstractmethod
    async def get_price_data(self, symbol: str, bars: int = 20):
        pass
    
    @abstractmethod
    async def get_vix_data(self):
        pass
    
    @abstractmethod
    async def get_option_chain(self, symbol: str, expiry: str):
        pass
```

2. **Companion Provider** (`companion_provider.py`):
```python
class CompanionDataProvider(BaseDataProvider):
    """Uses Magic8-Companion's IB connection"""
    def __init__(self, companion_url="http://localhost:8765"):
        self.base_url = companion_url
        
    async def get_price_data(self, symbol: str, bars: int = 20):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/market_data/{symbol}") as resp:
                return await resp.json()
```

3. **Redis Provider** (`redis_provider.py`):
```python
class RedisDataProvider(BaseDataProvider):
    """Subscribes to Redis channels for market data"""
    def __init__(self, redis_url="redis://localhost:6379"):
        self.redis = aioredis.from_url(redis_url)
        self.subscriptions = {}
```

4. **Standalone Provider** (`standalone_provider.py`):
```python
class StandaloneDataProvider(BaseDataProvider):
    """Direct IB connection with different client ID"""
    def __init__(self, ib_config):
        self.ib = IB()
        self.client_id = ib_config.get('client_id', 99)  # Different from others
```

#### 1.3 Feature Engineering

**File**: `src/feature_engineering/real_time_features.py`

```python
class RealTimeFeatureGenerator:
    def __init__(self, data_provider):
        self.data_provider = data_provider
        
    async def generate_features(self, symbol: str, order_details: dict):
        # Parallel data fetching
        price_task = self.data_provider.get_price_data(symbol, bars=100)
        vix_task = self.data_provider.get_vix_data()
        
        price_data, vix_data = await asyncio.gather(price_task, vix_task)
        
        features = {}
        
        # Temporal features
        features.update(self._generate_temporal_features())
        
        # Price features
        features.update(self._generate_price_features(price_data))
        
        # VIX features
        features.update(self._generate_vix_features(vix_data))
        
        # Trade features
        features.update(self._generate_trade_features(order_details))
        
        return self._align_with_training_features(features)
```

### Phase 2: Magic8-Companion Enhancement (Priority 2)

#### 2.1 Add Data API to Magic8-Companion

**File**: `magic8_companion/api/market_data_api.py`

```python
from fastapi import FastAPI, WebSocket
from ..modules.ib_client_manager import get_ib_connection

app = FastAPI()

@app.get("/api/market_data/{symbol}")
async def get_market_data(symbol: str, bars: int = 20):
    """Expose market data through REST API"""
    ib = await get_ib_connection()
    if not ib:
        return {"error": "IB not connected"}
    
    contract = Stock(symbol, 'SMART', 'USD')
    bars = await ib.reqHistoricalDataAsync(
        contract,
        endDateTime='',
        durationStr='1 D',
        barSizeSetting='5 mins',
        whatToShow='TRADES',
        useRTH=True
    )
    
    return {
        "symbol": symbol,
        "data": [
            {
                "time": bar.date.isoformat(),
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume
            }
            for bar in bars
        ]
    }

@app.websocket("/ws/market_data")
async def websocket_market_data(websocket: WebSocket):
    """Real-time market data via WebSocket"""
    await websocket.accept()
    # Implementation for streaming data
```

#### 2.2 Extend IBConnectionSingleton

```python
class IBConnectionSingleton:
    # ... existing code ...
    
    async def subscribe_market_data(self, symbol: str, callback):
        """Subscribe to real-time market data"""
        if symbol not in self._subscriptions:
            contract = Stock(symbol, 'SMART', 'USD')
            self._subscriptions[symbol] = await self._ib.reqMktDataAsync(contract)
            
        # Register callback
        self._callbacks[symbol].append(callback)
    
    async def publish_to_redis(self, channel: str, data: dict):
        """Publish market data to Redis"""
        if self._redis:
            await self._redis.publish(channel, json.dumps(data))
```

### Phase 3: DiscordTrading Integration (Priority 3)

#### 3.1 Add Prediction Hook

**Modify**: `discord_trading_bot.py`

```python
# Add to imports
from magic8_predictor import get_prediction_service

class DiscordTradingBot:
    def __init__(self):
        # ... existing code ...
        self.prediction_service = None
        if self.config.get('accuracy_predictor', {}).get('enabled', False):
            self.prediction_service = get_prediction_service(self.config)
    
    async def process_trade_instruction(self, instruction):
        """Process trade with optional prediction"""
        parsed_order = self.parse_instruction(instruction)
        
        # Get prediction if enabled
        if self.prediction_service:
            try:
                prediction = await self.prediction_service.predict_order(parsed_order)
                
                # Decision logic
                min_probability = self.config.get('accuracy_predictor', {}).get('min_win_probability', 0.55)
                
                if prediction['win_probability'] < min_probability:
                    self.logger.warning(
                        f"Skipping trade - low win probability: {prediction['win_probability']:.2%}"
                    )
                    return None
                    
                # Add prediction to order metadata
                parsed_order['prediction'] = prediction
                
            except Exception as e:
                self.logger.error(f"Prediction failed: {e}")
                # Continue without prediction
        
        # Execute trade
        return await self.execute_trade(parsed_order)
```

### Phase 4: Configuration System

#### 4.1 Configuration Schema

**File**: `config/config.yaml`

```yaml
# Magic8 Accuracy Predictor Configuration
system:
  log_level: INFO
  environment: "production"  # production, paper, backtest

data_source:
  primary: "companion"  # Options: companion, redis, standalone
  fallback: "redis"     # Fallback if primary fails
  
  companion:
    enabled: true
    base_url: "http://localhost:8765"
    timeout: 5
    retry_attempts: 3
    
  redis:
    enabled: true
    host: "localhost"
    port: 6379
    channels:
      price_data: "market:prices:{symbol}"
      vix_data: "market:vix"
      
  standalone:
    enabled: false
    ib_host: "127.0.0.1"
    ib_port: 7498  # Different from other systems
    client_id: 99   # Unique client ID

prediction:
  models:
    - name: "xgboost_phase1"
      path: "models/xgboost_model.pkl"
      symbols: ["SPX", "SPY", "RUT", "QQQ", "XSP", "NDX"]
      version: "1.0.0"
    
  feature_config:
    temporal:
      enabled: true
      features: ["hour", "minute", "day_of_week", "minutes_to_close"]
      
    price:
      enabled: true
      sma_periods: [20]
      momentum_periods: [5]
      rsi_period: 14
      
    vix:
      enabled: true
      sma_period: 20
      regime_thresholds: [15, 20, 25]

integration:
  discord_trading:
    enabled: true
    min_win_probability: 0.55
    skip_on_error: false
    
  magic8_companion:
    enabled: true
    sync_predictions: true
    
  monitoring:
    enabled: true
    track_predictions: true
    webhook_url: "http://localhost:9090/metrics"

performance:
  cache:
    enabled: true
    ttl_seconds: 300
    max_size: 1000
    
  batch_predictions:
    enabled: true
    max_batch_size: 10
    timeout_ms: 100
```

#### 4.2 Environment Variables

```bash
# .env file
MAGIC8_PREDICTOR_ENV=production
MAGIC8_PREDICTOR_DATA_SOURCE=companion
MAGIC8_PREDICTOR_MODEL_PATH=/path/to/models
MAGIC8_PREDICTOR_LOG_LEVEL=INFO

# IBKR Settings (for standalone mode)
MAGIC8_PREDICTOR_IB_HOST=127.0.0.1
MAGIC8_PREDICTOR_IB_PORT=7498
MAGIC8_PREDICTOR_IB_CLIENT_ID=99

# Redis Settings
MAGIC8_PREDICTOR_REDIS_HOST=localhost
MAGIC8_PREDICTOR_REDIS_PORT=6379

# API Settings
MAGIC8_PREDICTOR_API_PORT=8767
MAGIC8_PREDICTOR_API_HOST=0.0.0.0
```

### Phase 5: Deployment Options

#### Option A: All-in-One Deployment
```yaml
# docker-compose.yml
version: '3.8'
services:
  magic8-companion:
    build: ./Magic8-Companion
    ports:
      - "8765:8765"
    environment:
      - IB_GATEWAY_HOST=ib-gateway
      - ENABLE_DATA_API=true
      
  magic8-predictor:
    build: ./magic8-accuracy-predictor
    depends_on:
      - magic8-companion
    environment:
      - DATA_SOURCE=companion
      - COMPANION_URL=http://magic8-companion:8765
      
  discord-trading:
    build: ./DiscordTrading
    depends_on:
      - magic8-predictor
    environment:
      - PREDICTOR_URL=http://magic8-predictor:8767
```

#### Option B: Microservices with Redis
```yaml
version: '3.8'
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
      
  magic8-companion:
    build: ./Magic8-Companion
    environment:
      - REDIS_HOST=redis
      - PUBLISH_MARKET_DATA=true
      
  magic8-predictor:
    build: ./magic8-accuracy-predictor
    environment:
      - DATA_SOURCE=redis
      - REDIS_HOST=redis
```

#### Option C: Hybrid Mode
- Magic8-Companion for data during market hours
- Redis cache for off-hours testing
- Fallback to standalone if both fail

## Implementation Timeline

### Week 1: Core Infrastructure
- [ ] Create project structure
- [ ] Implement base data providers
- [ ] Build real-time feature generator
- [ ] Create prediction service

### Week 2: Integration Layer
- [ ] Add API to Magic8-Companion
- [ ] Implement Redis pub/sub
- [ ] Create WebSocket endpoints
- [ ] Test data flow

### Week 3: DiscordTrading Integration
- [ ] Add prediction hooks
- [ ] Implement decision logic
- [ ] Create monitoring dashboard
- [ ] Test end-to-end

### Week 4: Production Deployment
- [ ] Performance optimization
- [ ] Load testing
- [ ] Documentation
- [ ] Production rollout

## Monitoring and Observability

### Key Metrics
```python
# Prometheus metrics
prediction_latency = Histogram('prediction_latency_seconds', 'Time to generate prediction')
prediction_accuracy = Counter('prediction_accuracy', 'Correct predictions', ['symbol', 'strategy'])
data_fetch_errors = Counter('data_fetch_errors', 'Data provider errors', ['provider', 'error_type'])
```

### Logging Strategy
```python
# Structured logging
logger.info("prediction_made", extra={
    "symbol": symbol,
    "strategy": strategy,
    "win_probability": probability,
    "latency_ms": latency,
    "features_used": len(features),
    "data_source": data_source
})
```

## Risk Management

### Connection Failures
- Automatic fallback to secondary data source
- Circuit breaker pattern for failed providers
- Graceful degradation (skip prediction vs block trade)

### Rate Limiting
- Request throttling per data source
- Caching frequently used data
- Batch predictions when possible

### Data Quality
- Feature validation before prediction
- Outlier detection
- Missing data handling

## Testing Strategy

### Unit Tests
```python
# tests/test_real_time_predictor.py
async def test_prediction_with_mock_data():
    mock_provider = MockDataProvider()
    predictor = Magic8Predictor("test_model.pkl", mock_provider)
    
    order = {
        "symbol": "SPX",
        "strategy": "Butterfly",
        "strikes": [5900, 5910, 5920],
        "quantity": 1
    }
    
    result = await predictor.predict_order(order)
    assert 0 <= result['win_probability'] <= 1
```

### Integration Tests
- Test with each data provider
- Verify feature parity with training
- End-to-end prediction flow

### Performance Tests
- Measure prediction latency
- Test concurrent predictions
- Verify cache effectiveness

## Next Steps

1. **Immediate Actions**:
   - Create `src/real_time_predictor.py`
   - Implement companion data provider
   - Set up basic configuration

2. **Quick Wins**:
   - Add simple HTTP API to Magic8-Companion
   - Create prediction endpoint
   - Test with paper trading

3. **Long-term Goals**:
   - Full microservices architecture
   - ML model versioning
   - A/B testing framework
   - Real-time retraining pipeline

## Conclusion

This integration plan provides a flexible, scalable solution for adding real-time predictions to the Magic8 trading system while avoiding IBKR connection conflicts. The modular design allows for incremental implementation and easy configuration changes without code modifications.
