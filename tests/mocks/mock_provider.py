import asyncio
import random
from datetime import datetime
from typing import Dict, List

from src.data_providers.base_provider import BaseDataProvider
from tests.utils.market_scenarios import MarketScenario, generate_bars, generate_vix_value


class ScenarioMockProvider(BaseDataProvider):
    """Mock provider that responds based on a MarketScenario."""

    def __init__(self, scenario: MarketScenario):
        self.scenario = scenario
        self.connected = False
        self.base_prices = {
            "SPX": 5900.0,
            "SPY": 590.0,
            "NDX": 20500.0,
            "QQQ": 500.0,
            "RUT": 2300.0,
            "XSP": 590.0,
            "AAPL": 230.0,
            "TSLA": 250.0,
            "VIX": 15.0,
        }

    async def connect(self) -> bool:
        await asyncio.sleep(0.01)
        self.connected = True
        return True

    async def disconnect(self):
        self.connected = False

    async def is_connected(self) -> bool:
        return self.connected

    async def get_current_price(self, symbol: str) -> Dict:
        if not self.connected:
            raise ConnectionError("provider not connected")
        base = self.base_prices.get(symbol, 100.0)
        price = base * (1 + random.gauss(self.scenario.trend, self.scenario.vix / 1000.0))
        return {
            "symbol": symbol,
            "last": price,
            "time": datetime.now().isoformat(),
        }

    async def get_price_data(self, symbol: str, bars: int = 100, interval: str = "5 mins") -> List[Dict]:
        if not self.connected:
            raise ConnectionError("provider not connected")
        base = self.base_prices.get(symbol, 100.0)
        return generate_bars(base, self.scenario, bars)

    async def get_vix_data(self) -> Dict:
        if not self.connected:
            raise ConnectionError("provider not connected")
        return generate_vix_value(self.scenario)

    async def get_option_chain(self, symbol: str, expiry: str, right: str | None = None) -> List[Dict]:
        return []


__all__ = ["ScenarioMockProvider"]

