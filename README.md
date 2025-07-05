# Magic8 Accuracy Predictor

A sophisticated ML-based prediction system for Magic8 trading strategies, featuring multi-model architecture with per-symbol optimization.

## 🚀 Overview

The Magic8 Accuracy Predictor uses XGBoost models trained on historical trade data to predict win probabilities for option strategies (Butterfly, Iron Condor, Sonar, Vertical). It features:

- **Multi-Model Architecture**: Individual models for 8 symbols + 2 grouped models
- **Dynamic Thresholds**: Per-symbol-strategy optimized thresholds
- **Real-time Predictions**: FastAPI service with <200ms latency
- **90-94% Accuracy**: Validated on 1M+ historical trades

## 📋 Prerequisites

- Python 3.9+
- IBKR Gateway/TWS (for live data)
- 8GB+ RAM
- Trained models in `models/` directory

## 🛠️ Installation

```bash
# Clone repository
git clone https://github.com/birddograbbit/magic8-accuracy-predictor.git
cd magic8-accuracy-predictor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 📊 Model Architecture

### Individual Models (8 symbols)
- **Large Scale**: NDX (90.75%), RUT (92.07%)
- **Medium Scale**: SPX (90.03%), SPY (91.48%)
- **Small Scale**: XSP (90.59%), QQQ (91.02%), AAPL (94.08%), TSLA (94.04%)

### Grouped Models (2 groups)
- **SPX_SPY**: Combined medium-scale model (89.95%)
- **QQQ_AAPL_TSLA**: Combined small-scale model (90.13%)

## 🚦 Quick Start

### 1. Configure Data Source

Edit `config/config.yaml`:

```yaml
data_source:
  primary: "companion"      # or "standalone" for direct IBKR
  
  companion:
    base_url: "http://localhost:8765"
    
  standalone:
    ib_host: "127.0.0.1"
    ib_port: 7497          # IBKR Gateway port
    client_id: 99
```

### 2. Start Prediction API

```bash
# Using real-time features (recommended)
python src/prediction_api_realtime.py

# API will be available at http://localhost:8000
```

### 3. Test Predictions

```python
import requests

# Test prediction
response = requests.post('http://localhost:8000/predict', json={
    'symbol': 'SPX',
    'strategy': 'Butterfly',
    'premium': 24.82,
    'predicted_price': 5855
})

print(response.json())
# Output: {
#   "symbol": "SPX",
#   "strategy": "Butterfly", 
#   "win_probability": 0.723,
#   "prediction": "WIN",
#   "threshold": 0.55
# }
```

## 📁 Project Structure

```
magic8-accuracy-predictor/
├── config/
│   └── config.yaml              # Main configuration
├── data/
│   ├── symbol_specific/         # Per-symbol CSV files
│   └── phase1_processed/        # Processed features
├── models/
│   ├── individual/              # Per-symbol models
│   │   ├── *_trades_model.pkl
│   │   └── thresholds.json     # Optimized thresholds
│   ├── grouped/                 # Grouped models
│   │   ├── *_combined_model.pkl
│   │   └── thresholds_grouped.json
│   └── xgboost_phase1_model.pkl # Default fallback
├── src/
│   ├── data_providers/          # Market data interfaces
│   ├── feature_engineering/     # Feature generators
│   ├── models/                  # Model classes
│   └── prediction_api_realtime.py # Main API
└── docs/                        # Documentation
```

## 🔧 Full Deployment Workflow

### Step 1: Data Preparation

```bash
# Process historical data (if not done)
python src/data_processing/process_magic8_data_complete.py \
    --input data/raw \
    --output data/processed

# Split by symbol
python src/data_processing/split_by_symbol.py \
    --input data/processed/all_trades.csv \
    --output data/symbol_specific
```

### Step 2: Model Training

```bash
# Train individual models
python train_symbol_models.py \
    --data_dir data/symbol_specific \
    --output_dir models/individual

# Train grouped models
python train_grouped_models.py \
    --data_dir data/symbol_specific \
    --output_dir models/grouped \
    --groups '{"SPX_SPY": ["SPX", "SPY"], "QQQ_AAPL_TSLA": ["QQQ", "AAPL", "TSLA"]}'
```

### Step 3: Threshold Optimization

```bash
# Optimize individual thresholds
python optimize_thresholds.py \
    data/symbol_specific \
    models/individual

# Optimize grouped thresholds
python optimize_thresholds_grouped.py \
    data/symbol_specific \
    models/grouped
```

### Step 4: Production Deployment

```bash
# 1. Set production config
export ENVIRONMENT=production

# 2. Start IBKR Gateway (if using standalone)
# Ensure Gateway is running on port 7497

# 3. Start prediction API
python src/prediction_api_realtime.py

# 4. (Optional) Run with gunicorn for production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    src.prediction_api_realtime:app
```

### Step 5: Integration Testing

```bash
# Test all endpoints
python tests/test_api_endpoints.py

# Validate model loading
python tests/validate_models.py

# Check threshold application
python tests/test_thresholds.py
```

## 🔌 API Endpoints

### Health Check
```
GET /
Returns: API status and loaded models
```

### Market Data
```
GET /market/{symbol}
Returns: Current price and volatility
```

### Prediction
```
POST /predict
Body: {
    "symbol": "SPX",
    "strategy": "Butterfly",
    "premium": 24.82,
    "predicted_price": 5855
}
Returns: {
    "win_probability": 0.723,
    "prediction": "WIN",
    "threshold": 0.55
}
```

## 🔍 Monitoring

### Key Metrics
- **Prediction Latency**: Target <200ms
- **Model Accuracy**: Track by symbol/strategy
- **Trade Approval Rate**: Monitor threshold effectiveness
- **Profit vs Baseline**: Daily comparison

### Logging
```python
# View logs
tail -f logs/predictions.log

# Parse prediction history
python scripts/analyze_predictions.py logs/predictions.jsonl
```

## 🚨 Troubleshooting

### Common Issues

1. **Model Not Found**
   ```bash
   # Check model files exist
   ls -la models/individual/
   ls -la models/grouped/
   ```

2. **IBKR Connection Failed**
   - Verify Gateway is running
   - Check port 7497 is accessible
   - Ensure API permissions enabled

3. **Threshold Not Applied**
   ```bash
   # Verify threshold files
   cat models/individual/thresholds.json
   cat models/grouped/thresholds_grouped.json
   ```

## 🤝 Integration Examples

### DiscordTrading Bot
```python
from ml_prediction_client import check_ml_prediction_sync

# In your trade handler
should_execute, reason = check_ml_prediction_sync(
    instruction={'symbol': 'SPX', 'strategy': 'Butterfly', ...},
    min_prob=0.55
)
```

### Magic8-Companion
```python
# Configure in config.yaml
integration:
  magic8_companion:
    enabled: true
    sync_predictions: true
```

## 📈 Performance Optimization

### Caching
- Market data cached for 5 minutes
- Feature calculations cached per symbol
- Model predictions logged for analysis

### Scaling
- Use Redis for distributed caching
- Deploy multiple API instances
- Load balance with nginx

## 🔐 Security

- API authentication available (see docs/API_AUTH.md)
- SSL/TLS support for production
- Rate limiting configurable

## 📚 Additional Resources

- [Multi-Model Overview](docs/MULTI_MODEL_OVERVIEW.md)
- [Feature Engineering Guide](docs/FEATURE_ENGINEERING.md)
- [Threshold Optimization](docs/THRESHOLD_OPTIMIZATION.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)

## 🤖 Support

For issues or questions:
- Review [troubleshooting guide](docs/TROUBLESHOOTING.md)
- Check [FAQ](docs/FAQ.md)
- Submit GitHub issue

---

**Version**: 2.0.0 | **Last Updated**: January 2025