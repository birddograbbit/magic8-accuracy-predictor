#!/usr/bin/env python3
"""
Quick Start Script for Magic8 Accuracy Predictor
Get your first real-time prediction in minutes!

Usage:
    python quick_start.py
"""

import asyncio
import sys
import os
from pathlib import Path
import logging
import joblib
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def check_prerequisites():
    """Check if all requirements are met."""
    issues = []
    
    # Check for trained model
    model_paths = [
        'models/xgboost_phase1_model.pkl',
        'models/phase1/xgboost_baseline.json',
        'models/xgboost_model.pkl'
    ]
    
    model_found = False
    for path in model_paths:
        if Path(path).exists():
            model_found = True
            logger.info(f"✓ Found model at: {path}")
            break
    
    if not model_found:
        issues.append("No trained model found")
        logger.warning("✗ No trained model found. You need to train the Phase 1 model first.")
        logger.info("\nTo train the model:")
        logger.info("1. Download IBKR data: ./download_phase1_data.sh")
        logger.info("2. Process data: python src/phase1_data_preparation.py")
        logger.info("3. Train model: python src/models/xgboost_baseline.py")
    
    # Check for config
    if not Path('config/config.yaml').exists():
        issues.append("Config file missing")
        logger.warning("✗ Config file missing")
    else:
        logger.info("✓ Config file found")
        import yaml
        with open('config/config.yaml') as f:
            cfg = yaml.safe_load(f)
        provider = cfg.get('data_source', {}).get('primary', 'unknown')
        logger.info(f"✓ Primary data provider: {provider}")
    
    # Check for data providers
    if not Path('src/data_providers').exists():
        issues.append("Data providers missing")
        logger.warning("✗ Data providers missing")
    else:
        logger.info("✓ Data providers found")
    
    return len(issues) == 0, issues


async def create_mock_model():
    """Create a mock model for testing."""
    logger.info("\nCreating mock model for testing...")
    
    # Create models directory
    Path('models').mkdir(exist_ok=True)
    
    # Create a simple mock model
    class MockXGBoostModel:
        def predict_proba(self, X):
            # Generate realistic-looking probabilities
            base_prob = 0.45 + np.random.rand(len(X)) * 0.3
            probs = np.column_stack([1 - base_prob, base_prob])
            return probs
        
        def get_booster(self):
            return self
        
        def get_score(self, importance_type='gain'):
            # Mock feature importance
            return {
                'price_momentum_5': 100,
                'vix_level': 85,
                'rsi_14': 70,
                'minutes_to_close': 65,
                'price_sma_20': 60
            }
        
        version = "mock-1.0.0"
    
    # Save the mock model
    model_path = Path('models/xgboost_phase1_model.pkl')
    joblib.dump(MockXGBoostModel(), model_path)
    logger.info(f"✓ Created mock model at: {model_path}")
    
    return model_path


async def test_data_providers():
    """Test available data providers."""
    logger.info("\n" + "="*60)
    logger.info("Testing Data Providers")
    logger.info("="*60)
    
    from src.data_providers import CompanionDataProvider
    
    # Test companion provider
    logger.info("\nTesting Magic8-Companion connection...")
    companion = CompanionDataProvider()
    
    try:
        if await companion.connect():
            logger.info("✓ Connected to Magic8-Companion")
            
            # Test getting market data
            data = await companion.get_market_data('SPX')
            if data:
                logger.info(f"✓ Got SPX price: ${data.get('price', 'N/A')}")
            else:
                logger.info("✗ No market data available (market may be closed)")
        else:
            logger.info("✗ Could not connect to Magic8-Companion")
            logger.info("  Make sure Magic8-Companion is running with API enabled:")
            logger.info("  export M8C_ENABLE_DATA_API=true")
            logger.info("  python -m magic8_companion")
    except Exception as e:
        logger.error(f"✗ Error testing companion provider: {e}")
    finally:
        await companion.disconnect()


async def make_first_prediction():
    """Make your first prediction!"""
    logger.info("\n" + "="*60)
    logger.info("Making First Prediction")
    logger.info("="*60)
    
    from src.real_time_predictor import get_prediction_service
    
    # Initialize prediction service
    logger.info("\nInitializing prediction service...")
    service = get_prediction_service()
    
    # Example order (typical Magic8 trade)
    test_order = {
        'symbol': 'SPX',
        'strategy': 'Butterfly',
        'strikes': [5900, 5910, 5920],
        'expiry': '2025-07-01',
        'right': 'CALL',
        'quantity': 1,
        'premium': 1.50,
        'risk': 10.0,
        'reward': 90.0,
        'trade_prob': 0.70  # 70% probability from Magic8
    }
    
    logger.info(f"\nTest Order:")
    logger.info(f"  Symbol: {test_order['symbol']}")
    logger.info(f"  Strategy: {test_order['strategy']}")
    logger.info(f"  Strikes: {test_order['strikes']}")
    logger.info(f"  Risk/Reward: ${test_order['risk']:.2f}/${test_order['reward']:.2f}")
    
    try:
        # Make prediction
        logger.info("\nMaking prediction...")
        result = await service.predict(test_order)
        
        if result:
            logger.info("\n🎯 PREDICTION RESULTS:")
            logger.info(f"  Win Probability: {result.win_probability:.1%}")
            logger.info(f"  Confidence: {result.confidence:.1%}")
            logger.info(f"  Features Used: {result.features_used}")
            logger.info(f"  Latency: {result.prediction_time_ms:.0f}ms")
            
            # Trading decision
            min_prob = 0.55  # From config
            if result.win_probability >= min_prob:
                logger.info(f"\n✅ TRADE APPROVED (>= {min_prob:.0%})")
            else:
                logger.info(f"\n❌ TRADE REJECTED (< {min_prob:.0%})")
        else:
            logger.warning("\n⚠️  No prediction available")
            
    except Exception as e:
        logger.error(f"\n❌ Prediction failed: {e}")
        logger.info("\nTroubleshooting tips:")
        logger.info("1. Make sure you have a trained model")
        logger.info("2. Check that data providers are configured")
        logger.info("3. Verify Magic8-Companion is running (if using companion provider)")


async def show_next_steps():
    """Show next steps for integration."""
    logger.info("\n" + "="*60)
    logger.info("Next Steps")
    logger.info("="*60)
    
    logger.info("\n1. To get real predictions with actual data:")
    logger.info("   - Train the Phase 1 model (see instructions above)")
    logger.info("   - Start Magic8-Companion with API enabled")
    logger.info("   - Run this script again")
    
    logger.info("\n2. To integrate with DiscordTrading:")
    logger.info("   - Copy integration files: python integrate_discord_trading.py")
    logger.info("   - Update DiscordTrading config")
    logger.info("   - Restart DiscordTrading")
    
    logger.info("\n3. For production deployment:")
    logger.info("   - Review docs/REAL_TIME_INTEGRATION_PLAN.md")
    logger.info("   - Set up monitoring")
    logger.info("   - Configure appropriate thresholds")


async def main():
    """Main function."""
    print("\n" + "="*60)
    print("🎱 Magic8 Accuracy Predictor - Quick Start")
    print("="*60)
    
    # Check prerequisites
    ready, issues = check_prerequisites()
    
    if not ready:
        logger.info("\n⚠️  Some prerequisites are missing:")
        for issue in issues:
            logger.info(f"  - {issue}")
        
        # Ask if user wants to continue with mock
        response = input("\nWould you like to continue with a mock model for testing? (y/n): ")
        if response.lower() != 'y':
            logger.info("\nExiting. Please set up the prerequisites first.")
            return
        
        # Create mock model
        await create_mock_model()
    
    # Test data providers
    await test_data_providers()
    
    # Make first prediction
    await make_first_prediction()
    
    # Show next steps
    await show_next_steps()
    
    logger.info("\n✨ Quick start completed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        raise
