"""
Redis data provider for subscribing to market data streams.

This is a simplified implementation that subscribes to Redis pub/sub channels
for market data. Ideal for distributed systems where Magic8-Companion publishes
data to Redis.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

import redis.asyncio as aioredis

from .base_provider import BaseDataProvider

logger = logging.getLogger(__name__)


class RedisDataProvider(BaseDataProvider):
    """
    Simple Redis-based data provider using pub/sub pattern.
    
    Ship-fast implementation - can be enhanced later with:
    - Connection pooling
    - Better error handling
    - Data validation
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        channels: Optional[Dict] = None,
        db: int = 0
    ):
        """Initialize Redis data provider."""
        self.host = host
        self.port = port
        self.db = db
        self.channels = channels or {
            'price_data': 'market:prices:{symbol}',
            'vix_data': 'market:vix',
            'option_data': 'market:options:{symbol}'
        }
        
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        self._cache = {}  # Simple in-memory cache
        
        logger.info(f"RedisDataProvider initialized: {host}:{port}")
    
    async def connect(self) -> bool:
        """Connect to Redis."""
        try:
            self.redis = await aioredis.from_url(
                f"redis://{self.host}:{self.port}/{self.db}",
                decode_responses=True
            )
            
            # Test connection
            await self.redis.ping()
            
            # Create pubsub
            self.pubsub = self.redis.pubsub()
            
            logger.info("Connected to Redis")
            return True
            
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
        logger.info("Disconnected from Redis")
    
    async def is_connected(self) -> bool:
        """Check connection status."""
        if not self.redis:
            return False
        try:
            await self.redis.ping()
            return True
        except:
            return False
    
    async def get_price_data(
        self,
        symbol: str,
        bars: int = 100,
        interval: str = "5 mins"
    ) -> List[Dict]:
        """Get price data from Redis cache."""
        # Try cache first
        cache_key = f"bars:{symbol}:{interval}"
        
        # Get from Redis
        data = await self.redis.get(cache_key)
        if data:
            bars_data = json.loads(data)
            # Return requested number of bars
            return bars_data[-bars:] if len(bars_data) > bars else bars_data
        
        # Fallback: subscribe and wait for data
        channel = self.channels['price_data'].format(symbol=symbol)
        await self.pubsub.subscribe(channel)
        
        try:
            # Wait for data with timeout
            async with asyncio.timeout(5.0):
                async for message in self.pubsub.listen():
                    if message['type'] == 'message':
                        data = json.loads(message['data'])
                        if 'bars' in data:
                            return data['bars'][-bars:]
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for price data: {symbol}")
            return []
        finally:
            await self.pubsub.unsubscribe(channel)
    
    async def get_current_price(self, symbol: str) -> Dict:
        """Get current price from Redis."""
        # Simple implementation - get latest from cache
        quote_key = f"quote:{symbol}"
        
        data = await self.redis.get(quote_key)
        if data:
            return json.loads(data)
        
        # Return empty quote if not found
        return {
            'symbol': symbol,
            'last': 0,
            'bid': 0,
            'ask': 0,
            'bid_size': 0,
            'ask_size': 0,
            'time': datetime.now().isoformat()
        }
    
    async def get_vix_data(self) -> Dict:
        """Get VIX data from Redis."""
        vix_key = "quote:VIX"
        
        data = await self.redis.get(vix_key)
        if data:
            vix_data = json.loads(data)
            return {
                'last': vix_data.get('last', 0),
                'change': vix_data.get('change', 0),
                'change_pct': vix_data.get('change_pct', 0),
                'high': vix_data.get('high', 0),
                'low': vix_data.get('low', 0),
                'time': vix_data.get('time', datetime.now().isoformat())
            }
        
        # Return default if not found
        return {
            'last': 15.0,  # Default VIX
            'change': 0,
            'change_pct': 0,
            'high': 15.0,
            'low': 15.0,
            'time': datetime.now().isoformat()
        }
    
    async def get_option_chain(
        self,
        symbol: str,
        expiry: str,
        right: Optional[str] = None
    ) -> List[Dict]:
        """Get option chain from Redis."""
        # Simple implementation - just return empty for now
        # Can be enhanced later with actual option data
        logger.warning(f"Option chain not implemented for Redis provider")
        return []
    
    async def subscribe_to_updates(
        self,
        symbol: str,
        callback,
        update_type: str = "price"
    ) -> str:
        """Subscribe to real-time updates."""
        channel = self.channels.get(f'{update_type}_data', '').format(symbol=symbol)
        
        # Create subscription task
        subscription_id = f"{symbol}_{update_type}_{id(callback)}"
        
        async def listen():
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(channel)
            
            try:
                async for message in pubsub.listen():
                    if message['type'] == 'message':
                        data = json.loads(message['data'])
                        await callback(data)
            except Exception as e:
                logger.error(f"Subscription error: {e}")
            finally:
                await pubsub.close()
        
        # Start listener
        asyncio.create_task(listen())
        
        logger.info(f"Subscribed to {channel}")
        return subscription_id
