#!/usr/bin/env python3
"""
Test script to verify IBKR connection and index contract fixes.
Run this to ensure the StandaloneDataProvider works correctly with all indices.
"""

import asyncio
import logging
from src.data_providers.standalone_provider import StandaloneDataProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_index_contracts():
    """Test all index contracts with correct exchanges."""
    # Initialize provider
    provider = StandaloneDataProvider(
        ib_host="127.0.0.1",
        ib_port=7497,
        client_id=99
    )
    
    # Connect
    logger.info("Connecting to IBKR...")
    connected = await provider.connect()
    if not connected:
        logger.error("Failed to connect to IBKR")
        return
    
    # Test each index
    indices = ['SPX', 'VIX', 'RUT', 'NDX', 'XSP']
    
    logger.info("Testing index contracts...")
    for symbol in indices:
        logger.info(f"\n--- Testing {symbol} ---")
        
        # Get current price
        price_data = await provider.get_current_price(symbol)
        logger.info(f"{symbol} current price: ${price_data['last']:.2f}")
        logger.info(f"  Bid: ${price_data['bid']:.2f} (size: {price_data['bid_size']})")
        logger.info(f"  Ask: ${price_data['ask']:.2f} (size: {price_data['ask_size']})")
        
        # Brief pause between requests
        await asyncio.sleep(0.5)
    
    # Test a stock for comparison
    logger.info("\n--- Testing SPY (Stock) ---")
    spy_data = await provider.get_current_price('SPY')
    logger.info(f"SPY current price: ${spy_data['last']:.2f}")
    
    # Disconnect
    await provider.disconnect()
    logger.info("\nTest completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_index_contracts())
