import importlib
import os
import sys
from fastapi.testclient import TestClient

from tests.mocks.mock_provider import ScenarioMockProvider
from tests.utils.market_scenarios import normal_volatility


def create_client(monkeypatch, market_counter=None):
    project_root = os.path.join(os.path.dirname(__file__), "..")
    sys.path.append(project_root)
    sys.path.append(os.path.join(project_root, "src"))
    import types
    base_mod = types.ModuleType('data_providers.standalone_provider')
    base_mod.StandaloneDataProvider = object
    sys.modules['data_providers'] = types.ModuleType('data_providers')
    sys.modules['data_providers.standalone_provider'] = base_mod
    api = importlib.import_module("src.prediction_api_realtime")

    class FakeManager:
        def __init__(self, cfg):
            self.provider = ScenarioMockProvider(normal_volatility())

        async def connect(self):
            await self.provider.connect()

        async def disconnect(self):
            await self.provider.disconnect()

        async def get_market_data(self, symbol):
            if market_counter is not None:
                market_counter["count"] += 1
            price = await self.provider.get_current_price(symbol)
            return {"price": price["last"], "volatility": 17.0, "source": "mock"}

    monkeypatch.setattr(api, "DataManager", FakeManager)
    monkeypatch.setattr(api.joblib, "load", lambda p: type("M", (), {"predict_proba": lambda self, X: [[0.4, 0.6]]})())

    call_counter = {"count": 0}

    class FakeFeatureGen:
        feature_order = ["a", "b"]

        async def generate_features(self, symbol, order):
            call_counter["count"] += 1
            return [0.1, 0.2], ["a", "b"]

    monkeypatch.setattr(api, "RealTimeFeatureGenerator", lambda *a, **k: FakeFeatureGen())

    client = TestClient(api.app)
    client.__enter__()
    return client, api, call_counter


def test_batch_prediction_caching(monkeypatch):
    client, api, counter = create_client(monkeypatch)

    trade = {"strategy": "Butterfly", "symbol": "SPX", "premium": 1.0, "predicted_price": 5850}

    resp = client.post("/predict/batch", json={"requests": [trade, trade]})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["predictions"]) == 2

    resp = client.post("/predict/batch", json={"requests": [trade]})
    assert resp.status_code == 200
    assert counter["count"] == 1

    client.__exit__(None, None, None)


def test_share_market_data(monkeypatch):
    market_counter = {"count": 0}
    client, api, _ = create_client(monkeypatch, market_counter)

    trade = {"strategy": "Butterfly", "symbol": "SPX", "premium": 1.0, "predicted_price": 5850}

    resp = client.post("/predict/batch", json={"requests": [trade, trade], "share_market_data": True})
    assert resp.status_code == 200
    assert market_counter["count"] == 1

    client.__exit__(None, None, None)

