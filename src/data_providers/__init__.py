"""
Data providers package for real-time market data access.

This package provides a flexible abstraction layer for accessing market data
from multiple sources:
- Magic8-Companion's IB connection
- Redis pub/sub
- Standalone IB connection
- Mock provider for testing
"""

from .base_provider import BaseDataProvider
from .companion_provider import CompanionDataProvider
from .redis_provider import RedisDataProvider
from .standalone_provider import StandaloneDataProvider
from .mock_provider import MockDataProvider

__all__ = [
    'BaseDataProvider',
    'CompanionDataProvider',
    'RedisDataProvider',
    'StandaloneDataProvider',
    'MockDataProvider',
    'get_data_provider'
]


def get_data_provider(config: dict) -> BaseDataProvider:
    """
    Factory function to create appropriate data provider based on configuration.
    
    Args:
        config: Data source configuration dictionary
        
    Returns:
        Configured data provider instance
    """
    primary_source = config.get('primary', 'companion')
    fallback_source = config.get('fallback')
    
    # Create primary provider
    primary_provider = _create_provider(primary_source, config)
    
    # Create fallback provider if specified
    if fallback_source and fallback_source != primary_source:
        fallback_provider = _create_provider(fallback_source, config)
        
        # Wrap in fallback handler
        from .fallback_provider import FallbackDataProvider
        return FallbackDataProvider(primary_provider, fallback_provider)
    
    return primary_provider


def _create_provider(provider_type: str, config: dict) -> BaseDataProvider:
    """Create a specific provider instance."""
    provider_config = config.get(provider_type, {})
    
    if not provider_config.get('enabled', True):
        raise ValueError(f"Provider '{provider_type}' is not enabled")
    
    if provider_type == 'companion':
        return CompanionDataProvider(
            base_url=provider_config.get('base_url', 'http://localhost:8765'),
            timeout=provider_config.get('timeout', 5),
            retry_attempts=provider_config.get('retry_attempts', 3)
        )
    
    elif provider_type == 'redis':
        return RedisDataProvider(
            host=provider_config.get('host', 'localhost'),
            port=provider_config.get('port', 6379),
            channels=provider_config.get('channels', {})
        )
    
    elif provider_type == 'standalone':
        return StandaloneDataProvider(
            ib_host=provider_config.get('ib_host', '127.0.0.1'),
            ib_port=provider_config.get('ib_port', 7498),
            client_id=provider_config.get('client_id', 99)
        )
    
    elif provider_type == 'mock':
        return MockDataProvider(provider_config)
    
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
