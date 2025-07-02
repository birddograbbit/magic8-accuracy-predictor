"""
Simplified data manager using single IB connection.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np

from .ib_connection import ib_connection

logger = logging.getLogger(__name__)


class SimpleDataManager:
    """Simple data manager with IB connection and caching."""
    
    def __init__(self, config: dict):
        self.config = config
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(seconds=30)  # Short cache for real-time trading
        
        # IB connection config
        ib_config = config.get('ib', {})
        self.ib_host = ib_config.get('host', '127.0.0.1')
        self.ib_port = ib_config.get('port', 7497)
        self.ib_client_id = ib_config.get('client_id', 99)
        
    def connect(self) -> bool:
        """Connect to IB."""
        return ib_connection.connect(
            host=self.ib_host,
            port=self.ib_port,
            client_id=self.ib_client_id
        )
        
    def disconnect(self):
        """Disconnect from IB."""
        ib_connection.disconnect()
        
    def is_connected(self) -> bool:
        """Check if connected."""
        return ib_connection.is_connected()
        
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid."""
        if key not in self.cache:
            return False
        entry = self.cache[key]
        if 'timestamp' not in entry:
            return False
        age = datetime.now() - entry['timestamp']
        return age < self.cache_ttl
        
    def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get market data with caching."""
        cache_key = f"market_{symbol}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.debug(f"Using cached data for {symbol}")
            return self.cache[cache_key]['data']
            
        # Try to get live data
        try:
            price = ib_connection.get_current_price(symbol)
            
            # Try to calculate volatility from recent bars
            volatility = 0.20  # Default
            try:
                bars = ib_connection.get_historical_data(symbol, "1 D", "5 mins")
                if len(bars) > 2:
                    closes = [bar['close'] for bar in bars]
                    returns = []
                    for i in range(1, len(closes)):
                        if closes[i-1] > 0:
                            ret = (closes[i] - closes[i-1]) / closes[i-1]
                            returns.append(ret)
                    if returns:
                        # Annualized volatility (252 trading days, 78 5-min bars per day)
                        volatility = float(np.std(returns) * np.sqrt(252 * 78))
            except Exception as e:
                logger.debug(f"Could not calculate volatility for {symbol}: {e}")
                
            data = {
                'price': price,
                'volatility': volatility,
                'source': 'ibkr'
            }
            
            # Update cache
            self.cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now()
            }
            
            return data
            
        except Exception as e:
            logger.warning(f"Failed to get market data for {symbol}: {e}")
            
            # Return mock data as fallback
            return self._get_mock_data(symbol)
            
    def _get_mock_data(self, symbol: str) -> Dict[str, Any]:
        """Get mock data for testing."""
        mock_prices = {
            'SPX': 5850.0,
            'SPY': 585.0,
            'VIX': 15.0,
            'RUT': 2300.0,
            'QQQ': 500.0,
            'NDX': 20000.0,
            'XSP': 585.0,
            'AAPL': 220.0,
            'TSLA': 200.0
        }
        
        return {
            'price': mock_prices.get(symbol, 100.0),
            'volatility': 0.30 if symbol == 'VIX' else 0.20,
            'source': 'mock'
        }
