#!/usr/bin/env python3
"""
Test the fixed API to verify predictions vary with different inputs.
"""

import requests
import json

API_URL = "http://localhost:8000"

def test_predictions():
    """Test different trade configurations to verify predictions vary."""
    
    test_trades = [
        {
            "strategy": "Butterfly",
            "symbol": "SPX",
            "premium": 33.6,
            "predicted_price": 6255
        },
        {
            "strategy": "Butterfly", 
            "symbol": "SPX",
            "premium": 27.63,
            "predicted_price": 6220
        },
        {
            "strategy": "Butterfly",
            "symbol": "SPX", 
            "premium": 36.45,
            "predicted_price": 6170
        },
        {
            "strategy": "Iron Condor",
            "symbol": "SPX",
            "premium": 12.50,
            "predicted_price": 5850
        },
        {
            "strategy": "Vertical",
            "symbol": "SPX",
            "premium": 5.00,
            "predicted_price": 5900
        }
    ]
    
    print("🧪 Testing Fixed Prediction API")
    print("=" * 50)
    
    # Check if API is running
    try:
        resp = requests.get(f"{API_URL}/health")
        if resp.status_code != 200:
            print("❌ API not running! Start it with: ./run_fixed_api.sh")
            return
        health = resp.json()
        print(f"✅ API Status: {health['status']}")
        print(f"   Model: {health['components']['model']}")
        print(f"   Features: {health['components']['features']}")
        print()
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("   Start it with: ./run_fixed_api.sh")
        return
    
    # Test predictions
    predictions = []
    for i, trade in enumerate(test_trades):
        try:
            resp = requests.post(f"{API_URL}/predict", json=trade)
            if resp.status_code == 200:
                result = resp.json()
                win_prob = result['win_probability']
                predictions.append(win_prob)
                
                print(f"Test {i+1}: {trade['strategy']} @ ${trade['premium']}")
                print(f"   Predicted Price: {trade['predicted_price']}")
                print(f"   Win Probability: {win_prob:.1%}")
                print(f"   Recommendation: {result['recommendation']}")
                print()
            else:
                print(f"❌ Error: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    # Check if predictions vary
    if len(set(predictions)) == 1:
        print("⚠️  WARNING: All predictions are the same!")
        print("   The feature calculation may still have issues.")
    else:
        print("✅ SUCCESS: Predictions vary based on input!")
        print(f"   Unique predictions: {len(set(predictions))}")
        print(f"   Range: {min(predictions):.1%} to {max(predictions):.1%}")

if __name__ == "__main__":
    test_predictions()
