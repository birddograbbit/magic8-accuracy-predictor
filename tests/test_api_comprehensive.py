from datetime import datetime

import numpy as np
import pytest
from fastapi.testclient import TestClient


# Import modules after patching
from tests.mocks.mock_provider import ScenarioMockProvider
from tests.utils import market_scenarios as ms


@pytest.fixture(params=[
    ms.low_volatility(),
    ms.normal_volatility(),
    ms.elevated_volatility(),
    ms.high_volatility(),
])
def scenario(request):
    return request.param


def _get_fixed_datetime(hour: int, minute: int):
    class _Fixed(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2025, 7, 1, hour, minute)
    return _Fixed


def create_client(monkeypatch, scenario: ms.MarketScenario, hour: int, minute: int):
    import importlib
    import sys
    import os
    project_root = os.path.join(os.path.dirname(__file__), "..")
    sys.path.append(project_root)
    sys.path.append(os.path.join(project_root, "src"))
    api = importlib.import_module("src.prediction_api_realtime")

    class FakeManager:
        def __init__(self, cfg):
            self.provider = ScenarioMockProvider(scenario)

        async def connect(self):
            await self.provider.connect()

        async def disconnect(self):
            await self.provider.disconnect()

        async def get_market_data(self, symbol):
            price = await self.provider.get_current_price(symbol)
            return {"price": price["last"], "volatility": scenario.vix, "source": "mock"}

        async def get_current_price(self, symbol):
            price = await self.provider.get_current_price(symbol)
            return price

        async def get_price_data(self, symbol, bars=100, interval="5 mins"):
            return await self.provider.get_price_data(symbol, bars, interval)

        async def get_vix_data(self):
            return await self.provider.get_vix_data()

    # Patch components
    monkeypatch.setattr(api, "DataManager", FakeManager)

    class SimpleModel:
        def predict_proba(self, X):
            # Use vix from features
            names = api.feature_gen.feature_order
            idx = names.index("vix") if "vix" in names else 0
            vix = X[0][idx]
            prob = 1 / (1 + np.exp(-(vix - 20) / 5))
            # Cap probabilities to stay within reasonable bounds
            prob = min(max(prob, 0.05), 0.95)
            return np.array([[1 - prob, prob]])

    monkeypatch.setattr(api.joblib, "load", lambda p: SimpleModel())

    # Patch datetime for temporal features
    import importlib
    rtf = importlib.import_module("feature_engineering.real_time_features")
    monkeypatch.setattr(rtf, "datetime", _get_fixed_datetime(hour, minute))

    client = TestClient(api.app)
    client.__enter__()
    return client, api


time_mapping = {
    "open": (9, 35),
    "midday": (12, 0),
    "close": (15, 55),
    "after-hours": (18, 0),
}

strategies = ["Butterfly", "Iron Condor", "Vertical", "Sonar"]
symbols = ["SPX", "AAPL"]


@pytest.mark.parametrize("time_label", list(time_mapping.keys()))
@pytest.mark.parametrize("strategy", strategies)
@pytest.mark.parametrize("symbol", symbols)
def test_prediction_ranges(monkeypatch, scenario, time_label, strategy, symbol):
    hour, minute = time_mapping[time_label]
    client, api = create_client(monkeypatch, scenario, hour, minute)
    payload = {
        "strategy": strategy,
        "symbol": symbol,
        "premium": 5.0,
        "predicted_price": 5850.0,
    }
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert 0.05 <= data["win_probability"] <= 0.95
    assert data["n_features"] == 74
    client.__exit__(None, None, None)


@pytest.mark.parametrize("premium", [0.1, 50.0])
def test_edge_premiums(monkeypatch, premium):
    scenario = ms.normal_volatility()
    client, api = create_client(monkeypatch, scenario, *time_mapping["midday"])
    payload = {
        "strategy": "Butterfly",
        "symbol": "SPX",
        "premium": premium,
        "predicted_price": 5850.0,
    }
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["n_features"] == 74
    client.__exit__(None, None, None)

