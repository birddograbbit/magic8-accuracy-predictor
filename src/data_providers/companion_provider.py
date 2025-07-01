"""
Data provider that uses Magic8-Companion's IB connection.

This provider communicates with Magic8-Companion's API to get market data,
avoiding the need for a separate IBKR connection.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
from aiohttp import ClientTimeout

from .base_provider import BaseDataProvider

logger = logging.getLogger(__name__)


class CompanionDataProvider(BaseDataProvider):
    """
    Data provider that uses Magic8-Companion's IB connection via HTTP API.
    
    This is the recommended provider for production use as it:
    - Avoids IBKR connection conflicts
    - Leverages existing connection management
    - Provides centralized rate limiting
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8765",
        timeout: int = 5,
        retry_attempts: int = 3
    ):
        """
        Initialize the companion data provider.
        
        Args:
            base_url: Base URL for Magic8-Companion API
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = ClientTimeout(total=timeout)
        self.retry_attempts = retry_attempts
        self.session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        
        logger.info(f"CompanionDataProvider initialized with base_url: {base_url}")
    
    async def connect(self) -> bool:
        """Establish connection to Magic8-Companion API."""
        try:
            # Create session if not exists
            if not self.session:
                self.session = aiohttp.ClientSession(timeout=self.timeout)
            
            # Test connection with health check
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    self._connected = True
                    logger.info("Successfully connected to Magic8-Companion API")
                    return True
                else:
                    logger.error(f"Failed to connect: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Magic8-Companion API."""
        if self.session:
            await self.session.close()
            self.session = None
        self._connected = False
        logger.info("Disconnected from Magic8-Companion API")
    
    async def is_connected(self) -> bool:
        """Check if provider is connected and ready."""
        if not self._connected or not self.session:
            return False
            
        try:
            # Quick health check
            async with self.session.get(
                f"{self.base_url}/health",
                timeout=ClientTimeout(total=1)
            ) as response:
                return response.status == 200
        except:
            return False
    
    async def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict:
        """
        Make HTTP request with retry logic.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Query parameters
            json_data: JSON body data
            
        Returns:
            Response data as dictionary
        """
        if not self.session:
            await self.connect()
            
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.retry_attempts):
            try:
                async with self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data
                ) as response:
                    response.raise_for_status()
                    return await response.json()
                    
            except aiohttp.ClientError as e:
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.retry_attempts}): {e}"
                )
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
                else:
                    raise
    
    async def get_price_data(
        self,
        symbol: str,
        bars: int = 100,
        interval: str = "5 mins"
    ) -> List[Dict]:
        """Get historical price bars from Magic8-Companion."""
        try:
            data = await self._make_request(
                f"/api/market_data/{symbol}/bars",
                params={
                    "count": bars,
                    "interval": interval
                }
            )
            
            # Ensure consistent format
            formatted_bars = []
            for bar in data.get('bars', []):
                formatted_bars.append({
                    'time': bar.get('time'),
                    'open': float(bar.get('open', 0)),
                    'high': float(bar.get('high', 0)),
                    'low': float(bar.get('low', 0)),
                    'close': float(bar.get('close', 0)),
                    'volume': int(bar.get('volume', 0))
                })
                
            return formatted_bars
            
        except Exception as e:
            logger.error(f"Failed to get price data for {symbol}: {e}")
            raise
    
    async def get_current_price(self, symbol: str) -> Dict:
        """Get current price snapshot from Magic8-Companion."""
        try:
            data = await self._make_request(f"/api/market_data/{symbol}/quote")
            
            return {
                'symbol': symbol,
                'last': float(data.get('last', 0)),
                'bid': float(data.get('bid', 0)),
                'ask': float(data.get('ask', 0)),
                'bid_size': int(data.get('bid_size', 0)),
                'ask_size': int(data.get('ask_size', 0)),
                'time': data.get('time', datetime.now().isoformat())
            }
            
        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            raise
    
    async def get_vix_data(self) -> Dict:
        """Get current VIX data from Magic8-Companion."""
        try:
            data = await self._make_request("/api/market_data/VIX/quote")
            
            return {
                'last': float(data.get('last', 0)),
                'change': float(data.get('change', 0)),
                'change_pct': float(data.get('change_pct', 0)),
                'high': float(data.get('high', 0)),
                'low': float(data.get('low', 0)),
                'time': data.get('time', datetime.now().isoformat())
            }
            
        except Exception as e:
            logger.error(f"Failed to get VIX data: {e}")
            raise
    
    async def get_option_chain(
        self,
        symbol: str,
        expiry: str,
        right: Optional[str] = None
    ) -> List[Dict]:
        """Get option chain data from Magic8-Companion."""
        try:
            params = {
                'expiry': expiry
            }
            if right:
                params['right'] = right
                
            data = await self._make_request(
                f"/api/options/{symbol}/chain",
                params=params
            )
            
            # Format option data
            formatted_options = []
            for option in data.get('options', []):
                formatted_options.append({
                    'symbol': symbol,
                    'expiry': expiry,
                    'strike': float(option.get('strike', 0)),
                    'right': option.get('right'),
                    'bid': float(option.get('bid', 0)),
                    'ask': float(option.get('ask', 0)),
                    'last': float(option.get('last', 0)),
                    'volume': int(option.get('volume', 0)),
                    'open_interest': int(option.get('open_interest', 0)),
                    'implied_volatility': float(option.get('implied_volatility', 0)),
                    'delta': float(option.get('delta', 0)),
                    'gamma': float(option.get('gamma', 0)),
                    'theta': float(option.get('theta', 0)),
                    'vega': float(option.get('vega', 0))
                })
                
            return formatted_options
            
        except Exception as e:
            logger.error(f"Failed to get option chain for {symbol}: {e}")
            raise
    
    async def subscribe_to_updates(
        self,
        symbol: str,
        callback,
        update_type: str = "price"
    ) -> str:
        """
        Subscribe to real-time updates via WebSocket.
        
        Note: This requires Magic8-Companion to have WebSocket support enabled.
        """
        # WebSocket URL
        ws_url = self.base_url.replace('http', 'ws') + '/ws/market_data'
        
        # Create WebSocket connection
        session = aiohttp.ClientSession()
        
        try:
            ws = await session.ws_connect(ws_url)
            
            # Send subscription request
            await ws.send_json({
                'action': 'subscribe',
                'symbol': symbol,
                'type': update_type
            })
            
            # Start listening task
            subscription_id = f"{symbol}_{update_type}_{id(callback)}"
            
            async def listen():
                try:
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            if data.get('symbol') == symbol:
                                await callback(data)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.error(f"WebSocket error: {ws.exception()}")
                            break
                except Exception as e:
                    logger.error(f"WebSocket listener error: {e}")
                finally:
                    await ws.close()
                    await session.close()
            
            # Start listener task
            asyncio.create_task(listen())
            
            logger.info(f"Subscribed to {update_type} updates for {symbol}")
            return subscription_id
            
        except Exception as e:
            await session.close()
            logger.error(f"Failed to subscribe to updates: {e}")
            raise
    
    async def health_check(self) -> Dict:
        """Perform health check on Magic8-Companion connection."""
        try:
            # Get health status from companion
            data = await self._make_request("/api/health/detailed")
            
            return {
                'status': data.get('status', 'unknown'),
                'connected': data.get('ib_connected', False),
                'latency_ms': data.get('latency_ms'),
                'last_update': data.get('last_update', datetime.now().isoformat()),
                'errors': data.get('errors', [])
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'connected': False,
                'latency_ms': None,
                'last_update': datetime.now().isoformat(),
                'errors': [str(e)]
            }
