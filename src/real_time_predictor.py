"""
Real-time prediction service for Magic8 orders.

This module provides the core functionality for predicting win/loss probabilities
for Magic8 trading orders in real-time using trained XGBoost models.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from dataclasses import dataclass

from .feature_engineering import RealTimeFeatureGenerator
from .data_providers import get_data_provider

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Container for prediction results."""
    symbol: str
    strategy: str
    win_probability: float
    loss_probability: float
    confidence: float
    features_used: int
    prediction_time_ms: float
    timestamp: str
    metadata: Dict = None


class Magic8Predictor:
    """
    Real-time predictor for Magic8 trading orders.
    
    This class handles:
    - Model loading and management
    - Feature generation for incoming orders
    - Real-time predictions with caching
    - Performance monitoring
    """
    
    def __init__(
        self,
        model_path: str,
        data_provider_config: Dict,
        feature_config: Optional[Dict] = None,
        cache_config: Optional[Dict] = None
    ):
        """
        Initialize the predictor.
        
        Args:
            model_path: Path to the trained XGBoost model
            data_provider_config: Configuration for data provider
            feature_config: Optional feature generation configuration
            cache_config: Optional cache configuration
        """
        self.model_path = Path(model_path)
        self.model = self._load_model()
        
        # Initialize data provider
        self.data_provider = get_data_provider(data_provider_config)
        
        # Initialize feature generator
        self.feature_generator = RealTimeFeatureGenerator(
            data_provider=self.data_provider,
            config=feature_config or {}
        )
        
        # Cache configuration
        self.cache_enabled = cache_config and cache_config.get('enabled', False)
        self.cache_ttl = cache_config.get('ttl_seconds', 300) if cache_config else 300
        self.cache = {} if self.cache_enabled else None
        
        # Performance tracking
        self.prediction_count = 0
        self.total_latency_ms = 0
        
        logger.info(f"Magic8Predictor initialized with model: {model_path}")
        
    def _load_model(self):
        """Load the XGBoost model from disk."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")
            
        try:
            model = joblib.load(self.model_path)
            logger.info(f"Model loaded successfully from {self.model_path}")
            return model
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
            
    def _get_cache_key(self, order: Dict) -> str:
        """Generate cache key for an order."""
        # Create deterministic key from order details
        key_parts = [
            order.get('symbol', ''),
            order.get('strategy', ''),
            str(order.get('strikes', [])),
            str(order.get('expiry', '')),
            str(order.get('right', ''))
        ]
        return "|".join(key_parts)
        
    def _check_cache(self, cache_key: str) -> Optional[PredictionResult]:
        """Check if prediction exists in cache."""
        if not self.cache_enabled or cache_key not in self.cache:
            return None
            
        cached_item = self.cache[cache_key]
        cache_time = datetime.fromisoformat(cached_item['timestamp'])
        age_seconds = (datetime.now() - cache_time).total_seconds()
        
        if age_seconds < self.cache_ttl:
            logger.debug(f"Cache hit for key: {cache_key}")
            return cached_item['result']
        else:
            # Remove expired item
            del self.cache[cache_key]
            return None
            
    def _update_cache(self, cache_key: str, result: PredictionResult):
        """Update cache with new prediction."""
        if self.cache_enabled:
            self.cache[cache_key] = {
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            # Simple cache size management
            if len(self.cache) > 1000:
                # Remove oldest entries
                sorted_keys = sorted(
                    self.cache.keys(),
                    key=lambda k: self.cache[k]['timestamp']
                )
                for key in sorted_keys[:100]:
                    del self.cache[key]
                    
    async def predict_order(
        self,
        order: Dict,
        use_cache: bool = True
    ) -> PredictionResult:
        """
        Predict win/loss probability for a Magic8 order.
        
        Args:
            order: Dictionary containing order details
            use_cache: Whether to use cached predictions
            
        Returns:
            PredictionResult object with prediction details
        """
        start_time = datetime.now()
        
        # Check cache if enabled
        if use_cache:
            cache_key = self._get_cache_key(order)
            cached_result = self._check_cache(cache_key)
            if cached_result:
                return cached_result
        
        try:
            # Generate features
            features, feature_names = await self.feature_generator.generate_features(
                symbol=order.get('symbol'),
                order_details=order
            )
            
            # Convert to array for prediction
            feature_array = np.array([features])
            
            # Get prediction probabilities
            probabilities = self.model.predict_proba(feature_array)[0]
            
            # Calculate metrics
            win_probability = float(probabilities[1])
            loss_probability = float(probabilities[0])
            confidence = abs(win_probability - 0.5) * 2
            
            # Calculate latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Create result
            result = PredictionResult(
                symbol=order.get('symbol', 'UNKNOWN'),
                strategy=order.get('strategy', 'UNKNOWN'),
                win_probability=win_probability,
                loss_probability=loss_probability,
                confidence=confidence,
                features_used=len(features),
                prediction_time_ms=latency_ms,
                timestamp=datetime.now().isoformat(),
                metadata={
                    'model_version': getattr(self.model, 'version', '1.0.0'),
                    'feature_names': feature_names[:10]  # Top 10 features
                }
            )
            
            # Update cache
            if use_cache:
                self._update_cache(cache_key, result)
                
            # Update performance metrics
            self.prediction_count += 1
            self.total_latency_ms += latency_ms
            
            logger.info(
                f"Prediction completed for {order.get('symbol')} {order.get('strategy')}: "
                f"win_prob={win_probability:.2%}, latency={latency_ms:.1f}ms"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed for order {order}: {e}")
            raise
            
    async def predict_batch(
        self,
        orders: List[Dict],
        max_concurrent: int = 10
    ) -> List[PredictionResult]:
        """
        Predict multiple orders in batch.
        
        Args:
            orders: List of order dictionaries
            max_concurrent: Maximum concurrent predictions
            
        Returns:
            List of PredictionResult objects
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def predict_with_semaphore(order):
            async with semaphore:
                return await self.predict_order(order)
                
        tasks = [predict_with_semaphore(order) for order in orders]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch prediction failed for order {i}: {result}")
            else:
                valid_results.append(result)
                
        return valid_results
        
    def get_performance_stats(self) -> Dict:
        """Get performance statistics."""
        avg_latency = (
            self.total_latency_ms / self.prediction_count
            if self.prediction_count > 0 else 0
        )
        
        return {
            'total_predictions': self.prediction_count,
            'average_latency_ms': avg_latency,
            'cache_size': len(self.cache) if self.cache_enabled else 0,
            'cache_enabled': self.cache_enabled,
            'model_path': str(self.model_path)
        }
        
    def clear_cache(self):
        """Clear prediction cache."""
        if self.cache_enabled:
            self.cache.clear()
            logger.info("Prediction cache cleared")
            
    async def warmup(self, sample_orders: Optional[List[Dict]] = None):
        """
        Warmup the predictor with sample predictions.
        
        Args:
            sample_orders: Optional list of sample orders
        """
        if sample_orders is None:
            # Create default sample orders
            sample_orders = [
                {
                    'symbol': 'SPX',
                    'strategy': 'Butterfly',
                    'strikes': [5900, 5910, 5920],
                    'expiry': '2025-07-01',
                    'right': 'CALL',
                    'quantity': 1
                },
                {
                    'symbol': 'SPY',
                    'strategy': 'Vertical',
                    'strikes': [590, 595],
                    'expiry': '2025-07-01',
                    'right': 'CALL',
                    'quantity': 5
                }
            ]
            
        logger.info(f"Starting predictor warmup with {len(sample_orders)} samples")
        
        # Run predictions
        results = await self.predict_batch(sample_orders)
        
        logger.info(
            f"Warmup completed: {len(results)} successful predictions, "
            f"avg latency: {self.get_performance_stats()['average_latency_ms']:.1f}ms"
        )
        

class PredictionService:
    """
    High-level service for managing predictions.
    
    This service handles:
    - Multiple model management
    - Symbol-specific model selection
    - Fallback strategies
    - Integration with external systems
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the prediction service.
        
        Args:
            config: Service configuration dictionary
        """
        self.config = config
        self.predictors = {}
        self._initialize_predictors()
        
    def _initialize_predictors(self):
        """Initialize predictors based on configuration."""
        models_config = self.config.get('prediction', {}).get('models', [])
        data_config = self.config.get('data_source', {})
        
        for model_cfg in models_config:
            model_name = model_cfg['name']
            model_path = model_cfg['path']
            symbols = model_cfg.get('symbols', [])
            
            # Create predictor
            predictor = Magic8Predictor(
                model_path=model_path,
                data_provider_config=data_config,
                feature_config=self.config.get('prediction', {}).get('feature_config'),
                cache_config=self.config.get('performance', {}).get('cache')
            )
            
            # Register for each symbol
            for symbol in symbols:
                self.predictors[symbol] = predictor
                
            logger.info(f"Initialized model '{model_name}' for symbols: {symbols}")
            
    def get_predictor(self, symbol: str) -> Optional[Magic8Predictor]:
        """Get predictor for a specific symbol."""
        return self.predictors.get(symbol)
        
    async def predict(self, order: Dict) -> Optional[PredictionResult]:
        """
        Predict order outcome with appropriate model.
        
        Args:
            order: Order dictionary
            
        Returns:
            PredictionResult or None if no predictor available
        """
        symbol = order.get('symbol')
        if not symbol:
            logger.error("No symbol in order")
            return None
            
        predictor = self.get_predictor(symbol)
        if not predictor:
            logger.warning(f"No predictor available for symbol: {symbol}")
            return None
            
        return await predictor.predict_order(order)
        
    async def warmup_all(self):
        """Warmup all predictors."""
        unique_predictors = set(self.predictors.values())
        
        for predictor in unique_predictors:
            await predictor.warmup()
            
    def get_status(self) -> Dict:
        """Get service status."""
        unique_predictors = set(self.predictors.values())
        
        return {
            'symbol_coverage': list(self.predictors.keys()),
            'num_models': len(unique_predictors),
            'predictors': [
                {
                    'model_path': str(p.model_path),
                    'stats': p.get_performance_stats()
                }
                for p in unique_predictors
            ]
        }


# Singleton instance management
_prediction_service = None


def get_prediction_service(config: Optional[Dict] = None) -> PredictionService:
    """
    Get or create the prediction service singleton.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        PredictionService instance
    """
    global _prediction_service
    
    if _prediction_service is None:
        if config is None:
            # Load default config
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"
            if config_path.exists():
                import yaml
                with open(config_path) as f:
                    config = yaml.safe_load(f)
            else:
                raise ValueError("No configuration provided and default not found")
                
        _prediction_service = PredictionService(config)
        
    return _prediction_service
