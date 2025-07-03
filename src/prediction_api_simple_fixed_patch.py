#!/usr/bin/env python3
"""
Simple patch for the existing prediction API to reduce market data errors.
This file contains the patches that can be applied to prediction_api_simple_fixed.py
"""

# PATCH 1: Improve the shutdown function in lifespan to avoid double cancellation
SHUTDOWN_PATCH = '''
# Replace the shutdown section in lifespan with this:

# Shutdown
logger.info("Shutting down...")

if ib and ib.isConnected():
    try:
        # Get current active tickers and cancel only valid ones
        active_tickers = []
        try:
            active_tickers = list(ib.tickers())
        except:
            pass
        
        for ticker in active_tickers:
            try:
                # Only cancel if the ticker is still valid
                if ticker and hasattr(ticker, 'contract'):
                    ib.cancelMktData(ticker)
                    logger.debug(f"Cancelled market data for {ticker.contract.symbol}")
            except Exception as e:
                # Suppress cancellation errors during shutdown
                logger.debug(f"Ignoring cancellation error during shutdown: {e}")
        
        ib.disconnect()
        logger.info("✓ Disconnected from IB")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

ib_connected = False
logger.info("Shutdown complete")
'''

# PATCH 2: Improve error handling in get_ib_price
GET_IB_PRICE_PATCH = '''
def get_ib_price(symbol: str) -> float:
    """Get price from IB - simple and direct with improved error handling."""
    global ib, ib_connected
    
    if not ib_connected or not ib or not ib.isConnected():
        raise Exception("Not connected to IB")
    
    ticker = None
    try:
        # Create contract
        if symbol in ['SPX', 'VIX', 'XSP']:
            contract = Index(symbol, 'CBOE', 'USD')
        elif symbol == 'RUT':
            contract = Index('RUT', 'RUSSELL', 'USD')
        elif symbol == 'NDX':
            contract = Index('NDX', 'NASDAQ', 'USD')
        else:
            contract = Stock(symbol, 'SMART', 'USD')
        
        # Request market data
        ticker = ib.reqMktData(contract, '', False, False)
        
        # Wait for price with timeout
        timeout = 2.0
        start_time = time.time()
        price = None
        
        while time.time() - start_time < timeout:
            if ticker.last and not math.isnan(ticker.last):
                price = ticker.last
                break
            elif ticker.close and not math.isnan(ticker.close):
                price = ticker.close
                break
            time.sleep(0.1)
        
        if price is None:
            raise Exception(f"Timeout getting price for {symbol}")
        
        return float(price)
        
    except Exception as e:
        logger.debug(f"Error getting IB price for {symbol}: {e}")
        raise
    finally:
        # Safe cleanup - only cancel if ticker exists and is valid
        if ticker is not None:
            try:
                ib.cancelMktData(ticker)
            except Exception as cancel_error:
                # Suppress cancellation errors - they're not critical
                logger.debug(f"Ignoring cancellation error for {symbol}: {cancel_error}")
'''

print("Available patches for prediction_api_simple_fixed.py:")
print("1. SHUTDOWN_PATCH - Improves shutdown logic to avoid double cancellation")
print("2. GET_IB_PRICE_PATCH - Adds better error handling for market data requests")
print("")
print("Apply these manually to prediction_api_simple_fixed.py or use the v2 version.") 