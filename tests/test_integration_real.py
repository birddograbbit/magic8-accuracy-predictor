import pytest
from fastapi.testclient import TestClient

from tests.mocks.mock_provider import ScenarioMockProvider
from tests.utils.market_scenarios import normal_volatility
import importlib
import os
import sys


def test_prediction_flow(monkeypatch):
    project_root = os.path.join(os.path.dirname(__file__), "..")
    sys.path.append(project_root)
    sys.path.append(os.path.join(project_root, "src"))
    api = importlib.import_module("src.prediction_api_realtime")

    class FakeManager:
        def __init__(self, cfg):
            self.provider = ScenarioMockProvider(normal_volatility())

        async def connect(self):
            await self.provider.connect()

        async def disconnect(self):
            await self.provider.disconnect()

        async def get_market_data(self, symbol):
            p = await self.provider.get_current_price(symbol)
            return {"price": p["last"], "volatility": 17.0, "source": "mock"}

        async def get_current_price(self, symbol):
            return await self.provider.get_current_price(symbol)

        async def get_price_data(self, symbol, bars=100, interval="5 mins"):
            return await self.provider.get_price_data(symbol, bars, interval)

        async def get_vix_data(self):
            return await self.provider.get_vix_data()

    monkeypatch.setattr(api, "DataManager", FakeManager)
    monkeypatch.setattr(api.joblib, "load", lambda p: type("M", (), {"predict_proba": lambda self, X: [[0.4, 0.6]]})())

    rtf = importlib.import_module("feature_engineering.real_time_features")
    monkeypatch.setattr(rtf, "datetime", rtf.datetime)

    client = TestClient(api.app)
    client.__enter__()

    payload = {
        "strategy": "Butterfly",
        "symbol": "SPX",
        "premium": 3.0,
        "predicted_price": 5850.0,
    }
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "win_probability" in data
    client.__exit__(None, None, None)

