"""
Standalone IBKR data provider for direct connection.

This provider creates its own IBKR connection with a different client ID
to avoid conflicts. Ship-fast implementation using ib_insync.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ib_insync import IB, Stock, Index, Option, util

from .base_provider import BaseDataProvider

logger = logging.getLogger(__name__)


class StandaloneDataProvider(BaseDataProvider):
    """
    Direct IBKR connection provider.
    
    Uses a different client ID (default: 99) to avoid conflicts with
    other systems. Minimal implementation for fast shipping.
    """
    
    def __init__(
        self,
        ib_host: str = "127.0.0.1",
        ib_port: int = 7498,
        client_id: int = 99
    ):
        """Initialize standalone IBKR provider."""
        self.ib_host = ib_host
        self.ib_port = ib_port
        self.client_id = client_id
        self.ib: Optional[IB] = None
        
        # Contract cache
        self._contracts = {}
        
        logger.info(
            f"StandaloneDataProvider initialized: "
            f"{ib_host}:{ib_port}, client_id={client_id}"
        )
    
    async def connect(self) -> bool:
        """Connect to IBKR."""
        try:
            self.ib = IB()
            await self.ib.connectAsync(
                host=self.ib_host,
                port=self.ib_port,
                clientId=self.client_id,
                timeout=10
            )
            
            if self.ib.isConnected():
                logger.info(f"Connected to IBKR on client_id={self.client_id}")
                return True
            else:
                logger.error("IBKR connection failed")
                return False
                
        except Exception as e:
            logger.error(f"IBKR connection error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from IBKR."""
        if self.ib:
            self.ib.disconnect()
            self.ib = None
        logger.info("Disconnected from IBKR")
    
    async def is_connected(self) -> bool:
        """Check connection status."""
        return self.ib is not None and self.ib.isConnected()
    
    def _get_contract(self, symbol: str):
        """Get or create contract for symbol."""
        if symbol in self._contracts:
            return self._contracts[symbol]
        
        # Determine contract type
        if symbol in ['SPX', 'VIX', 'RUT', 'NDX']:
            contract = Index(symbol, 'CBOE')
        elif symbol == 'XSP':
            contract = Index('XSP', 'CBOE')
        else:
            # Default to stock
            contract = Stock(symbol, 'SMART', 'USD')
        
        self._contracts[symbol] = contract
        return contract
    
    async def get_price_data(
        self,
        symbol: str,
        bars: int = 100,
        interval: str = "5 mins"
    ) -> List[Dict]:
        """Get historical price bars from IBKR."""
        if not await self.is_connected():
            logger.error("Not connected to IBKR")
            return []
        
        try:
            contract = self._get_contract(symbol)
            
            # Request historical data
            bars_data = await self.ib.reqHistoricalDataAsync(
                contract,
                endDateTime='',
                durationStr='1 D' if bars <= 100 else '5 D',
                barSizeSetting=interval,
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1
            )
            
            # Format response
            formatted_bars = []
            for bar in bars_data[-bars:]:
                formatted_bars.append({
                    'time': bar.date.isoformat(),
                    'open': float(bar.open),
                    'high': float(bar.high),
                    'low': float(bar.low),
                    'close': float(bar.close),
                    'volume': int(bar.volume)
                })
            
            return formatted_bars
            
        except Exception as e:
            logger.error(f"Error getting price data for {symbol}: {e}")
            return []
    
    async def get_current_price(self, symbol: str) -> Dict:
        """Get current price from IBKR."""
        if not await self.is_connected():
            return {
                'symbol': symbol,
                'last': 0,
                'bid': 0,
                'ask': 0,
                'bid_size': 0,
                'ask_size': 0,
                'time': datetime.now().isoformat()
            }
        
        try:
            contract = self._get_contract(symbol)
            
            # Request market data
            self.ib.reqMktData(contract, '', False, False)
            
            # Wait for data
            await asyncio.sleep(1)
            
            ticker = self.ib.ticker(contract)
            
            return {
                'symbol': symbol,
                'last': float(ticker.last or ticker.close or 0),
                'bid': float(ticker.bid or 0),
                'ask': float(ticker.ask or 0),
                'bid_size': int(ticker.bidSize or 0),
                'ask_size': int(ticker.askSize or 0),
                'time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
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
        """Get VIX data from IBKR."""
        vix_quote = await self.get_current_price('VIX')
        
        # Calculate change (simplified - would need previous close)
        return {
            'last': vix_quote['last'],
            'change': 0,  # TODO: Calculate from previous close
            'change_pct': 0,
            'high': vix_quote['last'],  # TODO: Get daily high/low
            'low': vix_quote['last'],
            'time': vix_quote['time']
        }
    
    async def get_option_chain(
        self,
        symbol: str,
        expiry: str,
        right: Optional[str] = None
    ) -> List[Dict]:
        """Get option chain from IBKR."""
        if not await self.is_connected():
            return []
        
        try:
            # Get underlying contract
            underlying = self._get_contract(symbol)
            
            # Get chains
            chains = await self.ib.reqSecDefOptParamsAsync(
                underlying.symbol,
                '',
                underlying.secType,
                underlying.conId
            )
            
            if not chains:
                return []
            
            chain = chains[0]
            
            # Filter for expiry
            if expiry not in chain.expirations:
                return []
            
            # Get strikes around current price
            current_price = await self.get_current_price(symbol)
            atm_price = current_price['last']
            
            # Simple implementation - get 10 strikes around ATM
            all_strikes = sorted(chain.strikes)
            atm_index = min(range(len(all_strikes)), 
                          key=lambda i: abs(all_strikes[i] - atm_price))
            
            start_idx = max(0, atm_index - 5)
            end_idx = min(len(all_strikes), atm_index + 5)
            strikes = all_strikes[start_idx:end_idx]
            
            # Build option contracts
            options = []
            for strike in strikes:
                for r in ['C', 'P'] if right is None else [right[0]]:
                    option = Option(
                        symbol,
                        expiry.replace('-', ''),
                        strike,
                        r,
                        'SMART'
                    )
                    
                    # Simplified - just return basic data
                    options.append({
                        'symbol': symbol,
                        'expiry': expiry,
                        'strike': float(strike),
                        'right': 'CALL' if r == 'C' else 'PUT',
                        'bid': 0,
                        'ask': 0,
                        'last': 0,
                        'volume': 0,
                        'open_interest': 0,
                        'implied_volatility': 0,
                        'delta': 0,
                        'gamma': 0,
                        'theta': 0,
                        'vega': 0
                    })
            
            return options
            
        except Exception as e:
            logger.error(f"Error getting option chain: {e}")
            return []
