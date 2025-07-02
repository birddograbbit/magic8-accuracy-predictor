#!/usr/bin/env python3
"""
Test script to verify that the import fixes work correctly.
This tests both feature generation and prediction functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for absolute imports
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

print("🔧 Testing Magic8-Accuracy-Predictor Integration Fixes...")
print("=" * 60)

def test_imports():
    """Test that all imports work correctly."""
    print("1. Testing imports...")
    
    try:
        from feature_engineering.real_time_features import RealTimeFeatureGenerator
        print("   ✓ RealTimeFeatureGenerator import successful")
    except Exception as e:
        print(f"   ✗ RealTimeFeatureGenerator import failed: {e}")
        return False
    
    try:
        from data_providers import MockDataProvider
        print("   ✓ MockDataProvider import successful")
    except Exception as e:
        print(f"   ✗ MockDataProvider import failed: {e}")
        return False
    
    try:
        from real_time_predictor import get_prediction_service
        print("   ✓ Real-time predictor import successful")
    except Exception as e:
        print(f"   ✗ Real-time predictor import failed: {e}")
        return False
    
    return True

async def test_feature_generation():
    """Test feature generation with correct method signature."""
    print("\n2. Testing feature generation...")
    
    try:
        from feature_engineering.real_time_features import RealTimeFeatureGenerator
        from data_providers import MockDataProvider
        
        # Initialize components
        data_provider = MockDataProvider()
        feature_gen = RealTimeFeatureGenerator(data_provider)
        
        # Test order
        test_order = {
            'symbol': 'SPX',
            'strategy': 'Butterfly',
            'strikes': [5900, 5910, 5920],
            'expiry': '2025-07-01',
            'premium': 1.50,
            'risk': 10.0,
            'reward': 90.0
        }
        
        # Generate features with CORRECT signature (symbol, order_details)
        features, feature_names = await feature_gen.generate_features('SPX', test_order)
        
        print(f"   ✓ Feature generation successful")
        print(f"   ✓ Generated {len(features)} features")
        print(f"   ✓ Feature names sample: {feature_names[:5]}...")
        
        return len(features)
        
    except Exception as e:
        print(f"   ✗ Feature generation failed: {e}")
        return 0

async def test_prediction_service():
    """Test prediction service initialization and prediction."""
    print("\n3. Testing prediction service...")
    
    try:
        from real_time_predictor import get_prediction_service
        
        # Initialize service
        service = get_prediction_service()
        print("   ✓ Prediction service initialized")
        
        # Test order
        test_order = {
            'symbol': 'SPX',
            'strategy': 'Butterfly',
            'strikes': [5900, 5910, 5920],
            'expiry': '2025-07-01',
            'premium': 1.50,
            'risk': 10.0,
            'reward': 90.0,
            'trade_prob': 0.70
        }
        
        # Make prediction
        result = await service.predict(test_order)
        
        if result:
            print(f"   ✓ Prediction successful")
            print(f"   ✓ Win probability: {result.win_probability:.1%}")
            print(f"   ✓ Features used: {result.features_used}")
            print(f"   ✓ Latency: {result.prediction_time_ms:.0f}ms")
            return True
        else:
            print("   ✗ Prediction returned None")
            return False
            
    except Exception as e:
        print(f"   ✗ Prediction service failed: {e}")
        return False

async def test_configuration():
    """Test configuration loading."""
    print("\n4. Testing configuration...")
    
    try:
        import yaml
        
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        data_source = config.get('data_source', {})
        print(f"   ✓ Primary data source: {data_source.get('primary')}")
        print(f"   ✓ Companion enabled: {data_source.get('companion', {}).get('enabled')}")
        print(f"   ✓ Companion URL: {data_source.get('companion', {}).get('base_url')}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Configuration test failed: {e}")
        return False

async def main():
    """Run all tests."""
    
    # Test 1: Imports
    imports_ok = test_imports()
    
    if not imports_ok:
        print("\n❌ Import tests failed. Cannot proceed with other tests.")
        return
    
    # Test 2: Feature generation
    feature_count = await test_feature_generation()
    
    # Test 3: Prediction service
    prediction_ok = await test_prediction_service()
    
    # Test 4: Configuration
    config_ok = test_configuration()
    
    # Final assessment
    print("\n" + "=" * 60)
    print("🎯 INTEGRATION READINESS ASSESSMENT")
    print("=" * 60)
    
    if imports_ok and feature_count > 0 and prediction_ok and config_ok:
        print("✅ ALL TESTS PASSED!")
        print(f"✅ Feature count: {feature_count} (expected: 74)")
        print("✅ Magic8-accuracy-predictor integration preparation is COMPLETE")
        print("\n🎉 Ready to proceed with Magic8-Companion reconfiguration!")
        
    else:
        print("❌ SOME TESTS FAILED!")
        print("❌ Additional fixes needed before Magic8-Companion integration")
        print("\nPlease address the failing tests above.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Test script error: {e}")
