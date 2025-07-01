"""
Base interface for market data providers.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class BaseDataProvider(ABC):
    """
    Abstract base class for market data providers.
    
    All data providers must implement this interface to ensure
    compatibility with the feature generation pipeline.
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to data source.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from data source."""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if provider is connected and ready."""
        pass
    
    @abstractmethod
    async def get_price_data(
        self,
        symbol: str,
        bars: int = 100,
        interval: str = "5 mins"
    ) -> List[Dict]:
        """
        Get historical price bars for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'SPX', 'SPY')
            bars: Number of bars to retrieve
            interval: Bar size (e.g., '5 mins', '1 hour')
            
        Returns:
            List of price bars with OHLCV data
            
        Example return:
        [
            {
                'time': '2025-07-01T10:00:00',
                'open': 5900.50,
                'high': 5905.25,
                'low': 5899.75,
                'close': 5903.00,
                'volume': 150000
            },
            ...
        ]
        """
        pass
    
    @abstractmethod
    async def get_current_price(self, symbol: str) -> Dict:
        """
        Get current price snapshot for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with current price data
            
        Example return:
        {
            'symbol': 'SPX',
            'last': 5903.00,
            'bid': 5902.75,
            'ask': 5903.25,
            'bid_size': 10,
            'ask_size': 15,
            'time': '2025-07-01T10:05:30'
        }
        """
        pass
    
    @abstractmethod
    async def get_vix_data(self) -> Dict:
        """
        Get current VIX data.
        
        Returns:
            Dictionary with VIX information
            
        Example return:
        {
            'last': 13.45,
            'change': -0.32,
            'change_pct': -2.32,
            'high': 14.20,
            'low': 13.30,
            'time': '2025-07-01T10:05:30'
        }
        """
        pass
    
    @abstractmethod
    async def get_option_chain(
        self,
        symbol: str,
        expiry: str,
        right: Optional[str] = None
    ) -> List[Dict]:
        """
        Get option chain data for a symbol and expiry.
        
        Args:
            symbol: Underlying symbol
            expiry: Expiration date (YYYY-MM-DD format)
            right: Optional 'CALL' or 'PUT' filter
            
        Returns:
            List of option contracts with greeks
            
        Example return:
        [
            {
                'symbol': 'SPX',
                'expiry': '2025-07-01',
                'strike': 5900,
                'right': 'CALL',
                'bid': 15.20,
                'ask': 15.60,
                'last': 15.40,
                'volume': 1250,
                'open_interest': 5420,
                'implied_volatility': 0.1245,
                'delta': 0.52,
                'gamma': 0.0015,
                'theta': -1.25,
                'vega': 0.85
            },
            ...
        ]
        """
        pass
    
    async def get_market_hours(self, symbol: str) -> Dict:
        """
        Get market hours for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with market hours information
            
        Example return:
        {
            'is_open': True,
            'regular_open': '09:30',
            'regular_close': '16:00',
            'extended_open': '04:00',
            'extended_close': '20:00',
            'timezone': 'US/Eastern'
        }
        """
        # Default implementation - can be overridden
        return {
            'is_open': self._is_market_open(),
            'regular_open': '09:30',
            'regular_close': '16:00',
            'extended_open': '04:00',
            'extended_close': '20:00',
            'timezone': 'US/Eastern'
        }
    
    def _is_market_open(self) -> bool:
        """Check if market is currently open (basic implementation)."""
        now = datetime.now()
        weekday = now.weekday()
        
        # Market closed on weekends
        if weekday >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Simple time check (9:30 AM - 4:00 PM ET)
        # This is a basic implementation - providers should override
        # with proper timezone and holiday handling
        hour = now.hour
        minute = now.minute
        
        market_open = 9 * 60 + 30  # 9:30 AM
        market_close = 16 * 60      # 4:00 PM
        current_minutes = hour * 60 + minute
        
        return market_open <= current_minutes < market_close
    
    async def subscribe_to_updates(
        self,
        symbol: str,
        callback,
        update_type: str = "price"
    ) -> str:
        """
        Subscribe to real-time updates for a symbol.
        
        Args:
            symbol: Trading symbol
            callback: Async callback function to receive updates
            update_type: Type of updates ('price', 'quote', 'trades')
            
        Returns:
            Subscription ID for managing the subscription
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support real-time subscriptions"
        )
    
    async def unsubscribe(self, subscription_id: str):
        """
        Unsubscribe from real-time updates.
        
        Args:
            subscription_id: ID returned from subscribe_to_updates
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support real-time subscriptions"
        )
    
    async def health_check(self) -> Dict:
        """
        Perform health check on the data provider.
        
        Returns:
            Dictionary with health status
            
        Example return:
        {
            'status': 'healthy',
            'connected': True,
            'latency_ms': 45,
            'last_update': '2025-07-01T10:05:30',
            'errors': []
        }
        """
        # Default implementation
        try:
            is_connected = await self.is_connected()
            
            # Try a simple request to measure latency
            start_time = datetime.now()
            if is_connected:
                await self.get_current_price('SPX')
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                'status': 'healthy' if is_connected else 'disconnected',
                'connected': is_connected,
                'latency_ms': latency_ms if is_connected else None,
                'last_update': datetime.now().isoformat(),
                'errors': []
            }
        except Exception as e:
            return {
                'status': 'error',
                'connected': False,
                'latency_ms': None,
                'last_update': datetime.now().isoformat(),
                'errors': [str(e)]
            }
