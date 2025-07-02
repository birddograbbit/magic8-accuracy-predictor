# Troubleshooting IBKR Connection Issues

## NDX Subscription Error Causing Disconnection

### Problem
When running `python src/prediction_api.py`, you see:
```
ERROR:ib_insync.wrapper:Error 354, reqId 11: Requested market data is not subscribed...NDX NASDAQ 100 Stock Index
INFO:ib_insync.ib:Disconnecting from 127.0.0.1:7497...
```

The entire IBKR connection disconnects, preventing other symbols from being fetched.

### Solution Applied (July 2, 2025)

The system has been updated to handle subscription errors gracefully:

1. **Error Handler**: Catches error 354 specifically for missing subscriptions
2. **Failed Symbol Tracking**: Marks symbols with subscription issues to skip future attempts
3. **Connection Preservation**: Prevents subscription errors from disconnecting the entire connection
4. **Proper Cleanup**: Cancels market data requests after use to prevent lingering subscriptions

### How It Works Now

When you start the prediction API:
1. System attempts to fetch data for all symbols (SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA, VIX)
2. If NDX (or any symbol) returns a subscription error:
   - The error is logged as a warning
   - NDX is marked as failed and will use mock data
   - The connection remains active for other symbols
3. Other symbols continue to fetch real data normally
4. Future requests for NDX skip IBKR and use mock data directly

### Expected Behavior

You should see logs like this:
```
INFO:data_providers.standalone_provider:Connected to IBKR on client_id=99
WARNING:data_providers.standalone_provider:Market data not subscribed for NDX
WARNING:data_manager:Market data subscription missing for NDX, will use mock data
INFO:prediction_api:Using mock data for symbols without subscriptions: ['NDX']
```

The API continues running normally, using:
- **Real data**: SPX, SPY, VIX, and other subscribed symbols
- **Mock data**: NDX (20000.0) and any other unsubscribed symbols

### Testing the Fix

Run the test script to verify:
```bash
python test_resilient_connection.py
```

Expected output:
```
--- Testing SPX ---
✓ SPX: $5850.00 from ibkr

--- Testing NDX ---
✓ NDX: $20000.00 from mock
  (Using mock data due to subscription issues)

--- Testing VIX ---
✓ VIX: $15.00 from ibkr

✅ Test completed - connection remained stable despite NDX error!
```

### Alternative Solutions

If you prefer different behavior:

1. **Get NDX Subscription**: 
   - Log into IBKR Account Management
   - Subscribe to NASDAQ market data
   - NDX will then work with real data

2. **Remove NDX from Symbol List**:
   - Edit `src/prediction_api.py`
   - Remove 'NDX' from the symbols list in `update_market_data()`

3. **Use Different Mock Price**:
   - Edit `src/data_manager.py`
   - Change NDX mock price in `_get_mock_data()` method

### Key Points

- ✅ System continues working despite subscription errors
- ✅ Other symbols fetch real data normally
- ✅ No manual intervention required
- ✅ Transparent about which symbols use mock vs real data
- ✅ Connection remains stable throughout operation
