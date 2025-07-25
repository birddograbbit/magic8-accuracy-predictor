"""
Simplified standalone IBKR data provider.
Based on working examples - just create one connection and use it.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
import math

from ib_insync import IB, Stock, Index, Option, util
from src.constants import DEFAULT_IB_PORT
from src.ib_connection_manager import IBConnectionManager

from .base_provider import BaseDataProvider

logger = logging.getLogger(__name__)


class StandaloneDataProvider(BaseDataProvider):
    """
    Direct IBKR connection provider - simplified version.
    """
    
    def __init__(
        self,
        ib_host: str = "127.0.0.1",
        ib_port: int = DEFAULT_IB_PORT,
        client_id: int = 99
    ):
        """Initialize standalone IBKR provider."""
        self.ib_host = ib_host
        self.ib_port = ib_port
        self.client_id = client_id
        self.ib: Optional[IB] = None  # will be obtained from IBConnectionManager
        
        # Contract cache
        self._contracts = {}
        
        # Track failed symbols to avoid repeated subscription errors
        self._failed_symbols: Set[str] = set()

        # Caches for daily data
        self._previous_close_cache: Dict[str, float] = {}
        self._daily_highs_lows: Dict[str, Dict[str, float]] = {}
        self._cache_timestamp: Optional[datetime] = None
        
        logger.info(
            f"StandaloneDataProvider initialized: "
            f"{ib_host}:{ib_port}, client_id={client_id}"
        )
    
    async def connect(self) -> bool:
        """Connect to IBKR using the shared connection manager."""
        try:
            manager = IBConnectionManager.instance()
            self.ib = await manager.connect_async(
                self.ib_host, self.ib_port, self.client_id
            )

            def error_handler(reqId, errorCode, errorString, contract):
                if errorCode == 354:
                    logger.warning(
                        f"Market data not subscribed for {contract.symbol if contract else 'unknown'}"
                    )
                    if contract and hasattr(contract, 'symbol'):
                        self._failed_symbols.add(contract.symbol)

            self.ib.errorEvent += error_handler

            return self.ib.isConnected()
        except Exception as e:
            logger.error(f"IBKR connection error: {e}")
            self.ib = None
            return False
    
    async def disconnect(self):
        """Disconnect from IBKR."""
        IBConnectionManager.instance().disconnect()
        self.ib = None

    async def is_connected(self) -> bool:
        """Check connection status."""
        if self.ib is None:
            return False
        return self.ib.isConnected()
    
    def _get_contract(self, symbol: str):
        """Get or create contract for symbol."""
        if symbol in self._contracts:
            return self._contracts[symbol]
        
        # Determine contract type based on correct exchanges
        if symbol == 'SPX':
            contract = Index('SPX', 'CBOE', 'USD')
        elif symbol == 'VIX':
            contract = Index('VIX', 'CBOE', 'USD')
        elif symbol == 'RUT':
            contract = Index('RUT', 'RUSSELL', 'USD')  # Russell 2000
        elif symbol == 'NDX':
            contract = Index('NDX', 'NASDAQ', 'USD')   # Nasdaq 100
        elif symbol == 'XSP':
            contract = Index('XSP', 'CBOE', 'USD')     # Mini-SPX
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
        
        # Skip if we know this symbol has subscription issues
        if symbol in self._failed_symbols:
            logger.debug(f"Skipping {symbol} - known subscription failure")
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
            error_msg = str(e)
            if "market data is not subscribed" in error_msg.lower() or "error 354" in error_msg.lower():
                logger.warning(f"Market data subscription missing for {symbol}")
                self._failed_symbols.add(symbol)
            else:
                logger.error(f"Error getting price data for {symbol}: {e}")
            return []
    
    async def get_current_price(self, symbol: str) -> Dict:
        """Get current price from IBKR."""
        if not await self.is_connected():
            raise Exception("Not connected to IBKR")
        
        # Skip if we know this symbol has subscription issues
        if symbol in self._failed_symbols:
            raise Exception(f"Market data subscription missing for {symbol}")
        
        ticker = None
        try:
            contract = self._get_contract(symbol)

            # Request market data
            ticker = self.ib.reqMktData(contract, '', False, False)

            # Wait for data with timeout
            timeout = 5  # Increased timeout
            start_time = asyncio.get_event_loop().time()

            while (ticker.last is None or math.isnan(ticker.last)) and ticker.close is None:
                await asyncio.sleep(0.1)
                if asyncio.get_event_loop().time() - start_time > timeout:
                    if symbol in self._failed_symbols:
                        raise Exception(f"Market data subscription missing for {symbol}")
                    raise Exception(f"Timeout waiting for market data for {symbol}")
            
            # Helper function to safely convert to int, handling NaN
            def safe_int(value):
                if value is None or (isinstance(value, float) and math.isnan(value)):
                    return 0
                return int(value)
            
            # Helper function to safely convert to float, handling NaN
            def safe_float(value):
                if value is None or (isinstance(value, float) and math.isnan(value)):
                    return 0.0
                return float(value)
            
            return {
                'symbol': symbol,
                'last': safe_float(ticker.last or ticker.close),
                'bid': safe_float(ticker.bid),
                'ask': safe_float(ticker.ask),
                'bid_size': safe_int(ticker.bidSize),
                'ask_size': safe_int(ticker.askSize),
                'time': datetime.now().isoformat()
            }
            
        except Exception as e:
            # Re-raise the exception to be handled by DataManager
            raise e
        finally:
            if ticker is not None and hasattr(ticker, "reqId") and ticker.reqId is not None:
                try:
                    self.ib.cancelMktData(ticker)
                except Exception as cancel_error:
                    logger.debug(
                        f"Error cancelling market data for {symbol}: {cancel_error}"
                    )

    async def _update_daily_data(self, symbol: str):
        """Fetch daily bar data to update previous close and high/low."""
        try:
            bars = await self.get_price_data(symbol, bars=2, interval="1 day")
            if len(bars) >= 2:
                prev_bar = bars[-2]
                self._previous_close_cache[symbol] = prev_bar['close']
                today_bar = bars[-1]
                self._daily_highs_lows[symbol] = {
                    'high': today_bar['high'],
                    'low': today_bar['low']
                }
            elif len(bars) == 1:
                today_bar = bars[0]
                self._daily_highs_lows[symbol] = {
                    'high': today_bar['high'],
                    'low': today_bar['low']
                }
        except Exception as e:
            logger.warning(f"Could not update daily data for {symbol}: {e}")
    
    async def get_vix_data(self) -> Dict:
        """Get VIX data from IBKR with proper change calculation."""
        try:
            if self._cache_timestamp is None or (
                datetime.now() - self._cache_timestamp
            ).total_seconds() > 3600:
                await self._update_daily_data('VIX')
                self._cache_timestamp = datetime.now()

            vix_quote = await self.get_current_price('VIX')
            current_price = vix_quote['last']

            prev_close = self._previous_close_cache.get('VIX', current_price)
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0

            daily_data = self._daily_highs_lows.get('VIX', {})
            daily_high = max(daily_data.get('high', current_price), current_price)
            daily_low = min(daily_data.get('low', current_price), current_price)

            return {
                'last': current_price,
                'change': change,
                'change_pct': change_pct,
                'high': daily_high,
                'low': daily_low,
                'time': vix_quote['time'],
                'prev_close': prev_close
            }
        except Exception as e:
            logger.error(f"Error getting VIX data: {e}")
            return {
                'last': 15.0,
                'change': 0,
                'change_pct': 0,
                'high': 15.0,
                'low': 15.0,
                'time': datetime.now().isoformat(),
                'prev_close': 15.0
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
