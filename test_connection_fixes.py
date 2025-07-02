#!/usr/bin/env python3
"""
Test script to verify IBKR connection fixes
"""

import asyncio
import logging
from src.data_providers.standalone_provider import StandaloneDataProvider
from src.constants import DEFAULT_IB_PORT

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_connection():
    """Test the IBKR connection and data retrieval."""
    provider = StandaloneDataProvider(
        ib_host="127.0.0.1",
        ib_port=DEFAULT_IB_PORT,
        client_id=99
    )
    
    try:
        # Test 1: Connection
        logger.info("Test 1: Testing connection...")
        connected = await provider.connect()
        if connected:
            logger.info("✅ Connection successful")
        else:
            logger.error("❌ Connection failed")
            return
        
        # Test 2: Check connection status
        logger.info("\nTest 2: Checking connection status...")
        is_connected = await provider.is_connected()
        logger.info(f"Connection status: {'✅ Connected' if is_connected else '❌ Disconnected'}")
        
        # Test 3: Get current price for a symbol
        logger.info("\nTest 3: Getting current price for SPX...")
        try:
            price_data = await provider.get_current_price('SPX')
            logger.info(f"✅ SPX price: ${price_data['last']:.2f}")
            logger.info(f"   Bid: ${price_data['bid']:.2f} (size: {price_data['bid_size']})")
            logger.info(f"   Ask: ${price_data['ask']:.2f} (size: {price_data['ask_size']})")
        except Exception as e:
            logger.error(f"❌ Failed to get SPX price: {e}")
        
        # Test 4: Test with symbol that might not have market data subscription
        logger.info("\nTest 4: Testing market data subscription handling...")
        test_symbols = ['VIX', 'RUT', 'NDX']
        for symbol in test_symbols:
            try:
                price_data = await provider.get_current_price(symbol)
                logger.info(f"✅ {symbol} price: ${price_data['last']:.2f}")
            except Exception as e:
                if "market data subscription missing" in str(e).lower():
                    logger.warning(f"⚠️  {symbol}: Market data not subscribed (expected)")
                else:
                    logger.error(f"❌ {symbol}: Unexpected error - {e}")
        
        # Test 5: Connection persistence
        logger.info("\nTest 5: Testing connection persistence...")
        await asyncio.sleep(2)  # Wait 2 seconds
        is_still_connected = await provider.is_connected()
        logger.info(f"Connection after delay: {'✅ Still connected' if is_still_connected else '❌ Lost connection'}")
        
        # Test 6: Concurrent request handling
        logger.info("\nTest 6: Testing concurrent requests...")
        try:
            # Try to get multiple prices concurrently
            tasks = [
                provider.get_current_price('SPX'),
                provider.get_current_price('SPY'),
                provider.get_current_price('QQQ')
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                symbol = ['SPX', 'SPY', 'QQQ'][i]
                if isinstance(result, Exception):
                    logger.warning(f"⚠️  {symbol}: {result}")
                else:
                    logger.info(f"✅ {symbol}: ${result['last']:.2f}")
        except Exception as e:
            logger.error(f"❌ Concurrent request test failed: {e}")
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        
    finally:
        # Clean up
        logger.info("\nCleaning up...")
        await provider.disconnect()
        logger.info("✅ Disconnected")


async def test_reconnection():
    """Test reconnection after disconnect."""
    logger.info("\n" + "="*50)
    logger.info("Testing reconnection capability...")
    logger.info("="*50)
    
    provider = StandaloneDataProvider(
        ib_host="127.0.0.1",
        ib_port=DEFAULT_IB_PORT,
        client_id=99
    )
    
    try:
        # Initial connection
        logger.info("Connecting...")
        await provider.connect()
        
        # Get a price
        price1 = await provider.get_current_price('SPX')
        logger.info(f"✅ Initial SPX price: ${price1['last']:.2f}")
        
        # Disconnect
        logger.info("Disconnecting...")
        await provider.disconnect()
        
        # Try to get price after disconnect (should fail)
        logger.info("Attempting to get price after disconnect...")
        try:
            await provider.get_current_price('SPX')
            logger.error("❌ Should have failed but didn't")
        except Exception as e:
            logger.info(f"✅ Expected failure: {e}")
        
        # Reconnect
        logger.info("Reconnecting...")
        connected = await provider.connect()
        if connected:
            logger.info("✅ Reconnection successful")
            
            # Get price again
            price2 = await provider.get_current_price('SPX')
            logger.info(f"✅ SPX price after reconnect: ${price2['last']:.2f}")
        else:
            logger.error("❌ Reconnection failed")
            
    finally:
        await provider.disconnect()


if __name__ == "__main__":
    logger.info("Starting IBKR connection tests...")
    logger.info(f"Using IBKR Gateway on port {DEFAULT_IB_PORT}")
    
    # Run tests
    asyncio.run(test_connection())
    asyncio.run(test_reconnection())
    
    logger.info("\n✅ All tests completed!")
