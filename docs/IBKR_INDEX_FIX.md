# IBKR Index Contract Fix (July 2, 2025)

## Issue
The StandaloneDataProvider was failing to retrieve data for certain indices (RUT, NDX) with the error:
```
Error 200, reqId 7: No security definition has been found for the request, contract: Index(symbol='RUT', exchange='CBOE')
```

## Root Cause
The indices were using incorrect exchanges. All indices were defaulting to 'CBOE' exchange, but some indices trade on different exchanges:

- **SPX**: CBOE ✓ (correct)
- **VIX**: CBOE ✓ (correct)
- **RUT**: RUSSELL (was incorrectly using CBOE)
- **NDX**: NASDAQ (was incorrectly using CBOE)
- **XSP**: CBOE ✓ (correct)

Additionally, there was a NaN handling issue when converting ticker sizes to integers.

## Fix Applied
1. Updated `_get_contract()` method in `standalone_provider.py` to use correct exchanges:
   ```python
   elif symbol == 'RUT':
       contract = Index('RUT', 'RUSSELL', 'USD')  # Russell 2000
   elif symbol == 'NDX':
       contract = Index('NDX', 'NASDAQ', 'USD')   # Nasdaq 100
   ```

2. Added safe conversion functions to handle NaN values:
   ```python
   def safe_int(value):
       if value is None or (isinstance(value, float) and math.isnan(value)):
           return 0
       return int(value)
   ```

3. Added USD currency to all index contracts for consistency.

## Testing
Run the test script to verify all indices work correctly:
```bash
python test_ibkr_indices.py
```

Expected output:
```
--- Testing SPX ---
SPX current price: $5850.00
  Bid: $5849.50 (size: 10)
  Ask: $5850.50 (size: 10)

--- Testing RUT ---
RUT current price: $2300.00
...
```

## Future Reference
When adding new indices to the system:
1. Check the correct exchange for the index (use IBKR's contract search or documentation)
2. Add the contract definition with proper exchange and currency
3. Test with `test_ibkr_indices.py` to ensure it works

Common index exchanges:
- CBOE: SPX, VIX, XSP
- NASDAQ: NDX, COMP
- RUSSELL: RUT
- NYSE: TICK (use Index('TICK-NYSE', 'NYSE', 'USD'))
