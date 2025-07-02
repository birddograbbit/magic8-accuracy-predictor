# Simplified IB Connection for Magic8 Accuracy Predictor

## Overview

This is a simplified IB connection approach that follows the pattern from working examples like `option_trading.py` and `discord_trading_bot.py`. 

**Key principles:**
- ONE IB connection instance (singleton pattern)
- Synchronous connection (not async)
- Simple error handling
- Pass the connection object around

## Why This Approach?

The original async approach was timing out because:
1. The IB API connection handshake wasn't completing properly with async
2. Multiple connection attempts were being made
3. Over-engineered async/await patterns don't work well with IB API

## Files

- `ib_connection.py` - Simple singleton IB connection manager
- `data_manager.py` - Simplified data manager with caching
- `prediction_api_simple.py` - FastAPI service using simple connection
- `test_simple_connection.py` - Test script to verify connection

## Usage

### 1. Test the Connection

```bash
cd magic8-accuracy-predictor
python test_simple_connection.py
```

Expected output:
```
✓ Connected successfully!
✓ SPX price: $5890.50
✓ Got 78 historical bars
✓ All tests passed!
```

### 2. Start the Simplified API

```bash
cd magic8-accuracy-predictor
./start_simple_api.py
```

Or directly:
```bash
python -m uvicorn src.simple_ib.prediction_api_simple:app --host 0.0.0.0 --port 8000
```

### 3. Test the API

```bash
# Health check
curl http://localhost:8000/

# Get market data
curl http://localhost:8000/market/SPX

# Make prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "Butterfly",
    "symbol": "SPX", 
    "premium": 24.82,
    "predicted_price": 5855
  }'
```

## Integration with DiscordTrading

The API is compatible with the existing DiscordTrading integration. Just ensure:

1. IB Gateway is running on port 7497
2. Start the simplified API on port 8000
3. DiscordTrading will connect and use predictions as before

## Key Differences from Original

1. **Synchronous Connection**: Uses `ib.connect()` not `connectAsync()`
2. **Singleton Pattern**: One global connection instance
3. **Simple Threading**: Background updates use simple threads, not asyncio
4. **Direct Error Handling**: Catches subscription errors and continues

## Troubleshooting

### Connection Timeout
- Ensure IB Gateway is running
- Check port 7497 is not blocked
- Try client ID 99 (or another unused ID)

### Market Data Not Subscribed
- The code handles this gracefully
- Falls back to mock data for unsubscribed symbols
- Symbols are cached to avoid repeated attempts

### API Won't Start
- Check model file exists: `models/xgboost_phase1_model.pkl`
- Check feature config exists: `data/phase1_processed/feature_info.json`
- Ensure port 8000 is free

## Next Steps

1. Replace the original complex async implementation with this simple approach
2. Update the main prediction_api.py to use SimpleDataManager
3. Remove the over-engineered standalone_provider.py

The simple approach is more reliable and follows proven patterns from production trading systems.
