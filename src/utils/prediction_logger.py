"""
Prediction logger middleware for Magic8 Accuracy Predictor.
Ensures all predictions are properly logged for monitoring and analysis.

This can be added to any integration to enable logging.
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PredictionLogger:
    """Logs predictions to JSONL file for monitoring and analysis."""
    
    def __init__(self, log_file: str = "logs/predictions.jsonl"):
        """Initialize prediction logger."""
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        
    async def log_prediction(
        self,
        order: Dict[str, Any],
        prediction_result: Any,
        threshold: float = 0.55,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a prediction to the JSONL file.
        
        Args:
            order: The order being predicted
            prediction_result: The prediction result object
            threshold: The win probability threshold
            metadata: Additional metadata to log
        """
        try:
            # Build log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "symbol": order.get("symbol", "Unknown"),
                "strategy": order.get("strategy", "Unknown"),
                "strikes": order.get("strikes", []),
                "expiry": order.get("expiry", ""),
                "premium": order.get("premium", 0),
                "risk": order.get("risk", 0),
                "reward": order.get("reward", 0),
                "win_probability": prediction_result.win_probability if prediction_result else 0,
                "confidence": prediction_result.confidence if prediction_result else 0,
                "prediction_time_ms": prediction_result.prediction_time_ms if prediction_result else 0,
                "features_used": prediction_result.features_used if prediction_result else 0,
                "threshold": threshold,
                "approved": (prediction_result.win_probability >= threshold) if prediction_result else False,
                "model_version": prediction_result.model_version if prediction_result else "unknown"
            }
            
            # Add metadata if provided
            if metadata:
                log_entry["metadata"] = metadata
            
            # Write to file (thread-safe)
            async with self._lock:
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
                    
            logger.debug(f"Logged prediction for {order.get('symbol')} {order.get('strategy')}")
            
        except Exception as e:
            logger.error(f"Failed to log prediction: {e}")
    
    async def log_error(
        self,
        order: Dict[str, Any],
        error: Exception,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a prediction error."""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "symbol": order.get("symbol", "Unknown"),
                "strategy": order.get("strategy", "Unknown"),
                "error": str(error),
                "error_type": type(error).__name__,
                "approved": False,
                "win_probability": 0,
                "confidence": 0
            }
            
            if metadata:
                log_entry["metadata"] = metadata
            
            async with self._lock:
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
                    
        except Exception as e:
            logger.error(f"Failed to log error: {e}")


# Convenience decorator for automatic logging
def with_prediction_logging(log_file: str = "logs/predictions.jsonl"):
    """
    Decorator to automatically log predictions.
    
    Usage:
        @with_prediction_logging()
        async def predict_order(order):
            # Your prediction logic
            return prediction_result
    """
    def decorator(func):
        logger_instance = PredictionLogger(log_file)
        
        async def wrapper(order: Dict[str, Any], *args, **kwargs):
            try:
                # Call the prediction function
                result = await func(order, *args, **kwargs)
                
                # Log the prediction
                threshold = kwargs.get('threshold', 0.55)
                metadata = kwargs.get('metadata', {})
                await logger_instance.log_prediction(order, result, threshold, metadata)
                
                return result
                
            except Exception as e:
                # Log the error
                await logger_instance.log_error(order, e)
                raise
        
        return wrapper
    return decorator


# Example integration for DiscordTrading
class PredictionLoggingMiddleware:
    """
    Middleware that can be added to any prediction service to enable logging.
    
    Usage in DiscordTrading:
        # Add to your prediction pipeline
        prediction_logger = PredictionLoggingMiddleware()
        
        # In your prediction code
        result = await predictor.predict(order)
        await prediction_logger.log(order, result)
    """
    
    def __init__(self, log_file: str = "logs/predictions.jsonl", enabled: bool = True):
        self.logger = PredictionLogger(log_file) if enabled else None
        self.enabled = enabled
    
    async def log(
        self,
        order: Dict[str, Any],
        prediction_result: Any,
        threshold: float = 0.55,
        **kwargs
    ):
        """Log a prediction if logging is enabled."""
        if self.enabled and self.logger:
            await self.logger.log_prediction(order, prediction_result, threshold, kwargs)
    
    async def log_batch(
        self,
        predictions: list,
        threshold: float = 0.55
    ):
        """Log multiple predictions."""
        if self.enabled and self.logger:
            for order, result in predictions:
                await self.logger.log_prediction(order, result, threshold)


# Standalone logging function for simple integrations
async def log_prediction_simple(
    order: Dict[str, Any],
    win_probability: float,
    confidence: float = 0.0,
    latency_ms: float = 0.0,
    approved: bool = None,
    threshold: float = 0.55,
    log_file: str = "logs/predictions.jsonl"
):
    """
    Simple function to log a prediction without a full result object.
    
    Usage:
        await log_prediction_simple(
            order={"symbol": "SPX", "strategy": "Butterfly"},
            win_probability=0.72,
            confidence=0.85,
            latency_ms=125.3
        )
    """
    if approved is None:
        approved = win_probability >= threshold
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "symbol": order.get("symbol", "Unknown"),
        "strategy": order.get("strategy", "Unknown"),
        "win_probability": win_probability,
        "confidence": confidence,
        "prediction_time_ms": latency_ms,
        "threshold": threshold,
        "approved": approved,
        "strikes": order.get("strikes", []),
        "premium": order.get("premium", 0),
        "risk": order.get("risk", 0),
        "reward": order.get("reward", 0)
    }
    
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


if __name__ == "__main__":
    # Example usage
    async def test_logging():
        # Create logger
        logger = PredictionLogger()
        
        # Mock order
        test_order = {
            "symbol": "SPX",
            "strategy": "Butterfly",
            "strikes": [5900, 5910, 5920],
            "premium": 1.50,
            "risk": 10.0,
            "reward": 90.0
        }
        
        # Mock prediction result
        class MockResult:
            win_probability = 0.723
            confidence = 0.856
            prediction_time_ms = 125.3
            features_used = 67
            model_version = "test-1.0"
        
        # Log prediction
        await logger.log_prediction(test_order, MockResult())
        print(f"✓ Logged test prediction to {logger.log_file}")
        
        # Test simple logging
        await log_prediction_simple(
            order={"symbol": "SPY", "strategy": "Iron Condor"},
            win_probability=0.82,
            confidence=0.90,
            latency_ms=95.2
        )
        print("✓ Logged simple prediction")
    
    # Run test
    asyncio.run(test_logging())
