"""
Data Manager for magic8-accuracy-predictor
Handles data source selection with caching and fallback to IBKR.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

import aiohttp
import numpy as np

from .data_providers.standalone_provider import StandaloneDataProvider
from src.constants import DEFAULT_IB_PORT

logger = logging.getLogger(__name__)


class DataManager:
    """Manage market data from companion API with IBKR fallback."""

    def __init__(self, config: dict):
        self.config = config
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(minutes=5)
        self.companion_url = config.get("companion", {}).get("base_url", "http://localhost:8765")
        self.use_standalone = config.get("standalone", {}).get("enabled", True)
        self._ib_provider: Optional[StandaloneDataProvider] = None
        self._companion_session: Optional[aiohttp.ClientSession] = None
        self._subscription_failures: Dict[str, bool] = {}  # Track subscription failures

    async def __aenter__(self):
        """Initialize connections on context manager entry."""
        # Create companion session
        self._companion_session = aiohttp.ClientSession()
        
        # Initialize IB provider if enabled
        if self.use_standalone:
            conf = self.config.get("standalone", {})
            self._ib_provider = StandaloneDataProvider(
                ib_host=conf.get("ib_host", "127.0.0.1"),
                ib_port=conf.get("ib_port", DEFAULT_IB_PORT),
                client_id=conf.get("client_id", 99),
            )
            await self._ib_provider.connect()
        
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup connections on context manager exit."""
        # Close companion session
        if self._companion_session:
            await self._companion_session.close()
            self._companion_session = None
            
        # Disconnect IB provider
        if self._ib_provider:
            try:
                await self._ib_provider.disconnect()
                logger.info("IB provider disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting IB provider: {e}")
            finally:
                self._ib_provider = None


    def _is_cache_valid(self, key: str) -> bool:
        if key not in self.cache:
            return False
        ts = self.cache[key].get("timestamp")
        if not ts:
            return False
        return datetime.now() - ts < self.cache_ttl

    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        key = f"market_{symbol}"
        if self._is_cache_valid(key):
            logger.debug("Using cached data for %s", symbol)
            return self.cache[key]["data"]

        # Skip IBKR if we know this symbol has subscription issues
        skip_ibkr = self._subscription_failures.get(symbol, False)

        # try companion
        try:
            data = await self._fetch_from_companion(symbol)
            self._update_cache(key, data)
            return data
        except Exception as e:
            logger.debug("Companion fetch failed for %s: %s", symbol, e)

        if self.use_standalone and not skip_ibkr:
            try:
                data = await self._fetch_from_ibkr(symbol)
                self._update_cache(key, data)
                # Clear subscription failure flag on success
                self._subscription_failures[symbol] = False
                return data
            except Exception as e:
                error_msg = str(e)
                # Check if it's a subscription error
                if self._is_subscription_error(error_msg):
                    logger.warning(f"Market data subscription missing for {symbol}, will use mock data")
                    self._subscription_failures[symbol] = True
                else:
                    logger.warning("IBKR fetch failed for %s: %s", symbol, e)

        return self._get_mock_data(symbol)

    def _is_subscription_error(self, error_msg: str) -> bool:
        """Check if the error is due to missing market data subscription."""
        subscription_errors = [
            "market data is not subscribed",
            "error 354",
            "requested market data is not subscribed",
            "delayed market data is available"
        ]
        error_lower = error_msg.lower()
        return any(err in error_lower for err in subscription_errors)

    async def _fetch_from_companion(self, symbol: str) -> Dict[str, Any]:
        if not self._companion_session:
            raise RuntimeError("Session not initialized")
        url = f"{self.companion_url}/market/{symbol}"
        async with self._companion_session.get(url, timeout=5) as resp:
            if resp.status != 200:
                raise Exception(f"API returned {resp.status}")
            data = await resp.json()
            return {
                "price": data.get("price", 0.0),
                "volatility": data.get("volatility", 0.20),
                "source": "companion",
            }

    async def _fetch_from_ibkr(self, symbol: str) -> Dict[str, Any]:
        """Fetch data from IBKR, ensuring connection persists."""
        # Ensure provider is initialized and connected
        if not self._ib_provider:
            conf = self.config.get("standalone", {})
            self._ib_provider = StandaloneDataProvider(
                ib_host=conf.get("ib_host", "127.0.0.1"),
                ib_port=conf.get("ib_port", DEFAULT_IB_PORT),
                client_id=conf.get("client_id", 99),
            )
        if not await self._ib_provider.is_connected():
            await self._ib_provider.connect()

        try:
            price_data = await self._ib_provider.get_current_price(symbol)
            volatility = 0.20
            
            # Only try to get volatility if we got a valid price
            if price_data.get("last", 0) > 0:
                try:
                    bars = await self._ib_provider.get_price_data(symbol, bars=20, interval="5 mins")
                    if bars:
                        closes = [bar["close"] for bar in bars]
                        if len(closes) > 1:
                            rets = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]
                            volatility = float(np.std(rets) * np.sqrt(252 * 78))
                except Exception as e:
                    logger.debug("Volatility calc failed: %s", e)

            return {
                "price": price_data.get("last", 0.0),
                "volatility": volatility,
                "source": "ibkr",
            }
        except Exception as e:
            # Check if connection was lost
            if not await self._ib_provider.is_connected():
                logger.warning("IB connection lost during data fetch")
            # Re-raise with original error for proper handling upstream
            raise e

    def _get_mock_data(self, symbol: str) -> Dict[str, Any]:
        mock_prices = {
            "SPX": 5850.0,
            "VIX": 15.0,
            "SPY": 585.0,
            "RUT": 2300.0,
            "QQQ": 500.0,
            "NDX": 20000.0,
            "AAPL": 220.0,
            "TSLA": 200.0,
        }
        return {
            "price": mock_prices.get(symbol, 100.0),
            "volatility": 0.30 if symbol == "VIX" else 0.20,
            "source": "mock",
        }

    def _update_cache(self, key: str, data: Dict[str, Any]):
        self.cache[key] = {"data": data, "timestamp": datetime.now()}
