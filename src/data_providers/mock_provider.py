"""
Mock data provider for testing without external dependencies.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np

from .base_provider import BaseDataProvider


class MockDataProvider(BaseDataProvider):
    """
    Mock data provider for testing and development.
    Provides realistic-looking market data without external connections.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize mock data provider."""
        super().__init__(config)
        self.connected = False
        
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
            
        # Check cache
        cache_key = f"{symbol}_{interval}_{lookback_days}"
        if cache_key in self._historical_cache:
            return self._historical_cache[cache_key]
            
        base_price = self.base_prices.get(symbol, 100.0)
        
        # Calculate number of bars
        if interval == '5m':
            bars_per_day = 78  # 6.5 hours * 12 bars/hour
        elif interval == '1h':
            bars_per_day = 7
        elif interval == '1d':
            bars_per_day = 1
        else:
            bars_per_day = 78
            
        total_bars = bars_per_day * lookback_days
        
        # Generate historical data
        data = []
        current_time = datetime.now()
        current_price = base_price
        
        for i in range(total_bars):
            # Time calculation
            if interval == '5m':
                bar_time = current_time - timedelta(minutes=5 * i)
            elif interval == '1h':
                bar_time = current_time - timedelta(hours=i)
            elif interval == '1d':
                bar_time = current_time - timedelta(days=i)
            else:
                bar_time = current_time - timedelta(minutes=5 * i)
                
            # Skip non-market hours for intraday
            if interval in ['5m', '1h']:
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
                'timestamp': bar_time,
                'open': open_price,
                'high': high,
                'low': low,
                'close': current_price,
                'volume': random.randint(100000, 1000000)
            }
            
            data.append(bar)
            
        # Reverse to have oldest first
        data.reverse()
        
        # Cache the result
        self._historical_cache[cache_key] = data
        
        return data
        
    async def get_option_chain(
        self,
        symbol: str,
        expiry: str
    ) -> Optional[Dict[str, Any]]:
        """Generate mock option chain."""
        if not self.connected:
            return None
            
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
        calls = []
        puts = []
        
        for strike in strikes:
            # Simple Black-Scholes approximation for mock data
            moneyness = (base_price - strike) / base_price
            time_to_expiry = 1 / 365  # Assume 1 day for 0DTE
            
            # Call option
            call_price = max(0.01, base_price - strike + random.uniform(0.1, 0.5))
            call_iv = 0.15 + abs(moneyness) * 0.1 + random.uniform(-0.02, 0.02)
            
            calls.append({
                'strike': strike,
                'bid': call_price - 0.05,
                'ask': call_price + 0.05,
                'last': call_price,
                'iv': call_iv,
                'volume': random.randint(0, 1000),
                'open_interest': random.randint(0, 5000)
            })
            
            # Put option
            put_price = max(0.01, strike - base_price + random.uniform(0.1, 0.5))
            put_iv = 0.15 + abs(moneyness) * 0.1 + random.uniform(-0.02, 0.02)
            
            puts.append({
                'strike': strike,
                'bid': put_price - 0.05,
                'ask': put_price + 0.05,
                'last': put_price,
                'iv': put_iv,
                'volume': random.randint(0, 1000),
                'open_interest': random.randint(0, 5000)
            })
            
        return {
            'symbol': symbol,
            'expiry': expiry,
            'underlying_price': base_price,
            'calls': calls,
            'puts': puts
        }
        
    async def get_vix_data(self) -> Optional[Dict[str, Any]]:
        """Get mock VIX data."""
        return await self.get_market_data('VIX')


# Add to __init__.py exports
__all__ = ['MockDataProvider']
