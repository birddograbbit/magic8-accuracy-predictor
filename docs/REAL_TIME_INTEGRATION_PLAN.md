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

## User Guide

### Quick Start

#### 1. Prerequisites

- Python 3.8+
- Trained XGBoost model from Phase 1
- One of the following data sources:
  - Magic8-Companion running with API enabled
  - Redis server
  - IBKR Gateway/TWS with available port

#### 2. Installation

```bash
# Clone the repository
git clone https://github.com/birddograbbit/magic8-accuracy-predictor.git
cd magic8-accuracy-predictor

# Install dependencies
pip install -r requirements.txt

# Copy and configure settings
cp config/config.yaml config/config.local.yaml
```

#### 3. Configuration

Edit `config/config.local.yaml`:

```yaml
# Choose your data source
data_source:
  primary: "companion"  # companion, redis, or standalone
  
  companion:
    enabled: true
    base_url: "http://localhost:8765"  # Magic8-Companion URL
```

#### 4. Test the Setup

```bash
# Run the test script
python test_real_time_predictor.py
```

Expected output:
```
============================================================
Magic8 Accuracy Predictor - Real-Time Test
============================================================
2025-07-01 10:30:00 - INFO - Testing data providers...

1. Testing CompanionDataProvider...
   Connected to Magic8-Companion
   Health: healthy

2. Testing RedisDataProvider...
   Connected to Redis
   Health: healthy

Testing predictions...
Predicting for: SPX Butterfly
  Win probability: 72.34%
  Confidence: 44.68%
  Latency: 125.3ms
  Features used: 67
```

### Integration with DiscordTrading

#### Option 1: Direct Integration (Recommended)

1. Copy the predictor module to DiscordTrading:
```bash
cp -r src/real_time_predictor.py ../DiscordTrading/
cp -r src/data_providers ../DiscordTrading/
cp -r src/feature_engineering ../DiscordTrading/
```

2. Modify DiscordTrading's `config.yaml`:
```yaml
accuracy_predictor:
  enabled: true
  min_win_probability: 0.55
  model_path: "../magic8-accuracy-predictor/models/xgboost_phase1_model.pkl"
  data_source: "companion"
```

3. Update `discord_trading_bot.py`:
```python
# Add import
from real_time_predictor import get_prediction_service

# In process_trade_instruction()
if self.config.get('accuracy_predictor', {}).get('enabled'):
    prediction = await self.prediction_service.predict(order)
    if prediction.win_probability < min_probability:
        logger.info(f"Skipping trade - low win probability: {prediction.win_probability:.2%}")
        return None
```

#### Option 2: API Service

1. Start the prediction API:
```bash
python -m uvicorn src.api.prediction_api:app --port 8767
```

2. Configure DiscordTrading to use the API:
```yaml
accuracy_predictor:
  enabled: true
  api_url: "http://localhost:8767"
```

### Running Different Configurations

#### 1. With Magic8-Companion (Default)

Ensure Magic8-Companion is running with the data API enabled:

```bash
# In Magic8-Companion directory
export M8C_ENABLE_DATA_API=true
python -m magic8_companion
```

Then run predictions:
```python
from src.real_time_predictor import get_prediction_service

service = get_prediction_service()
result = await service.predict(order)
```

#### 2. With Redis (High Performance)

Start Redis with market data publishing:

```bash
# Start Redis
redis-server

# In another terminal, start the data publisher
python scripts/redis_market_publisher.py
```

Configure to use Redis:
```yaml
data_source:
  primary: "redis"
```

#### 3. Standalone Mode (Development)

For development or when other services are unavailable:

```yaml
data_source:
  primary: "standalone"
  
  standalone:
    enabled: true
    ib_port: 7498  # Different from other connections
    client_id: 99
```

### Performance Tuning

#### 1. Enable Caching

```yaml
performance:
  cache:
    enabled: true
    ttl_seconds: 300  # 5 minutes
```

#### 2. Batch Predictions

```python
# Predict multiple orders at once
orders = [order1, order2, order3]
results = await predictor.predict_batch(orders, max_concurrent=5)
```

#### 3. Warmup on Startup

```python
# Warmup with sample predictions
await service.warmup_all()
```

## Operational Guide

### Deployment Scenarios

#### Scenario 1: All Systems on Same Machine

```bash
# Terminal 1: IBKR Gateway
/opt/ibgateway/bin/run.sh

# Terminal 2: Magic8-Companion with API
cd /opt/Magic8-Companion
./start_with_api.sh

# Terminal 3: Redis (optional)
redis-server

# Terminal 4: DiscordTrading with predictions
cd /opt/DiscordTrading
python discord_trading_bot.py
```

#### Scenario 2: Distributed Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
  
  magic8-companion:
    build: ./Magic8-Companion
    environment:
      - ENABLE_DATA_API=true
      - REDIS_HOST=redis
    ports:
      - "8765:8765"
  
  predictor:
    build: ./magic8-accuracy-predictor
    environment:
      - DATA_SOURCE=companion
      - COMPANION_URL=http://magic8-companion:8765
    depends_on:
      - magic8-companion
      - redis
```

### Monitoring

#### 1. Health Checks

```bash
# Check predictor health
curl http://localhost:8767/health

# Check data provider status
python scripts/check_data_providers.py
```

#### 2. Log Monitoring

```bash
# Watch prediction logs
tail -f logs/predictions.jsonl | jq

# Monitor errors
grep ERROR logs/magic8_predictor.log
```

#### 3. Performance Metrics

```python
# Get performance stats
stats = service.get_status()
print(f"Total predictions: {stats['predictors'][0]['stats']['total_predictions']}")
print(f"Avg latency: {stats['predictors'][0]['stats']['average_latency_ms']}ms")
```

### Troubleshooting

#### Issue: "Failed to connect to Magic8-Companion"

**Solution**:
1. Check Magic8-Companion is running: `ps aux | grep magic8`
2. Verify API is enabled: `curl http://localhost:8765/health`
3. Check firewall settings

#### Issue: "No predictor available for symbol"

**Solution**:
1. Check model configuration includes the symbol
2. Verify model file exists at configured path
3. Add symbol to model config:
```yaml
prediction:
  models:
    - name: "xgboost_phase1"
      symbols: ["SPX", "SPY", "NEW_SYMBOL"]
```

#### Issue: High prediction latency

**Solution**:
1. Enable caching in config
2. Use Redis instead of HTTP API
3. Reduce feature generation complexity
4. Check network latency to data source

#### Issue: IBKR connection conflicts

**Solution**:
1. Use Magic8-Companion as primary data source
2. Ensure unique client IDs for each connection
3. Use different ports for multiple gateways:
   - Magic8-Companion: 7497
   - Standalone predictor: 7498
   - DiscordTrading: 7496

### Maintenance

#### Daily Tasks

1. **Check logs for errors**:
```bash
./scripts/daily_log_check.sh
```

2. **Verify prediction accuracy**:
```python
python scripts/verify_predictions.py --date today
```

#### Weekly Tasks

1. **Review prediction performance**:
```python
python scripts/generate_performance_report.py --week
```

2. **Clean up old cache and logs**:
```bash
find logs -name "*.log" -mtime +7 -delete
redis-cli FLUSHDB  # Clear Redis cache
```

#### Monthly Tasks

1. **Retrain models with new data**:
```bash
cd ..
python src/models/xgboost_baseline.py --retrain
```

2. **Update feature engineering if needed**
3. **Review and optimize configuration**

### Production Checklist

- [ ] Set `environment: "production"` in config
- [ ] Configure proper logging levels
- [ ] Set up monitoring alerts
- [ ] Enable Redis for production performance
- [ ] Configure appropriate win probability thresholds
- [ ] Set up automatic restarts (systemd/supervisor)
- [ ] Configure firewall rules
- [ ] Set up backup for predictions log
- [ ] Test failover scenarios
- [ ] Document custom configurations

### Emergency Procedures

#### Disable Predictions Quickly

```bash
# Option 1: Via config
sed -i 's/enabled: true/enabled: false/g' config/config.yaml

# Option 2: Via environment
export MAGIC8_PREDICTOR_ENABLED=false

# Option 3: Kill process
pkill -f real_time_predictor
```

#### Fallback to Manual Trading

1. Disable predictor in DiscordTrading config
2. Restart DiscordTrading
3. Monitor manually until issue resolved

#### Data Source Failover

If primary data source fails:
1. System automatically tries fallback
2. Monitor logs for failover events
3. Manually switch if needed:
```yaml
data_source:
  primary: "redis"  # Switch from companion
```

## Conclusion

This integration provides a robust, scalable solution for real-time Magic8 order predictions. The modular design allows for flexible deployment options while the ship-fast implementation focuses on getting a working system quickly. Follow the operational guide for smooth production deployment and maintenance.
