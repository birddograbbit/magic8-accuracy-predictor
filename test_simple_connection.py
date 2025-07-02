#!/usr/bin/env python3
"""
Test the simplified IB connection.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.simple_ib import ib_connection, SimpleDataManager
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_direct_connection():
    """Test direct IB connection."""
    print("\n" + "="*50)
    print("Testing Direct IB Connection")
    print("="*50)
    
    # Test connection
    print("\n1. Testing connection...")
    connected = ib_connection.connect(port=7497, client_id=99)
    if connected:
        print("✓ Connected successfully!")
    else:
        print("✗ Connection failed")
        return False
        
    # Test price fetch
    print("\n2. Testing price fetch...")
    try:
        price = ib_connection.get_current_price('SPX')
        print(f"✓ SPX price: ${price:.2f}")
    except Exception as e:
        print(f"✗ Price fetch failed: {e}")
        
    # Test historical data
    print("\n3. Testing historical data...")
    try:
        bars = ib_connection.get_historical_data('SPX', '1 D', '5 mins')
        print(f"✓ Got {len(bars)} historical bars")
        if bars:
            latest = bars[-1]
            print(f"  Latest bar: {latest['time']} - Close: ${latest['close']:.2f}")
    except Exception as e:
        print(f"✗ Historical data failed: {e}")
        
    # Disconnect
    print("\n4. Disconnecting...")
    ib_connection.disconnect()
    print("✓ Disconnected")
    
    return True

def test_data_manager():
    """Test data manager."""
    print("\n" + "="*50)
    print("Testing Data Manager")
    print("="*50)
    
    config = {
        'ib': {
            'host': '127.0.0.1',
            'port': 7497,
            'client_id': 99
        }
    }
    
    dm = SimpleDataManager(config)
    
    # Connect
    print("\n1. Connecting via data manager...")
    if dm.connect():
        print("✓ Connected")
    else:
        print("✗ Connection failed")
        return False
        
    # Test market data fetch
    print("\n2. Testing market data fetch...")
    symbols = ['SPX', 'VIX', 'SPY']
    
    for symbol in symbols:
        try:
            data = dm.get_market_data(symbol)
            print(f"✓ {symbol}: ${data['price']:.2f} (vol: {data['volatility']:.2%}) [{data['source']}]")
        except Exception as e:
            print(f"✗ {symbol}: {e}")
            
    # Test caching
    print("\n3. Testing cache (should be instant)...")
    start = time.time()
    data = dm.get_market_data('SPX')
    elapsed = time.time() - start
    print(f"✓ Cache hit: {elapsed:.3f} seconds")
    
    # Disconnect
    print("\n4. Disconnecting...")
    dm.disconnect()
    print("✓ Disconnected")
    
    return True

def main():
    print("Simple IB Connection Test")
    print("=" * 50)
    print("Make sure IB Gateway is running on port 7497")
    print("=" * 50)
    
    # Test direct connection
    if not test_direct_connection():
        print("\n✗ Direct connection test failed")
        return 1
        
    # Small delay between tests
    time.sleep(1)
    
    # Test data manager
    if not test_data_manager():
        print("\n✗ Data manager test failed")
        return 1
        
    print("\n" + "="*50)
    print("✓ All tests passed!")
    print("="*50)
    return 0

if __name__ == "__main__":
    sys.exit(main())
