# Magic8 Accuracy Predictor Revamp Plan 3: Continuous Monitoring Support

## Overview

This revamp addresses the significant changes introduced by DiscordTrading's continuous monitoring system (Section 12). The system now makes ML confidence checks every 5 minutes for all active symbols and strategies, representing a 10-20x increase in API calls compared to the previous schedule-based approach.

## Current Issues

1. **Performance Bottlenecks**
   - Each prediction request fetches market data individually
   - Feature calculations are repeated for the same symbol/time
   - No batch processing capability
   - Single-threaded request handling

2. **Resource Inefficiency**
   - Market data cached for only 30 seconds
   - No feature caching
   - No prediction result caching
   - Repeated model loading for hierarchical predictions

3. **Missing Capabilities**
   - No batch prediction endpoint
   - No confidence history tracking
   - No performance metrics/monitoring
   - No websocket support for real-time updates

## Proposed Enhancements

### Phase 1: Critical Performance Optimizations (Week 1)

#### 1.1 Batch Prediction Endpoint
Create `/predict/batch` endpoint to handle multiple predictions in a single request.

**Benefits:**
- Reduce API calls by 80%
- Share market data fetching across predictions
- Batch feature calculation
- Single model loading for multiple predictions

**Implementation:**
```python
class BatchTradeRequest(BaseModel):
    requests: List[TradeRequest]
    share_market_data: bool = True  # Use same market snapshot for all

class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
    batch_metrics: Dict[str, Any]  # Processing time, cache hits, etc.
```

#### 1.2 Enhanced Caching Layer
Implement three-tier caching with configurable TTLs:

**Market Data Cache (existing, optimize)**
- Increase TTL from 30s to 5 minutes for continuous monitoring
- Add cache warming for frequently requested symbols

**Feature Cache (new)**
- Cache calculated features by symbol + timestamp
- TTL: 1 minute (features change with market data)
- Key: `f"{symbol}_{int(timestamp/60)}"` (minute precision)

**Prediction Cache (new)**
- Cache predictions by symbol + strategy + feature hash
- TTL: 5 minutes (align with monitoring interval)
- Include confidence decay factor

**Implementation:**
```python
from functools import lru_cache
from typing import Tuple
import hashlib

class CacheManager:
    def __init__(self):
        self.feature_cache = {}  # TTL-based dict
        self.prediction_cache = {}  # TTL-based dict
        
    def get_feature_key(self, symbol: str, timestamp: datetime) -> str:
        # Round to minute for feature caching
        minute_ts = int(timestamp.timestamp() / 60) * 60
        return f"features_{symbol}_{minute_ts}"
        
    def get_prediction_key(self, symbol: str, strategy: str, features: np.ndarray) -> str:
        # Hash features for prediction caching
        feature_hash = hashlib.md5(features.tobytes()).hexdigest()[:8]
        return f"pred_{symbol}_{strategy}_{feature_hash}"
```

### Phase 2: Advanced Features (Week 2)

#### 2.1 Confidence History Tracking
Store and analyze prediction history for trend detection.

**Database Schema:**
```sql
CREATE TABLE confidence_history (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    strategy VARCHAR(20) NOT NULL,
    win_probability FLOAT NOT NULL,
    prediction VARCHAR(10) NOT NULL,
    model_type VARCHAR(50),
    features_hash VARCHAR(32),
    INDEX idx_symbol_strategy_time (symbol, strategy, timestamp)
);
```

**API Endpoints:**
```python
@app.get("/confidence/history/{symbol}/{strategy}")
async def get_confidence_history(
    symbol: str, 
    strategy: str,
    hours: int = 24,
    include_features: bool = False
):
    """Return confidence history for analysis."""
    
@app.get("/confidence/trends")
async def get_confidence_trends(
    symbols: List[str] = Query([]),
    strategies: List[str] = Query([]),
    window: int = 60  # minutes
):
    """Return confidence trends and statistics."""
```

#### 2.2 Performance Monitoring
Add metrics collection and monitoring endpoints.

**Metrics to Track:**
- Request latency by endpoint
- Cache hit rates
- Model inference time
- Market data fetch time
- Feature calculation time
- Queue depth (for batch processing)

**Implementation:**
```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
request_count = Counter('prediction_requests_total', 'Total prediction requests', ['endpoint', 'status'])
request_latency = Histogram('prediction_request_duration_seconds', 'Request latency', ['endpoint'])
cache_hits = Counter('cache_hits_total', 'Cache hit count', ['cache_type'])
cache_misses = Counter('cache_misses_total', 'Cache miss count', ['cache_type'])
active_connections = Gauge('active_connections', 'Number of active connections')

@app.get("/metrics")
async def get_metrics():
    """Prometheus-compatible metrics endpoint."""
    
@app.get("/health/detailed")
async def health_check_detailed():
    """Detailed health check with component status."""
    return {
        "status": "healthy",
        "components": {
            "market_data": await check_market_data_health(),
            "model": check_model_health(),
            "cache": get_cache_stats(),
            "database": await check_db_health()
        },
        "metrics": {
            "requests_per_minute": get_rpm(),
            "avg_latency_ms": get_avg_latency(),
            "cache_hit_rate": get_cache_hit_rate()
        }
    }
```

### Phase 3: Real-time Capabilities (Week 3)

#### 3.1 WebSocket Support
Enable real-time confidence updates for continuous monitoring.

**Implementation:**
```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.symbol_subscriptions: Dict[str, Set[WebSocket]] = {}
        
@app.websocket("/ws/confidence")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data["action"] == "subscribe":
                await manager.subscribe(websocket, data["symbols"])
            elif data["action"] == "unsubscribe":
                await manager.unsubscribe(websocket, data["symbols"])
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

#### 3.2 Async Processing Optimization
Fully leverage FastAPI's async capabilities.

**Improvements:**
- Concurrent market data fetching for batch requests
- Async feature calculation where possible
- Background task queue for non-critical operations
- Connection pooling for database operations

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncBatchProcessor:
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    async def process_batch(self, requests: List[TradeRequest]) -> List[PredictionResponse]:
        # Group by symbol for efficient market data fetching
        symbols = list(set(req.symbol for req in requests))
        
        # Fetch all market data concurrently
        market_data_tasks = [self.fetch_market_data(sym) for sym in symbols]
        market_data_results = await asyncio.gather(*market_data_tasks)
        market_data = dict(zip(symbols, market_data_results))
        
        # Process predictions concurrently
        prediction_tasks = [
            self.process_single_prediction(req, market_data[req.symbol])
            for req in requests
        ]
        return await asyncio.gather(*prediction_tasks)
```

### Phase 4: Production Hardening (Week 4)

#### 4.1 Rate Limiting
Implement rate limiting to prevent API abuse.

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/predict")
@limiter.limit("100/minute")  # 100 requests per minute per IP
async def predict(request: TradeRequest):
    ...

@app.post("/predict/batch")
@limiter.limit("20/minute")  # Lower limit for batch endpoint
async def predict_batch(request: BatchTradeRequest):
    ...
```

#### 4.2 Graceful Degradation
Handle failures gracefully when services are unavailable.

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.is_open = False
        
    async def call(self, func, *args, **kwargs):
        if self.is_open:
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.is_open = False
                self.failure_count = 0
            else:
                raise CircuitBreakerOpen("Circuit breaker is open")
                
        try:
            result = await func(*args, **kwargs)
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            if self.failure_count >= self.failure_threshold:
                self.is_open = True
            raise e
```

#### 4.3 Deployment Configuration
Update deployment for high availability.

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - WORKERS=4
      - MAX_CONNECTIONS=1000
      - CACHE_SIZE=10000
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
          
  redis:
    image: redis:alpine
    command: redis-server --maxmemory 512mb --maxmemory-policy lru
    
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

## Implementation Timeline

### Week 1: Critical Performance
- [ ] Implement batch prediction endpoint
- [ ] Add feature caching
- [ ] Add prediction caching
- [ ] Optimize market data cache TTL

### Week 2: Advanced Features
- [ ] Set up confidence history database
- [ ] Implement history tracking
- [ ] Add trend analysis endpoints
- [ ] Create metrics collection

### Week 3: Real-time Support
- [ ] Implement WebSocket server
- [ ] Add subscription management
- [ ] Optimize async processing
- [ ] Create background task queue

### Week 4: Production Ready
- [ ] Add rate limiting
- [ ] Implement circuit breakers
- [ ] Set up monitoring stack
- [ ] Deploy with high availability

## Expected Benefits

1. **Performance Improvements**
   - 80% reduction in API calls via batching
   - 60% reduction in computation via caching
   - 90% reduction in market data calls
   - Sub-100ms response time for cached predictions

2. **Operational Benefits**
   - Real-time monitoring of system health
   - Historical analysis of confidence trends
   - Graceful handling of failures
   - Horizontal scalability

3. **Integration Benefits**
   - Better support for continuous monitoring
   - WebSocket support for future real-time needs
   - Comprehensive metrics for optimization
   - Reduced load on market data providers

## Testing Strategy

1. **Load Testing**
   ```bash
   # Simulate continuous monitoring load
   locust -f tests/load_test.py --users 100 --spawn-rate 10
   ```

2. **Cache Effectiveness**
   - Monitor cache hit rates during testing
   - Verify memory usage stays within limits
   - Test cache invalidation logic

3. **Batch Processing**
   - Test with varying batch sizes (10, 50, 100 predictions)
   - Verify consistent results vs individual predictions
   - Measure latency improvements

4. **Integration Testing**
   - Test with DiscordTrading continuous monitoring
   - Verify confidence history accuracy
   - Test WebSocket reliability

## Rollout Plan

1. **Phase 1 Rollout**
   - Deploy to staging environment
   - Run parallel with existing API
   - Monitor performance metrics
   - Gradual traffic migration

2. **Production Deployment**
   - Blue-green deployment strategy
   - Monitor error rates and latency
   - Keep rollback plan ready
   - Communicate changes to DiscordTrading team

## Configuration Updates

**config.yaml additions:**
```yaml
api:
  batch_size_limit: 100
  rate_limit_per_minute: 100
  
cache:
  market_data_ttl: 300  # 5 minutes
  feature_ttl: 60       # 1 minute  
  prediction_ttl: 300   # 5 minutes
  max_memory_mb: 1024
  
monitoring:
  enable_metrics: true
  enable_history: true
  history_retention_days: 30
  
websocket:
  enabled: false  # Enable in phase 3
  max_connections: 1000
  heartbeat_interval: 30
```

## Success Metrics

1. **Performance KPIs**
   - API response time < 100ms (p95)
   - Cache hit rate > 70%
   - Batch processing time < 500ms for 50 predictions
   - Zero timeout errors under normal load

2. **Reliability KPIs**
   - Uptime > 99.9%
   - Error rate < 0.1%
   - Successful degradation during outages
   - < 5 second recovery time

3. **Integration KPIs**
   - Support 50+ symbols with continuous monitoring
   - Handle 1000+ predictions per minute
   - Maintain accuracy within 0.1% of baseline
   - Zero data inconsistencies

## Conclusion

This revamp transforms magic8-accuracy-predictor from a simple prediction API to a production-ready, high-performance system capable of supporting DiscordTrading's continuous monitoring requirements. The phased approach ensures minimal disruption while delivering immediate performance benefits.
