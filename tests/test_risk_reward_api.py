import importlib
import os
import sys

from fastapi.testclient import TestClient

from tests.mocks.mock_provider import ScenarioMockProvider
from tests.utils.market_scenarios import normal_volatility


def create_client(monkeypatch):
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
            price = await self.provider.get_current_price(symbol)
            return {"price": price["last"], "volatility": 17.0, "source": "mock"}

    monkeypatch.setattr(api, "DataManager", FakeManager)
    monkeypatch.setattr(api.joblib, "load", lambda p: type("M", (), {"predict_proba": lambda self, X: [[0.4, 0.6]]})())

    client = TestClient(api.app)
    client.__enter__()
    return client, api


def test_risk_reward_endpoint(monkeypatch):
    client, api = create_client(monkeypatch)
    payload = {
        "symbol": "SPX",
        "strategy": "Butterfly",
        "strikes": [4800, 4850, 4900],
        "premium": 2.0,
        "action": "BUY",
    }
    resp = client.post("/calculate_risk_reward", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_reward_ratio"] > 0
    client.__exit__(None, None, None)
