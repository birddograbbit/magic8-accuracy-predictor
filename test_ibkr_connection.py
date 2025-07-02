#!/usr/bin/env python3
"""Test script to verify IBKR connection and data fetching works properly."""

import asyncio
import logging
from data_providers.standalone_provider import StandaloneDataProvider

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_ibkr_connection():
    """Test IBKR connection and data fetching."""
    provider = StandaloneDataProvider(
        ib_host="127.0.0.1",
        ib_port=7497,
        client_id=99
    )
    
    try:
        # Test connection
        logger.info("Testing IBKR connection...")
        connected = await provider.connect()
        if not connected:
            logger.error("Failed to connect to IBKR")
            return
        
        logger.info("✓ Connected successfully")
        
        # Test symbols
        test_symbols = ['SPX', 'SPY', 'VIX', 'NDX', 'RUT', 'QQQ', 'AAPL']
        
        for symbol in test_symbols:
            try:
                logger.info(f"\nTesting {symbol}...")
                
                # Get current price
                price_data = await provider.get_current_price(symbol)
                logger.info(f"✓ {symbol} current price: ${price_data['last']:.2f}")
                
                # Get historical data
                hist_data = await provider.get_price_data(symbol, bars=10, interval="5 mins")
                if hist_data:
                    logger.info(f"✓ {symbol} historical data: {len(hist_data)} bars")
                    logger.info(f"  Last bar: {hist_data[-1]['time']} - Close: ${hist_data[-1]['close']:.2f}")
                else:
                    logger.warning(f"✗ No historical data for {symbol}")
                    
            except Exception as e:
                logger.error(f"✗ Error with {symbol}: {e}")
        
        # Show failed symbols
        if provider._failed_symbols:
            logger.warning(f"\nSymbols with subscription issues: {provider._failed_symbols}")
            logger.info("These symbols will use mock data in the prediction API")
        
    finally:
        # Test disconnect
        logger.info("\nTesting disconnect...")
        await provider.disconnect()
        logger.info("✓ Disconnected successfully")

if __name__ == "__main__":
    asyncio.run(test_ibkr_connection())
