"""
Mock data provider for testing without external dependencies.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np
import logging

from .base_provider import BaseDataProvider


class MockDataProvider(BaseDataProvider):
    """
    Mock data provider for testing and development.
    Provides realistic-looking market data without external connections.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize mock data provider."""
        self.config = config or {}
        self.connected = False
        self.logger = logging.getLogger(__name__)
        
        # Base prices for symbols
        self.base_prices = {
            'SPX': 5900.0,
            'SPY': 590.0,
            'NDX': 20500.0,
            'QQQ': 500.0,
            'RUT': 2300.0,
            'XSP': 590.0,
            'AAPL': 230.0,
            'TSLA': 250.0,
            'VIX': 15.0
        }
        
        # Historical data cache
        self._historical_cache = {}
        
    async def connect(self) -> bool:
        """Simulate connection."""
        await asyncio.sleep(0.1)  # Simulate connection delay
        self.connected = True
        self.logger.info("MockDataProvider connected")
        return True
        
    async def disconnect(self):
        """Simulate disconnection."""
        self.connected = False
        self.logger.info("MockDataProvider disconnected")
        
    async def is_connected(self) -> bool:
        """Check if provider is connected."""
        return self.connected
        
    async def get_current_price(self, symbol: str) -> Dict:
        """
        Get current price snapshot for a symbol.
        
        Returns dictionary with current price data as specified by base class.
        """
        if not self.connected:
            raise ConnectionError("MockDataProvider not connected")
            
        base_price = self.base_prices.get(symbol, 100.0)
        
        # Add some random variation
        variation = random.uniform(-0.01, 0.01)  # ±1%
        price = base_price * (1 + variation)
        
        # Generate bid/ask spread
        spread = random.uniform(0.01, 0.05)
        bid = price - spread / 2
        ask = price + spread / 2
        
        return {
            'symbol': symbol,
            'last': price,
            'bid': bid,
            'ask': ask,
            'bid_size': random.randint(10, 100),
            'ask_size': random.randint(10, 100),
            'time': datetime.now().isoformat()
        }
        
    async def get_price_data(
        self,
        symbol: str,
        bars: int = 100,
        interval: str = "5 mins"
    ) -> List[Dict]:
        """
        Get historical price bars for a symbol.
        
        Returns list of price bars with OHLCV data as specified by base class.
        """
        if not self.connected:
            raise ConnectionError("MockDataProvider not connected")
            
        base_price = self.base_prices.get(symbol, 100.0)
        
        # Parse interval
        if "min" in interval:
            minutes = int(interval.split()[0])
            time_delta = timedelta(minutes=minutes)
        elif "hour" in interval:
            hours = int(interval.split()[0])
            time_delta = timedelta(hours=hours)
        else:
            time_delta = timedelta(minutes=5)
            
        # Generate historical data
        data = []
        current_time = datetime.now()
        current_price = base_price
        
        for i in range(bars):
            # Calculate bar time
            bar_time = current_time - (time_delta * i)
            
            # Skip non-market hours for intraday
            if "min" in interval or "hour" in interval:
                if bar_time.hour < 9 or bar_time.hour >= 16:
                    continue
                    
            # Price simulation with trend and volatility
            trend = 0.0001 * (i % 20 - 10)  # Cyclical trend
            volatility = 0.002 * abs(np.sin(i * 0.1))  # Varying volatility
            change = random.gauss(trend, volatility)
            
            current_price *= (1 + change)
            
            # OHLC calculation
            high = current_price * (1 + random.uniform(0, 0.002))
            low = current_price * (1 - random.uniform(0, 0.002))
            open_price = current_price * (1 + random.uniform(-0.001, 0.001))
            
            bar = {
                'time': bar_time.isoformat(),
                'open': open_price,
                'high': high,
                'low': low,
                'close': current_price,
                'volume': random.randint(100000, 1000000)
            }
            
            data.append(bar)
            
        # Reverse to have oldest first
        data.reverse()
        
        return data
        
    async def health_check(self) -> Dict[str, Any]:
        """Return mock health status."""
        return {
            'status': 'healthy' if self.connected else 'disconnected',
            'provider': 'mock',
            'timestamp': datetime.now().isoformat()
        }
        
    async def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Generate mock market data."""
        if not self.connected:
            return None
            
        base_price = self.base_prices.get(symbol, 100.0)
        
        # Add some random variation
        variation = random.uniform(-0.01, 0.01)  # ±1%
        price = base_price * (1 + variation)
        
        # Generate other market data
        bid = price - random.uniform(0.01, 0.05)
        ask = price + random.uniform(0.01, 0.05)
        
        return {
            'symbol': symbol,
            'price': price,
            'bid': bid,
            'ask': ask,
            'volume': random.randint(1000000, 10000000),
            'open': base_price,
            'high': price * 1.002,
            'low': price * 0.998,
            'close': price,
            'timestamp': datetime.now()
        }
        
    async def get_historical_data(
        self,
        symbol: str,
        interval: str = '5m',
        lookback_days: int = 1
    ) -> Optional[List[Dict[str, Any]]]:
        """Generate mock historical data."""
        if not self.connected:
            return None
            
        # Use get_price_data for consistency
        if interval == '5m':
            bars = lookback_days * 78  # 6.5 hours * 12 bars/hour
            return await self.get_price_data(symbol, bars, "5 mins")
        elif interval == '1h':
            bars = lookback_days * 7
            return await self.get_price_data(symbol, bars, "1 hour")
        else:
            bars = lookback_days * 78
            return await self.get_price_data(symbol, bars, "5 mins")
            
    async def get_option_chain(
        self,
        symbol: str,
        expiry: str,
        right: Optional[str] = None
    ) -> List[Dict]:
        """Generate mock option chain."""
        if not self.connected:
            raise ConnectionError("MockDataProvider not connected")
            
        base_price = self.base_prices.get(symbol, 100.0)
        
        # Generate strikes around current price
        strikes = []
        for i in range(-10, 11):
            if symbol in ['SPX', 'NDX']:
                strike = round(base_price + i * 5, 0)
            else:
                strike = round(base_price + i * 1, 0)
            strikes.append(strike)
            
        # Generate option data
        options = []
        
        for strike in strikes:
            # Simple Black-Scholes approximation for mock data
            moneyness = (base_price - strike) / base_price
            time_to_expiry = 1 / 365  # Assume 1 day for 0DTE
            
            # Generate both calls and puts unless filtered
            rights_to_generate = [right] if right else ['CALL', 'PUT']
            
            for opt_right in rights_to_generate:
                if opt_right == 'CALL':
                    # Call option
                    price = max(0.01, base_price - strike + random.uniform(0.1, 0.5))
                    iv = 0.15 + abs(moneyness) * 0.1 + random.uniform(-0.02, 0.02)
                    delta = 0.5 + moneyness * 2  # Simplified
                else:
                    # Put option
                    price = max(0.01, strike - base_price + random.uniform(0.1, 0.5))
                    iv = 0.15 + abs(moneyness) * 0.1 + random.uniform(-0.02, 0.02)
                    delta = -0.5 + moneyness * 2  # Simplified
                
                options.append({
                    'symbol': symbol,
                    'expiry': expiry,
                    'strike': strike,
                    'right': opt_right,
                    'bid': price - 0.05,
                    'ask': price + 0.05,
                    'last': price,
                    'volume': random.randint(0, 1000),
                    'open_interest': random.randint(0, 5000),
                    'implied_volatility': iv,
                    'delta': max(-1, min(1, delta)),
                    'gamma': 0.01 * (1 - abs(moneyness)),
                    'theta': -0.5 - random.uniform(0, 0.5),
                    'vega': 0.5 + random.uniform(0, 0.3)
                })
                
        return options
        
    async def get_vix_data(self) -> Dict:
        """Get mock VIX data."""
        if not self.connected:
            raise ConnectionError("MockDataProvider not connected")
            
        base_vix = self.base_prices.get('VIX', 15.0)
        current_vix = base_vix + random.uniform(-2, 2)
        
        return {
            'last': current_vix,
            'change': random.uniform(-1, 1),
            'change_pct': random.uniform(-5, 5),
            'high': current_vix + random.uniform(0, 1),
            'low': current_vix - random.uniform(0, 1),
            'time': datetime.now().isoformat()
        }


# Add to __init__.py exports
__all__ = ['MockDataProvider']
