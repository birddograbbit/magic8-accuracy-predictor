#!/usr/bin/env python3
"""
Test direct IB connection - as simple as possible.
Just like your sample scripts.
"""

import time
import math
from ib_insync import IB, Stock, Index

def test_ib_connection():
    """Test IB connection directly."""
    print("Testing Direct IB Connection")
    print("=" * 40)
    
    ib = IB()
    
    try:
        # Connect
        print("Connecting to IB Gateway...")
        ib.connect('127.0.0.1', 7497, clientId=99)
        
        # Wait for connection
        time.sleep(0.5)
        
        if ib.isConnected():
            print("✓ Connected successfully!")
        else:
            print("✗ Failed to connect")
            return False
        
        # Test getting SPX price
        print("\nGetting SPX price...")
        contract = Index('SPX', 'CBOE', 'USD')
        ticker = ib.reqMktData(contract, '', False, False)
        
        # Wait for price
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
        
        # Make sure to cancel before checking price
        ib.cancelMktData(ticker)
        
        if price and not math.isnan(price):
            print(f"✓ SPX price: ${price:.2f}")
        else:
            print("✗ Could not get valid SPX price (market may be closed)")
        
        # Disconnect
        print("\nDisconnecting...")
        ib.disconnect()
        print("✓ Disconnected")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        if ib.isConnected():
            ib.disconnect()
        return False

if __name__ == "__main__":
    if test_ib_connection():
        print("\n✓ Test passed!")
    else:
        print("\n✗ Test failed!")
