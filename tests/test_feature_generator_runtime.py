import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.feature_engineering.real_time_features import RealTimeFeatureGenerator

class DummyProvider:
    async def connect(self) -> bool:
        return True
    async def disconnect(self):
        pass
    async def is_connected(self) -> bool:
        return True
    async def get_price_data(self, symbol: str, bars: int = 100, interval: str = "5 mins"):
        return [{"time": "2025-01-01T00:00:00", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 0}] * bars
    async def get_current_price(self, symbol: str):
        return {"last": 1}
    async def get_vix_data(self):
        return {"last": 15}

async def generate():
    path = Path("data/phase1_processed/feature_info.json")
    provider = DummyProvider()
    gen = RealTimeFeatureGenerator(provider, feature_info_path=str(path))
    feats, names = await gen.generate_features("SPX", {"strategy": "Butterfly", "premium": 1, "predicted_price": 1})
    return feats, names


def test_generated_feature_length():
    feats, names = asyncio.run(generate())
    with open("data/phase1_processed/feature_info.json") as f:
        info = json.load(f)
    assert len(feats) == info["n_features"]
    assert len(names) == info["n_features"]
