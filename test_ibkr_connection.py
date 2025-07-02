"""Test IBKR connection for magic8-accuracy-predictor"""

import asyncio
import logging

from src.data_manager import DataManager

logging.basicConfig(level=logging.INFO)

async def test_connection():
    config = {
        'companion': {
            'enabled': True,
            'base_url': 'http://localhost:8765'
        },
        'standalone': {
            'enabled': True,
            'ib_host': '127.0.0.1',
            'ib_port': 7497,
            'client_id': 99
        }
    }

    async with DataManager(config) as dm:
        for symbol in ['SPX', 'VIX', 'SPY']:
            data = await dm.get_market_data(symbol)
            print(f"{symbol}: ${data['price']:.2f} (vol: {data['volatility']:.2%}) from {data['source']}")

if __name__ == "__main__":
    asyncio.run(test_connection())
