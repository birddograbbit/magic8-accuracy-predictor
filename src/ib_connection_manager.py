import logging
import asyncio
from typing import Optional
from ib_insync import IB

logger = logging.getLogger(__name__)

class IBConnectionManager:
    """Singleton manager for a single IB connection."""

    _instance: Optional["IBConnectionManager"] = None

    def __init__(self):
        self.ib: Optional[IB] = None
        self.host = "127.0.0.1"
        self.port = 7497
        self.client_id = 99
        self._lock = asyncio.Lock()

    @classmethod
    def instance(cls) -> "IBConnectionManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def connect(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 99) -> IB:
        """Synchronous wrapper around :meth:`connect_async`."""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Avoid run_until_complete if loop is already running
            raise RuntimeError("connect() cannot be called from an event loop; use connect_async")
        return loop.run_until_complete(self.connect_async(host, port, client_id))

    async def connect_async(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 99) -> IB:
        """Asynchronously connect to IBKR using ib_insync."""
        if self.ib and self.ib.isConnected():
            return self.ib

        self.host = host
        self.port = port
        self.client_id = client_id

        async with self._lock:
            if self.ib and self.ib.isConnected():
                return self.ib

            self.ib = IB()
            try:
                await self.ib.connectAsync(host, port, clientId=client_id)
                logger.info(
                    f"Connected to IBKR at {host}:{port} clientId={client_id}"
                )
            except Exception as e:
                logger.error(f"Failed to connect to IBKR: {e}")
                self.ib = None
                raise
        return self.ib

    def get_ib(self) -> IB:
        if not self.ib or not self.ib.isConnected():
            self.connect(self.host, self.port, self.client_id)
        return self.ib

    def disconnect(self):
        if self.ib and self.ib.isConnected():
            self.ib.disconnect()
            logger.info("Disconnected from IBKR")
        self.ib = None
