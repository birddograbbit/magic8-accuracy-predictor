"""
Quick test script for real-time predictor.

Run this to verify the implementation is working:
    python test_real_time_predictor.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.real_time_predictor import get_prediction_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_prediction():
    """Test the prediction service with sample orders."""
    
    # Test orders
    test_orders = [
        {
            'symbol': 'SPX',
            'strategy': 'Butterfly',
            'strikes': [5900, 5910, 5920],
            'expiry': '2025-07-01',
            'right': 'CALL',
            'quantity': 1,
            'premium': 1.50,
            'risk': 10.0,
            'reward': 90.0
        },
        {
            'symbol': 'SPY',
            'strategy': 'Vertical',
            'strikes': [590, 595],
            'expiry': '2025-07-01',
            'right': 'CALL',
            'quantity': 5,
            'premium': 0.50,
            'risk': 5.0,
            'reward': 0.50
        },
        {
            'symbol': 'QQQ',
            'strategy': 'Iron Condor',
            'strikes': [485, 490, 500, 505],
            'expiry': '2025-07-01',
            'right': 'CALL/PUT',
            'quantity': 2,
            'premium': 0.75,
            'risk': 4.25,
            'reward': 0.75
        }
    ]
    
    try:
        # Get prediction service
        logger.info("Initializing prediction service...")
        service = get_prediction_service()
        
        # Check service status
        status = service.get_status()
        logger.info(f"Service status: {status}")
        
        # Warmup
        logger.info("Warming up predictors...")
        await service.warmup_all()
        
        # Test predictions
        logger.info("\nTesting predictions...")
        for order in test_orders:
            logger.info(f"\nPredicting for: {order['symbol']} {order['strategy']}")
            
            try:
                result = await service.predict(order)
                
                if result:
                    logger.info(f"  Win probability: {result.win_probability:.2%}")
                    logger.info(f"  Confidence: {result.confidence:.2%}")
                    logger.info(f"  Latency: {result.prediction_time_ms:.1f}ms")
                    logger.info(f"  Features used: {result.features_used}")
                else:
                    logger.warning(f"  No predictor available for {order['symbol']}")
                    
            except Exception as e:
                logger.error(f"  Prediction failed: {e}")
        
        # Final status
        logger.info("\nFinal service status:")
        for predictor_info in service.get_status()['predictors']:
            stats = predictor_info['stats']
            logger.info(f"  Model: {predictor_info['model_path']}")
            logger.info(f"    Total predictions: {stats['total_predictions']}")
            logger.info(f"    Average latency: {stats['average_latency_ms']:.1f}ms")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


async def test_data_providers():
    """Test different data provider configurations."""
    logger.info("\nTesting data providers...")
    
    from src.data_providers import (
        CompanionDataProvider,
        RedisDataProvider,
        StandaloneDataProvider,
        FallbackDataProvider
    )
    
    # Test companion provider
    logger.info("\n1. Testing CompanionDataProvider...")
    companion = CompanionDataProvider()
    if await companion.connect():
        logger.info("   Connected to Magic8-Companion")
        health = await companion.health_check()
        logger.info(f"   Health: {health['status']}")
    else:
        logger.warning("   Failed to connect to Magic8-Companion")
    
    # Test Redis provider
    logger.info("\n2. Testing RedisDataProvider...")
    redis = RedisDataProvider()
    if await redis.connect():
        logger.info("   Connected to Redis")
        health = await redis.health_check()
        logger.info(f"   Health: {health['status']}")
    else:
        logger.warning("   Failed to connect to Redis")
    
    # Test fallback
    logger.info("\n3. Testing FallbackDataProvider...")
    fallback = FallbackDataProvider(companion, redis)
    if await fallback.connect():
        logger.info("   Fallback provider ready")
        health = await fallback.health_check()
        logger.info(f"   Health: {health}")
    
    # Cleanup
    await companion.disconnect()
    await redis.disconnect()
    await fallback.disconnect()


def main():
    """Main test function."""
    print("=" * 60)
    print("Magic8 Accuracy Predictor - Real-Time Test")
    print("=" * 60)
    
    # Check for model file
    model_path = Path("models/xgboost_phase1_model.pkl")
    if not model_path.exists():
        logger.warning(
            f"Model file not found at {model_path}. "
            "Using mock mode for testing."
        )
        # Create mock model file for testing
        model_path.parent.mkdir(exist_ok=True)
        import joblib
        import numpy as np
        
        # Create dummy model
        class MockModel:
            def predict_proba(self, X):
                # Random predictions for testing
                probs = np.random.rand(len(X), 2)
                probs = probs / probs.sum(axis=1, keepdims=True)
                return probs
            
            version = "mock-1.0.0"
        
        joblib.dump(MockModel(), model_path)
        logger.info("Created mock model for testing")
    
    # Run tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Test data providers
        loop.run_until_complete(test_data_providers())
        
        # Test predictions
        loop.run_until_complete(test_prediction())
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        loop.close()


if __name__ == "__main__":
    main()
