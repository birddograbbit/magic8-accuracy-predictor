import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import types
base_module = types.ModuleType('data_providers.base_provider')
class BaseDataProvider:
    async def connect(self) -> bool:
        return True
    async def disconnect(self):
        pass
    async def is_connected(self) -> bool:
        return True
base_module.BaseDataProvider = BaseDataProvider
sys.modules['data_providers'] = types.ModuleType('data_providers')
sys.modules['data_providers.base_provider'] = base_module

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

async def generate(order=None):
    path = Path("data/phase1_processed/feature_info.json")
    provider = DummyProvider()
    gen = RealTimeFeatureGenerator(provider, feature_info_path=str(path))
    order = order or {"strategy": "Butterfly", "premium": 1, "predicted_price": 1}
    feats, names = await gen.generate_features("SPX", order)
    return feats, names


def test_generated_feature_length():
    feats, names = asyncio.run(generate())
    import joblib
    order_path = Path("models/individual/SPX_trades_features.pkl")
    expected = len(joblib.load(order_path)) if order_path.exists() else 0
    assert len(feats) == expected
    assert len(names) == expected

def test_delta_features_present():
    order = {
        "strategy": "Butterfly",
        "premium": 1,
        "predicted_price": 5850,
        "price": 5845,
        "short_term": 5850,
        "long_term": 5860,
    }
    feats, names = asyncio.run(generate(order))
    delta_features = [
        "short_term",
        "long_term",
        "has_delta_data",
        "short_long_spread",
        "short_long_ratio",
        "price_vs_short",
        "price_vs_long",
        "predicted_vs_short",
        "predicted_vs_long",
        "delta_convergence",
        "predictions_aligned",
    ]
    for f in delta_features:
        assert f in names


class AltVIXProvider(DummyProvider):
    async def get_vix_data(self):
        return {"price": 16}


class AltPriceProvider(DummyProvider):
    async def get_current_price(self, symbol: str):
        return {"price": 1}


def test_vix_key_fallback():
    path = Path("data/phase1_processed/feature_info.json")
    provider = AltVIXProvider()
    gen = RealTimeFeatureGenerator(provider, feature_info_path=str(path))
    feats, names = asyncio.run(gen.generate_features("SPX", {"strategy": "Butterfly", "premium": 1, "predicted_price": 1}))
    assert "vix" in names


def test_price_key_fallback():
    path = Path("data/phase1_processed/feature_info.json")
    provider = AltPriceProvider()
    gen = RealTimeFeatureGenerator(provider, feature_info_path=str(path))
    feats, names = asyncio.run(gen.generate_features("SPX", {"strategy": "Butterfly", "premium": 1, "predicted_price": 1}))
    import joblib
    order_path = Path("models/individual/SPX_trades_features.pkl")
    expected = len(joblib.load(order_path)) if order_path.exists() else 0
    assert len(feats) == expected
    assert f"SPX_close" in names

