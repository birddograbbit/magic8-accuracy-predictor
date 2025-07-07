# Real-Time Prediction Integration Guide

This guide explains how to integrate the trained ML model with Magic8's trading system for real-time predictions.

## Overview

After training your model with `phase1_data_preparation.py` and `xgboost_baseline.py`, you have several options for real-time predictions:

### Option 1: FastAPI REST Service (Recommended)
- Simple HTTP API
- Easy to integrate with any system
- Scalable and production-ready

### Option 2: Direct IBKR Integration
- Connects directly to IBKR TWS/Gateway
- Real-time market data updates
- More complex setup

### Option 3: Custom Integration
- Direct Python integration
- Most flexible

## Quick Start: FastAPI Service

### 1. Install Dependencies
```bash
pip install fastapi uvicorn pandas numpy xgboost scikit-learn
```

### 2. Start the Prediction Service
```bash
./run_realtime_api.sh
```
The API will be available at `http://localhost:8000` and automatically
generates all 74 Phase‑1 features using live market data. Ensure the
Magic8‑Companion API or IBKR Gateway is running so market data is
available. The service falls back to mock prices when both sources fail.

`src/prediction_api_realtime.py` uses `DataManager` to pull current prices
and historical bars from either data source with caching (30&nbsp;seconds for
prices, five minutes for bars). These values are passed to
`RealTimeFeatureGenerator`, which computes SMA, momentum, RSI and other
indicators and then orders them according to `data/phase1_processed/feature_info.json`.
Price and VIX data are fetched concurrently so prediction responses remain
fast while still matching the exact feature set used during model training.

### 3. Test the API
```bash
# Health check
curl http://localhost:8000/

# Single prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "Butterfly",
    "symbol": "SPX",
    "premium": 25.50,
    "predicted_price": 5850.00
  }'

# Batch predictions
curl -X POST http://localhost:8000/predict/batch \
  -H "Content-Type: application/json" \
  -d '{
    "trades": [
      {"strategy": "Butterfly", "symbol": "SPX", "premium": 25.50, "predicted_price": 5850.00},
      {"strategy": "Iron Condor", "symbol": "SPX", "premium": 0.65, "predicted_price": 5850.00}
    ]
  }'
```

## API Endpoints

### `POST /predict`
Predict a single trade outcome.

**Request:**
```json
{
  "strategy": "Butterfly",
  "symbol": "SPX",
  "premium": 25.50,
  "predicted_price": 5850.00,
  "risk": 25.50,      // optional
  "reward": 24.50     // optional
}
```

**Response:**
```json
{
  "timestamp": "2025-06-30T15:30:00",
  "strategy": "Butterfly",
  "symbol": "SPX",
  "premium": 25.50,
  "predicted_price": 5850.00,
  "win_probability": 0.6234,
  "prediction": "WIN",
  "confidence": 0.6234,
  "recommendation": "BUY",
  "risk_score": 0.35
}
```

### `POST /predict/batch`
Predict multiple trades at once.
Request body:
```json
{
  "requests": [
    {"strategy": "Butterfly", "symbol": "SPX", "premium": 25.5, "predicted_price": 5850},
    {"strategy": "Iron Condor", "symbol": "SPX", "premium": 0.65, "predicted_price": 5850}
  ]
}
```
Returns a list of `PredictionResponse` objects and cache metrics.

### `GET /feature-importance`
Get the most important features from the model.

### `GET /market-data/{symbol}`
Get current market data for a symbol.

## Integration with Magic8

### Method 1: Direct API Calls

```python
import requests
import json

def get_magic8_prediction(strategy, symbol, premium, predicted_price):
    """Get prediction from ML service"""
    
    url = "http://localhost:8000/predict"
    payload = {
        "strategy": strategy,
        "symbol": symbol,
        "premium": premium,
        "predicted_price": predicted_price
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        return {
            'should_trade': result['recommendation'] in ['BUY', 'STRONG BUY'],
            'win_probability': result['win_probability'],
            'risk_score': result['risk_score']
        }
    else:
        return None

# Example usage in Magic8
def process_magic8_signal(signal):
    """Process a Magic8 trading signal"""
    
    # Get ML prediction
    prediction = get_magic8_prediction(
        strategy=signal['strategy'],
        symbol=signal['symbol'],
        premium=signal['premium'],
        predicted_price=signal['predicted_price']
    )
    
    if prediction and prediction['should_trade']:
        # Execute trade
        execute_trade(signal)
    else:
        # Skip trade
        log_skipped_trade(signal, prediction)
```

### Method 2: Webhook Integration

```python
# In Magic8 system
def send_to_ml_service(orders):
    """Send orders to ML service for prediction"""
    
    webhook_url = "http://localhost:8000/predict/batch"
    
    payload = {
        "trades": [
            {
                "strategy": order['strategy'],
                "symbol": order['symbol'],
                "premium": order['premium'],
                "predicted_price": order['predicted_price']
            }
            for order in orders
        ]
    }
    
    response = requests.post(webhook_url, json=payload)
    predictions = response.json()['predictions']
    
    # Filter trades based on predictions
    approved_trades = []
    for order, prediction in zip(orders, predictions):
        if prediction['recommendation'] in ['BUY', 'STRONG BUY']:
            approved_trades.append(order)
            
    return approved_trades
```

## Real-Time Market Data Integration

For the most accurate predictions, integrate real-time market data:

### Using IBKR (requires TWS/Gateway)

```python
from src.real_time_predictor import Magic8Predictor

# Initialize predictor
predictor = Magic8Predictor()

# Connect to IBKR
predictor.connect_to_ibkr(host='127.0.0.1', port=7497)

# Make prediction with live data
result = predictor.predict_trade(
    strategy='Butterfly',
    symbol='SPX',
    premium=25.50,
    predicted_price=5850.00
)
```

## Production Deployment

### 1. Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY models/ ./models/
COPY data/phase1_processed/feature_info.json ./data/phase1_processed/

CMD ["uvicorn", "src.prediction_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t magic8-predictor .
docker run -p 8000:8000 magic8-predictor
```

### 2. Using systemd (Linux)

Create `/etc/systemd/system/magic8-predictor.service`:
```ini
[Unit]
Description=Magic8 ML Prediction Service
After=network.target

[Service]
Type=simple
User=magic8
WorkingDirectory=/opt/magic8-predictor
ExecStart=/opt/magic8-predictor/venv/bin/python -m uvicorn src.prediction_api:app --host 0.0.0.0 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl enable magic8-predictor
sudo systemctl start magic8-predictor
```

## Monitoring and Logging

### 1. Track Prediction Performance

```python
# Add to your integration
def log_prediction_result(prediction, actual_outcome):
    """Log prediction vs actual for monitoring"""
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'prediction': prediction,
        'actual': actual_outcome,
        'correct': prediction['prediction'] == actual_outcome
    }
    
    # Save to database or file
    with open('predictions_log.jsonl', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
```

### 2. Performance Metrics

```python
# Calculate daily performance
def calculate_daily_metrics(log_file):
    """Calculate prediction accuracy metrics"""
    
    correct = 0
    total = 0
    
    with open(log_file, 'r') as f:
        for line in f:
            entry = json.loads(line)
            total += 1
            if entry['correct']:
                correct += 1
                
    accuracy = correct / total if total > 0 else 0
    
    return {
        'date': datetime.now().date().isoformat(),
        'total_predictions': total,
        'correct_predictions': correct,
        'accuracy': accuracy
    }
```

## Best Practices

### 1. Feature Drift Monitoring
- Track feature distributions over time
- Alert when features deviate from training data

### 2. Model Retraining
- Retrain weekly/monthly with recent data
- A/B test new models before full deployment

### 3. Risk Management
- Set maximum daily loss limits
- Skip trades when market conditions are unusual
- Use position sizing based on confidence

### 4. Latency Optimization
- Cache market data updates
- Use connection pooling for API calls
- Consider edge deployment for lowest latency

## Example Integration Script

Complete example for Magic8 integration:

```python
#!/usr/bin/env python3
"""
Magic8 ML Integration
Connects Magic8 signals to ML predictions
"""

import requests
import time
from datetime import datetime

class Magic8MLIntegration:
    def __init__(self, ml_api_url="http://localhost:8000"):
        self.ml_api_url = ml_api_url
        self.check_ml_service()
        
    def check_ml_service(self):
        """Verify ML service is running"""
        try:
            response = requests.get(f"{self.ml_api_url}/")
            if response.status_code == 200:
                print("✅ ML service is running")
            else:
                print("❌ ML service error")
        except:
            print("❌ Cannot connect to ML service")
            
    def process_signals(self, signals):
        """Process Magic8 signals through ML"""
        
        # Prepare batch request
        trades = [
            {
                "strategy": sig['strategy'],
                "symbol": sig['symbol'],
                "premium": sig['premium'],
                "predicted_price": sig['predicted_price']
            }
            for sig in signals
        ]
        
        # Get predictions
        response = requests.post(
            f"{self.ml_api_url}/predict/batch",
            json={"trades": trades}
        )
        
        if response.status_code != 200:
            print(f"Error getting predictions: {response.text}")
            return []
            
        predictions = response.json()['predictions']
        
        # Filter approved trades
        approved = []
        for signal, pred in zip(signals, predictions):
            if pred['recommendation'] in ['BUY', 'STRONG BUY']:
                signal['ml_prediction'] = pred
                approved.append(signal)
                print(f"✅ Approved: {signal['symbol']} {signal['strategy']} "
                      f"(confidence: {pred['confidence']:.2%})")
            else:
                print(f"❌ Rejected: {signal['symbol']} {signal['strategy']} "
                      f"(win prob: {pred['win_probability']:.2%})")
                
        return approved
    
    def run_continuous(self, get_signals_func, execute_trades_func):
        """Run continuous prediction loop"""
        
        print("Starting Magic8 ML integration...")
        
        while True:
            try:
                # Get pending signals
                signals = get_signals_func()
                
                if signals:
                    print(f"\nProcessing {len(signals)} signals...")
                    
                    # Get ML predictions
                    approved = self.process_signals(signals)
                    
                    # Execute approved trades
                    if approved:
                        execute_trades_func(approved)
                        
                # Wait 5 minutes
                time.sleep(300)
                
            except KeyboardInterrupt:
                print("\nShutting down...")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(60)

# Example usage
if __name__ == "__main__":
    integration = Magic8MLIntegration()
    
    # Mock functions - replace with actual Magic8 integration
    def get_signals():
        # In production, this would query Magic8 for pending trades
        return [
            {
                'strategy': 'Butterfly',
                'symbol': 'SPX',
                'premium': 25.50,
                'predicted_price': 5850.00
            }
        ]
    
    def execute_trades(trades):
        # In production, this would send orders to broker
        for trade in trades:
            print(f"Executing: {trade}")
    
    # Run the integration
    integration.run_continuous(get_signals, execute_trades)
```

## Troubleshooting

### Model not loading
- Check model file exists at `models/xgboost_phase1.pkl`
- Verify feature config at `data/phase1_processed/feature_info.json`

### Low prediction accuracy
- Ensure market data is up-to-date
- Check for feature drift
- Consider retraining with recent data

### High latency
- Move prediction service closer to Magic8
- Use batch predictions
- Cache market data
- Enable feature and prediction caching (see `performance.cache` in config)

## Next Steps

1. **Test the integration** with paper trading
2. **Monitor predictions** vs actual outcomes
3. **Optimize thresholds** for your risk tolerance
4. **Scale horizontally** for higher throughput
5. **Add more features** from Phase 2 plan

For questions or issues, check the repository:
https://github.com/birddograbbit/magic8-accuracy-predictor
