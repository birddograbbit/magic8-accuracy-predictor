# Essential Files in This PR

The PR has been cleaned up to contain only the essential files:

1. **src/prediction_api_simple.py** - The main API with IB connection fix
2. **test_direct_ib.py** - Test script for IB connection
3. **start_api_simple.py** - Startup script
4. **run_simple_api.sh** - Quick run script
5. **README_IB_FIX.md** - Documentation of the fix

## The Key Fix

The async warning was fixed by properly handling IB connection in a thread:

```python
def connect_ib_sync():
    # Create new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    ib = IB()
    
    # Use util.run to handle the connection properly
    def do_connect():
        ib.connect('127.0.0.1', 7497, clientId=99)
        return ib.isConnected()
    
    connected = util.run(do_connect)
```

This prevents the "coroutine was never awaited" warning.