# Handling Market Data Subscription Errors

## Overview
When using the IBKR connection for real-time data, you may encounter subscription errors for certain symbols (like NDX) if you don't have the required market data subscriptions. The system is now designed to be resilient to these failures.

## How It Works

### Automatic Fallback
The system now automatically handles subscription errors:

1. **First Attempt**: Tries Magic8-Companion API (if available)
2. **Second Attempt**: Tries direct IBKR connection
3. **On Subscription Error**: Marks the symbol as failed and uses mock data
4. **Future Requests**: Skips IBKR for failed symbols, using mock data directly

### Error Detection
The system detects subscription errors by looking for these patterns:
- "market data is not subscribed"
- "error 354"
- "requested market data is not subscribed" 
- "delayed market data is available"

### Mock Data Values
When a symbol fails due to subscription issues, these mock prices are used:
- SPX: 5850.0
- VIX: 15.0
- SPY: 585.0
- RUT: 2300.0
- QQQ: 500.0
- NDX: 20000.0
- AAPL: 220.0
- TSLA: 200.0

## Monitoring Failed Symbols

You can check which symbols are using mock data via the API:
```bash
curl http://localhost:8000/
```

Response includes:
```json
{
  "failed_symbols": ["NDX"],
  "data_sources": {
    "SPX": "ibkr",
    "NDX": "mock",
    "VIX": "ibkr"
  }
}
```

## Alternative: Disable Specific Symbols

If you prefer to disable certain symbols entirely, you can modify the symbol list in `src/prediction_api.py`:

```python
# Remove symbols you don't have subscriptions for
symbols = ['SPX', 'SPY', 'RUT', 'QQQ', 'XSP', 'AAPL', 'TSLA', 'VIX']  # Removed NDX
```

## Getting Market Data Subscriptions

To get real-time data for all symbols:
1. Log into IBKR Account Management
2. Go to Settings > User Settings > Market Data Subscriptions
3. Subscribe to the relevant exchanges:
   - NASDAQ (for NDX)
   - CBOE (for SPX, VIX, XSP)
   - RUSSELL (for RUT)
   - NYSE (for stocks)

## Benefits of Current Approach

1. **No Manual Configuration**: System automatically detects and handles subscription errors
2. **Graceful Degradation**: Uses mock data instead of crashing
3. **Transparent**: API shows which symbols are using mock vs real data
4. **Future-Proof**: If you add subscriptions later, the system will automatically start using real data

## Example Logs

When a subscription error occurs:
```
WARNING:data_manager:Market data subscription missing for NDX, will use mock data
INFO:prediction_api:Using mock data for symbols without subscriptions: ['NDX']
```

The system continues running normally, just using mock data for affected symbols.
