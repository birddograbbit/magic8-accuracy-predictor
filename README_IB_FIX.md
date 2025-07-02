# IB Connection Fix - Simple Direct Approach

## The Problem

The original implementation had complex async patterns that caused:
1. `TimeoutError()` when using `connectAsync()`
2. "event loop already running" errors
3. "coroutine was never awaited" warnings

## The Solution

Put everything in one file (`src/prediction_api_simple.py`) with direct IB connection, just like the working sample scripts.

### Key Fix: Proper Thread Handling

```python
def connect_ib_sync():
    """Connect to IB Gateway - handle async properly in thread."""
    global ib, ib_connected
    
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        ib = IB()
        
        # Use util.run to handle the connection properly
        def do_connect():
            ib.connect('127.0.0.1', 7497, clientId=99)
            return ib.isConnected()
        
        connected = util.run(do_connect)
        
        if connected:
            ib_connected = True
            return True
```

This approach:
1. Creates a new event loop for the thread (avoids FastAPI conflict)
2. Uses `util.run()` to handle IB's internal async properly
3. No more async/await complexity

## Files in This Fix

1. **`src/prediction_api_simple.py`** - Complete API with IB connection (all in one file)
2. **`test_direct_ib.py`** - Simple test script
3. **`start_api_simple.py`** - Startup script
4. **`run_simple_api.sh`** - Quick run script

## How to Use

```bash
# 1. Test IB connection
python test_direct_ib.py

# 2. Run the API
./run_simple_api.sh

# Or directly:
python -m uvicorn src.prediction_api_simple:app --host 0.0.0.0 --port 8000
```

## API Endpoints

```bash
# Health check
curl http://localhost:8000/

# Market data
curl http://localhost:8000/market/SPX

# Prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "Butterfly",
    "symbol": "SPX",
    "premium": 24.82,
    "predicted_price": 5855
  }'
```

## Why This Works

1. **Single file** - No complex imports or module dependencies
2. **Direct IB usage** - Just like your working trading scripts
3. **Proper thread handling** - Uses `util.run()` to handle IB's async internals
4. **Fallback to mock** - Works even without IB connection

## Integration with DiscordTrading

The API is fully compatible:
1. Start IB Gateway on port 7497
2. Run this API on port 8000
3. DiscordTrading connects as before

No changes needed to DiscordTrading!