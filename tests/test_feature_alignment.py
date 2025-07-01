import json
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import types

base_module = types.ModuleType('src.data_providers.base_provider')

class BaseDataProvider:
    async def connect(self) -> bool:
        return True

    async def disconnect(self):
        pass

    async def is_connected(self) -> bool:
        return True

base_module.BaseDataProvider = BaseDataProvider
sys.modules['src.data_providers'] = types.ModuleType('src.data_providers')
sys.modules['src.data_providers.base_provider'] = base_module

from src.feature_engineering.real_time_features import RealTimeFeatureGenerator

class DummyProvider:
    async def connect(self) -> bool:
        return True

    async def disconnect(self):
        pass

    async def is_connected(self) -> bool:
        return True

    async def get_price_data(self, symbol: str, bars: int = 100):
        return []

    async def get_current_price(self, symbol: str):
        return {"last": 0}

    async def get_vix_data(self):
        return {"last": 0}

    async def get_price_snapshot(self, symbol: str):
        return {}


def test_feature_order_matches_model():
    path = Path("data/phase1_processed/feature_info.json")
    info = json.loads(path.read_text())
    provider = DummyProvider()
    gen = RealTimeFeatureGenerator(provider, feature_info_path=str(path))
    assert len(gen.feature_order) == info["n_features"]
