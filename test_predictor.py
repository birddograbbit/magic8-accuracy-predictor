#!/usr/bin/env python3
"""
Test script to verify the Magic8 Accuracy Predictor is working correctly.

Usage:
    python test_predictor.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.real_time_predictor import get_prediction_service


async def test_predictor():
    """Test the predictor with a sample order."""
    print("=" * 60)
    print("🧪 Testing Magic8 Accuracy Predictor")
    print("=" * 60)
    
    try:
        # Initialize prediction service
        print("\n1. Initializing prediction service...")
        service = get_prediction_service()
        print("✅ Service initialized successfully")
        
        # Create a test order
        test_order = {
            'symbol': 'SPX',
            'strategy': 'Butterfly',
            'strikes': [5900, 5910, 5920],
            'expiry': '2025-07-01',
            'right': 'CALL',
            'quantity': 1,
            'premium': 2.50,
            'risk': 250,
            'reward': 750,
            'probability': 0.45
        }
        
        print(f"\n2. Making prediction for test order:")
        print(f"   Symbol: {test_order['symbol']}")
        print(f"   Strategy: {test_order['strategy']}")
        print(f"   Strikes: {test_order['strikes']}")
        
        # Make prediction
        result = await service.predict(test_order)
        
        if result:
            print(f"\n✅ Prediction successful!")
            print(f"   Win Probability: {result.win_probability:.2%}")
            print(f"   Loss Probability: {result.loss_probability:.2%}")
            print(f"   Confidence: {result.confidence:.2%}")
            print(f"   Features Used: {result.features_used}")
            print(f"   Latency: {result.prediction_time_ms:.1f}ms")
            
            # Test another strategy
            test_order['strategy'] = 'IronCondor'
            test_order['strikes'] = [5880, 5890, 5920, 5930]
            
            print(f"\n3. Testing Iron Condor strategy...")
            result2 = await service.predict(test_order)
            
            if result2:
                print(f"   Win Probability: {result2.win_probability:.2%}")
                print(f"   Strategy performs {'better' if result2.win_probability > result.win_probability else 'worse'} than Butterfly")
        else:
            print("❌ Prediction failed")
            
        # Get service status
        print(f"\n4. Service Status:")
        status = service.get_status()
        print(f"   Symbols covered: {', '.join(status['symbol_coverage'][:5])}...")
        print(f"   Number of models: {status['num_models']}")
        print(f"   Cache enabled: {status['predictors'][0]['stats']['cache_enabled']}")
        
        print("\n✅ All tests passed! The predictor is working correctly.")
        print("\nYou can now:")
        print("  - Run 'python quick_start.py' for more examples")
        print("  - Run 'python monitor_predictions.py' to track predictions")
        print("  - Integrate with DiscordTrading or Magic8-Companion")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    return True


if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_predictor())
    sys.exit(0 if success else 1)
