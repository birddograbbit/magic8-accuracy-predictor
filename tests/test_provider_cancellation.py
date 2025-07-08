import pytest

from src.data_providers.standalone_provider import StandaloneDataProvider


class FakeTicker:
    def __init__(self):
        self.last = 100.0
        self.close = None
        self.bid = 99.5
        self.ask = 100.5
        self.bidSize = 1
        self.askSize = 1


class FakeIB:
    def __init__(self):
        self.cancel_called = False

    def isConnected(self):
        return True

    def reqMktData(self, contract, *args):
        return FakeTicker()

    def cancelMktData(self, ticker):
        self.cancel_called = True
        raise Exception("No reqId found")


@pytest.mark.asyncio
async def test_cancel_mkt_data_handled():
    provider = StandaloneDataProvider()
    provider.ib = FakeIB()
    result = await provider.get_current_price("SPX")
    assert result["symbol"] == "SPX"
    assert provider.ib.cancel_called

