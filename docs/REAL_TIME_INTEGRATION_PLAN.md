# Real-Time Integration Plan for Magic8 Accuracy Predictor

## Overview

This document outlines the integration strategy for building a real-time prediction pipeline that works seamlessly with DiscordTrading, Magic8-Companion, and MLOptionTrading without creating IBKR session conflicts or hitting rate limits.

## 🚀 NEW: Quick Start Scripts

We've created helper scripts to get you running quickly:

1. **`quick_start.py`** - Get your first prediction in minutes
2. **`integrate_discord_trading.py`** - Automated DiscordTrading integration
3. **`setup_companion_api.py`** - Configure Magic8-Companion API
4. **`monitor_predictions.py`** - Real-time prediction dashboard

### Fastest Path to First Prediction

```bash
# 1. Get your first prediction (works with mock data)
python quick_start.py

# 2. Set up Magic8-Companion API
python setup_companion_api.py

# 3. Integrate with DiscordTrading
python integrate_discord_trading.py

# 4. Monitor predictions in real-time
python monitor_predictions.py
```

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

### Quick Start with Helper Scripts

#### 1. Prerequisites Check & First Prediction

```bash
# This script checks prerequisites and can create a mock model for testing
python quick_start.py
```

The script will:
- Check for trained models
- Test data provider connections
- Make a sample prediction
- Show you exactly what to do next

#### 2. Set Up Magic8-Companion API

```bash
# Automatically configure Magic8-Companion for data sharing
python setup_companion_api.py

# Or just test if the API is already working
python setup_companion_api.py --test-only
```

#### 3. Integrate with DiscordTrading

```bash
# Automated integration (finds DiscordTrading automatically)
python integrate_discord_trading.py

# Or specify the path
python integrate_discord_trading.py --discord-path /path/to/DiscordTrading
```

This script:
- Copies all necessary files
- Creates integration wrapper
- Updates config.yaml
- Shows manual integration steps

#### 4. Monitor Predictions

```bash
# Real-time monitoring dashboard
python monitor_predictions.py

# With custom log file
python monitor_predictions.py --log-file logs/my_predictions.jsonl
```

Features:
- Live updating statistics
- Approval rates by symbol/strategy
- Recent prediction history
- Performance metrics

### Manual Installation

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

#### Option 1: Automated Integration (Recommended)

```bash
# Run the integration script
python integrate_discord_trading.py

# Follow the prompts and instructions
```

#### Option 2: Manual Integration

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
from magic8_predictor_integration import Magic8PredictorIntegration

# In __init__
self.ml_predictor = Magic8PredictorIntegration(self.config)

# In process_trade_instruction()
if hasattr(self, 'ml_predictor'):
    should_trade, prediction = await self.ml_predictor.should_trade(order)
    if not should_trade:
        logger.info(f"Trade rejected by ML prediction")
        return None
```

#### Option 3: API Service

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
# Use the helper script
python setup_companion_api.py
cd /path/to/Magic8-Companion
./start_with_api.sh

# Or manually
export M8C_ENABLE_DATA_API=true
python -m magic8_companion
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

# Terminal 3: Prediction Monitor (optional)
cd /opt/magic8-accuracy-predictor
python monitor_predictions.py

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

#### 1. Real-Time Dashboard

```bash
# Start the monitoring dashboard
python monitor_predictions.py

# Features:
# - Live prediction statistics
# - Approval rates by symbol/strategy
# - Recent prediction feed
# - Performance metrics
```

#### 2. Health Checks

```bash
# Check predictor health
curl http://localhost:8767/health

# Check data provider status
python setup_companion_api.py --test-only
```

#### 3. Log Analysis

```bash
# Watch prediction logs
tail -f logs/predictions.jsonl | jq

# Generate daily report
python scripts/generate_daily_report.py

# Monitor errors
grep ERROR logs/magic8_predictor.log
```

### Troubleshooting

#### Common Issues & Solutions

##### "Failed to connect to Magic8-Companion"

```bash
# Quick fix
python setup_companion_api.py
```

Or manually:
1. Check Magic8-Companion is running: `ps aux | grep magic8`
2. Verify API is enabled: `curl http://localhost:8765/health`
3. Check firewall settings

##### "No predictor available for symbol"

1. Check model configuration includes the symbol
2. Verify model file exists at configured path
3. Add symbol to model config:
```yaml
prediction:
  models:
    - name: "xgboost_phase1"
      symbols: ["SPX", "SPY", "NEW_SYMBOL"]
```

##### High prediction latency

1. Enable caching in config
2. Use Redis instead of HTTP API
3. Check with: `python monitor_predictions.py`
4. Reduce feature generation complexity

##### IBKR connection conflicts

1. Use Magic8-Companion as primary data source
2. Ensure unique client IDs for each connection
3. Use different ports for multiple gateways:
   - Magic8-Companion: 7497
   - Standalone predictor: 7498
   - DiscordTrading: 7496

### Maintenance

#### Daily Tasks

1. **Check prediction performance**:
```bash
# View live dashboard
python monitor_predictions.py

# Generate report
python scripts/generate_daily_report.py
```

2. **Verify system health**:
```bash
python setup_companion_api.py --test-only
python quick_start.py
```

#### Weekly Tasks

1. **Review prediction accuracy**:
```python
python scripts/analyze_weekly_performance.py
```

2. **Clean up old logs**:
```bash
find logs -name "*.log" -mtime +7 -delete
find logs -name "*.jsonl" -mtime +30 -delete
```

#### Monthly Tasks

1. **Retrain models with new data**
2. **Update feature engineering if needed**
3. **Review and optimize configuration**

### Production Checklist

- [ ] Run `quick_start.py` to verify setup
- [ ] Set `environment: "production"` in config
- [ ] Configure proper logging levels
- [ ] Set up `monitor_predictions.py` on dedicated screen/tmux
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

## Implementation Status

### Completed ✅

1. **Core Predictor Implementation**
   - Real-time prediction engine
   - Feature engineering pipeline
   - Model loading and caching

2. **Data Providers**
   - CompanionDataProvider (HTTP API)
   - RedisDataProvider (Pub/Sub)
   - StandaloneDataProvider (Direct IB)
   - FallbackDataProvider (Automatic failover)

3. **Integration Scripts**
   - `quick_start.py` - First prediction helper
   - `integrate_discord_trading.py` - Automated integration
   - `setup_companion_api.py` - API configuration
   - `monitor_predictions.py` - Live dashboard

4. **Configuration**
   - Flexible YAML configuration
   - Environment variable overrides
   - Multi-environment support

### Next Steps 🚀

1. **Train Phase 1 Model** (if not done)
   ```bash
   # Download IBKR data
   ./download_phase1_data.sh
   
   # Process data
   python src/phase1_data_preparation.py
   
   # Train model
   python src/models/xgboost_baseline.py
   ```

2. **Enable Magic8-Companion API**
   ```bash
   python setup_companion_api.py
   ```

3. **Integrate with DiscordTrading**
   ```bash
   python integrate_discord_trading.py
   ```

4. **Start Monitoring**
   ```bash
   python monitor_predictions.py
   ```

## Conclusion

This integration provides a robust, scalable solution for real-time Magic8 order predictions. The helper scripts enable a "ship-fast" approach - you can get your first prediction in minutes and integrate with DiscordTrading in under 10 minutes. The modular design allows for flexible deployment options while maintaining production-ready quality.

For questions or issues, refer to the troubleshooting section or check the individual script help:
```bash
python quick_start.py --help
python integrate_discord_trading.py --help
python setup_companion_api.py --help
python monitor_predictions.py --help
```
