"""
Simple IB connection manager following the pattern from working examples.
Single connection, passed around, no over-engineering.
"""

import logging
import time
from typing import Optional, Dict, List
from datetime import datetime
import math
import threading

from ib_insync import IB, Stock, Index, util

logger = logging.getLogger(__name__)


class SimpleIBConnection:
    """Simple IB connection wrapper that maintains a single connection."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Ensure singleton pattern."""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize only once."""
        if hasattr(self, '_initialized'):
            return
            
        self.ib: Optional[IB] = None
        self.connected = False
        self.contracts = {}
        self.failed_symbols = set()
        self._initialized = True
        
        # Configure logging
        util.logToConsole(logging.WARNING)
        
    def connect(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 99) -> bool:
        """Connect to IB Gateway/TWS synchronously."""
        if self.connected and self.ib and self.ib.isConnected():
            logger.info("Already connected to IB")
            return True
            
        try:
            # Clean up any existing connection
            if self.ib:
                try:
                    self.ib.disconnect()
                except:
                    pass
                    
            # Create new IB instance
            self.ib = IB()
            
            # Error handler
            def on_error(reqId, errorCode, errorString, contract):
                if errorCode == 354:  # Not subscribed
                    if contract and hasattr(contract, 'symbol'):
                        self.failed_symbols.add(contract.symbol)
                        logger.debug(f"Market data not subscribed for {contract.symbol}")
                elif errorCode == 504:  # Not connected
                    logger.error("Lost connection to IB")
                    self.connected = False
                    
            self.ib.errorEvent += on_error
            
            # Connect synchronously
            logger.info(f"Connecting to IB at {host}:{port} with clientId={client_id}")
            self.ib.connect(host, port, clientId=client_id, timeout=10)
            
            # Wait a moment for connection to stabilize
            time.sleep(0.5)
            
            if self.ib.isConnected():
                self.connected = True
                logger.info("Successfully connected to IB")
                return True
            else:
                logger.error("Failed to connect to IB")
                return False
                
        except Exception as e:
            logger.error(f"IB connection error: {e}")
            self.connected = False
            if self.ib:
                try:
                    self.ib.disconnect()
                except:
                    pass
                self.ib = None
            return False
            
    def disconnect(self):
        """Disconnect from IB."""
        if self.ib and self.ib.isConnected():
            try:
                # Cancel any active market data
                for ticker in self.ib.tickers():
                    try:
                        self.ib.cancelMktData(ticker)
                    except:
                        pass
                        
                self.ib.disconnect()
                logger.info("Disconnected from IB")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
            finally:
                self.connected = False
                self.ib = None
                
    def get_contract(self, symbol: str):
        """Get or create contract for symbol."""
        if symbol in self.contracts:
            return self.contracts[symbol]
            
        # Create appropriate contract type
        if symbol in ['SPX', 'VIX', 'XSP']:
            contract = Index(symbol, 'CBOE', 'USD')
        elif symbol == 'RUT':
            contract = Index('RUT', 'RUSSELL', 'USD')
        elif symbol == 'NDX':
            contract = Index('NDX', 'NASDAQ', 'USD')
        else:
            contract = Stock(symbol, 'SMART', 'USD')
            
        self.contracts[symbol] = contract
        return contract
        
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol."""
        if not self.connected or not self.ib or not self.ib.isConnected():
            raise Exception("Not connected to IB")
            
        if symbol in self.failed_symbols:
            raise Exception(f"Market data not available for {symbol}")
            
        try:
            contract = self.get_contract(symbol)
            
            # Request market data
            ticker = self.ib.reqMktData(contract, '', False, False)
            
            # Wait for data with timeout
            timeout = 2.0
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if ticker.last and not math.isnan(ticker.last):
                    price = ticker.last
                    break
                elif ticker.close and not math.isnan(ticker.close):
                    price = ticker.close
                    break
                time.sleep(0.1)
            else:
                # Timeout
                self.ib.cancelMktData(ticker)
                raise Exception(f"Timeout getting price for {symbol}")
                
            # Cancel market data
            self.ib.cancelMktData(ticker)
            
            return float(price)
            
        except Exception as e:
            # Check if it's a subscription error
            error_msg = str(e).lower()
            if "not subscribed" in error_msg or "error 354" in error_msg:
                self.failed_symbols.add(symbol)
            raise
            
    def get_historical_data(
        self, 
        symbol: str, 
        duration: str = "1 D",
        bar_size: str = "5 mins"
    ) -> List[Dict]:
        """Get historical bars."""
        if not self.connected or not self.ib or not self.ib.isConnected():
            raise Exception("Not connected to IB")
            
        try:
            contract = self.get_contract(symbol)
            
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow='TRADES',
                useRTH=True
            )
            
            # Convert to dict format
            result = []
            for bar in bars:
                result.append({
                    'time': bar.date,
                    'open': float(bar.open),
                    'high': float(bar.high),
                    'low': float(bar.low),
                    'close': float(bar.close),
                    'volume': int(bar.volume)
                })
                
            return result
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return []
            
    def is_connected(self) -> bool:
        """Check if connected."""
        return self.connected and self.ib and self.ib.isConnected()


# Global singleton instance
ib_connection = SimpleIBConnection()
