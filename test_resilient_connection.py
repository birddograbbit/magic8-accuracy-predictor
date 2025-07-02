#!/usr/bin/env python3
"""
Test the resilient IBKR connection with NDX subscription error handling.
"""

import asyncio
import logging
from src.data_manager import DataManager
from src.constants import DEFAULT_IB_PORT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_resilient_connection():
    """Test that the system handles NDX subscription errors gracefully."""
    
    config = {
        'companion': {
            'enabled': False,  # Skip companion to test IBKR directly
            'base_url': 'http://localhost:8765'
        },
        'standalone': {
            'enabled': True,
            'ib_host': '127.0.0.1',
            'ib_port': DEFAULT_IB_PORT,
            'client_id': 99
        }
    }
    
    print("Testing resilient IBKR connection with subscription error handling...\n")
    
    async with DataManager(config) as dm:
        # Test symbols including NDX which has subscription issues
        test_symbols = ['SPX', 'NDX', 'VIX', 'SPY']
        
        for symbol in test_symbols:
            print(f"\n--- Testing {symbol} ---")
            try:
                data = await dm.get_market_data(symbol)
                print(f"✓ {symbol}: ${data['price']:.2f} from {data['source']}")
                
                if data['source'] == 'mock':
                    print(f"  (Using mock data due to subscription issues)")
                    
            except Exception as e:
                print(f"✗ {symbol}: Error - {e}")
        
        print("\n--- Second pass (should use cache/skip failed) ---")
        # Second pass should be faster as failed symbols are skipped
        for symbol in test_symbols:
            data = await dm.get_market_data(symbol)
            print(f"{symbol}: ${data['price']:.2f} from {data['source']}")
    
    print("\n✅ Test completed - connection remained stable despite NDX error!")

if __name__ == "__main__":
    asyncio.run(test_resilient_connection())
