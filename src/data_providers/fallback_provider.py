"""
Fallback data provider for automatic failover.

Simple wrapper that tries primary provider first, then falls back to
secondary if primary fails.
"""

import logging
from typing import Dict, List, Optional

from .base_provider import BaseDataProvider

logger = logging.getLogger(__name__)


class FallbackDataProvider(BaseDataProvider):
    """
    Provides automatic failover between two data providers.
    
    Ship-fast implementation - tries primary first, then fallback.
    """
    
    def __init__(
        self,
        primary: BaseDataProvider,
        fallback: BaseDataProvider
    ):
        """Initialize with primary and fallback providers."""
        self.primary = primary
        self.fallback = fallback
        self.current = primary
        self._primary_failed = False
        
        logger.info(
            f"FallbackDataProvider initialized: "
            f"primary={type(primary).__name__}, "
            f"fallback={type(fallback).__name__}"
        )
    
    async def connect(self) -> bool:
        """Connect to primary, fallback if needed."""
        # Try primary first
        if await self.primary.connect():
            self.current = self.primary
            self._primary_failed = False
            logger.info("Connected to primary provider")
            return True
        
        # Primary failed, try fallback
        logger.warning("Primary provider failed, trying fallback")
        if await self.fallback.connect():
            self.current = self.fallback
            self._primary_failed = True
            logger.info("Connected to fallback provider")
            return True
        
        logger.error("Both providers failed to connect")
        return False
    
    async def disconnect(self):
        """Disconnect both providers."""
        await self.primary.disconnect()
        await self.fallback.disconnect()
    
    async def is_connected(self) -> bool:
        """Check current provider connection."""
        return await self.current.is_connected()
    
    async def _try_with_fallback(self, method_name: str, *args, **kwargs):
        """
        Try method on current provider, fallback if fails.
        
        Simple implementation - if current fails, switch to other.
        """
        try:
            # Try current provider
            method = getattr(self.current, method_name)
            result = await method(*args, **kwargs)
            
            # If we're on fallback and primary is back, switch back
            if self._primary_failed and await self.primary.is_connected():
                self.current = self.primary
                self._primary_failed = False
                logger.info("Switched back to primary provider")
            
            return result
            
        except Exception as e:
            logger.warning(f"{method_name} failed on {type(self.current).__name__}: {e}")
            
            # Switch to other provider
            if self.current == self.primary:
                if await self.fallback.is_connected() or await self.fallback.connect():
                    self.current = self.fallback
                    self._primary_failed = True
                    logger.info("Switched to fallback provider")
            else:
                if await self.primary.is_connected() or await self.primary.connect():
                    self.current = self.primary
                    self._primary_failed = False
                    logger.info("Switched back to primary provider")
            
            # Retry with new provider
            try:
                method = getattr(self.current, method_name)
                return await method(*args, **kwargs)
            except Exception as e2:
                logger.error(f"{method_name} failed on both providers: {e2}")
                raise
    
    async def get_price_data(
        self,
        symbol: str,
        bars: int = 100,
        interval: str = "5 mins"
    ) -> List[Dict]:
        """Get price data with fallback."""
        return await self._try_with_fallback(
            'get_price_data',
            symbol,
            bars=bars,
            interval=interval
        )
    
    async def get_current_price(self, symbol: str) -> Dict:
        """Get current price with fallback."""
        return await self._try_with_fallback('get_current_price', symbol)
    
    async def get_vix_data(self) -> Dict:
        """Get VIX data with fallback."""
        return await self._try_with_fallback('get_vix_data')
    
    async def get_option_chain(
        self,
        symbol: str,
        expiry: str,
        right: Optional[str] = None
    ) -> List[Dict]:
        """Get option chain with fallback."""
        return await self._try_with_fallback(
            'get_option_chain',
            symbol,
            expiry,
            right=right
        )
    
    async def health_check(self) -> Dict:
        """Check health of both providers."""
        primary_health = await self.primary.health_check()
        fallback_health = await self.fallback.health_check()
        
        return {
            'status': 'healthy' if primary_health['status'] == 'healthy' else 'degraded',
            'connected': await self.is_connected(),
            'current_provider': type(self.current).__name__,
            'primary': primary_health,
            'fallback': fallback_health,
            'last_update': primary_health.get('last_update')
        }
