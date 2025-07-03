from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict
import random


@dataclass
class MarketScenario:
    """Representation of a test market condition."""

    vix: float
    trend: float = 0.0
    time_of_day: str = "midday"


def low_volatility() -> MarketScenario:
    return MarketScenario(vix=12.0, trend=0.0005)


def normal_volatility() -> MarketScenario:
    return MarketScenario(vix=17.0, trend=0.0007)


def elevated_volatility() -> MarketScenario:
    return MarketScenario(vix=25.0, trend=0.001)


def high_volatility() -> MarketScenario:
    return MarketScenario(vix=35.0, trend=0.002)


SCENARIO_FUNCS = {
    "low": low_volatility,
    "normal": normal_volatility,
    "elevated": elevated_volatility,
    "high": high_volatility,
}


def generate_bars(base_price: float, scenario: MarketScenario, bars: int = 30) -> List[Dict]:
    """Generate simple OHLCV bars for a scenario."""
    data = []
    current = base_price
    now = datetime.now()
    for i in range(bars):
        current *= 1 + random.gauss(scenario.trend, scenario.vix / 1000.0)
        bar_time = now - timedelta(minutes=5 * (bars - i))
        data.append(
            {
                "time": bar_time.isoformat(),
                "open": current * random.uniform(0.999, 1.001),
                "high": current * random.uniform(1.0, 1.003),
                "low": current * random.uniform(0.997, 1.0),
                "close": current,
                "volume": random.randint(100000, 200000),
            }
        )
    return data


def generate_vix_value(scenario: MarketScenario) -> Dict:
    """Return current VIX data for the scenario."""
    return {
        "last": scenario.vix,
        "time": datetime.now().isoformat(),
    }


__all__ = [
    "MarketScenario",
    "low_volatility",
    "normal_volatility",
    "elevated_volatility",
    "high_volatility",
    "generate_bars",
    "generate_vix_value",
]

