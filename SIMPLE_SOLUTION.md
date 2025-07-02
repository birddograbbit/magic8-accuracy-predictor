# SIMPLIFIED IB CONNECTION - ALL IN ONE FILE

## What I Changed

Removed ALL the complex modules and put everything directly in `src/prediction_api_simple.py`:
- No singleton patterns
- No separate data managers
- No complex async handling
- Just direct IB connection like your sample scripts

## The Simple Approach

```python
# Direct IB connection in the API file
def connect_ib():
    global ib, ib_connected
    
    try:
        ib = IB()
        ib.connect('127.0.0.1', 7497, clientId=99)
        time.sleep(0.5)
        
        if ib.isConnected():
            ib_connected = True
            return True
    except Exception as e:
        logger.error(f"IB connection error: {e}")
        return False

# Direct price fetching
def get_ib_price(symbol: str) -> float:
    if not ib_connected:
        raise Exception("Not connected to IB")
    
    # Create contract and get price
    contract = Index(symbol, 'CBOE', 'USD')  # or Stock
    ticker = ib.reqMktData(contract, '', False, False)
    
    # Wait for price...
    # Cancel and return
```

## Files

1. **`src/prediction_api_simple.py`** - Everything in one file
2. **`start_api_simple.py`** - Simple startup script
3. **`test_direct_ib.py`** - Test IB connection directly

## Removed

- Deleted `src/simple_ib/` directory and all its modules
- No more singletons, no more data managers
- No more passing connections between modules

## How to Run

### 1. Test IB Connection First
```bash
cd /Users/jt/magic8/magic8-accuracy-predictor
python test_direct_ib.py
```

This should show:
```
✓ Connected successfully!
✓ SPX price: $5890.50
✓ Test passed!
```

### 2. Start the API
```bash
./start_api_simple.py
```

Or directly:
```bash
python -m uvicorn src.prediction_api_simple:app --host 0.0.0.0 --port 8000
```

## Key Points

- IB connection is created in a separate thread during startup to avoid event loop conflicts
- Everything is in one file - no complex module imports
- Falls back to mock data if IB is not available
- Simple caching with a dictionary and threading lock

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

This is as simple as it gets - just like your working sample scripts!
