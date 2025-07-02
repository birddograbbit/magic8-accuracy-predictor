#!/usr/bin/env python3
"""Test script to verify model file and configuration."""

import os
import joblib
import json

def test_model_files():
    """Test that model and config files exist and can be loaded."""
    print("Testing model and configuration files...\n")
    
    # Test model file
    model_paths = [
        'models/xgboost_phase1_model.pkl',
        'models/xgboost_phase1.pkl',
        'models/phase1/xgboost_model.pkl'
    ]
    
    model_found = False
    for path in model_paths:
        if os.path.exists(path):
            print(f"✓ Found model at: {path}")
            try:
                model = joblib.load(path)
                print(f"  Model type: {type(model).__name__}")
                if hasattr(model, 'n_features_in_'):
                    print(f"  Features expected: {model.n_features_in_}")
                model_found = True
                break
            except Exception as e:
                print(f"  ✗ Error loading model: {e}")
    
    if not model_found:
        print("✗ No model file found!")
    
    # Test feature config
    print("\nTesting feature configuration...")
    config_path = 'data/phase1_processed/feature_info.json'
    
    if os.path.exists(config_path):
        print(f"✓ Found feature config at: {config_path}")
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            print(f"  Number of features: {len(config.get('feature_names', []))}")
            print(f"  Sample features: {config.get('feature_names', [])[:5]}")
        except Exception as e:
            print(f"  ✗ Error loading config: {e}")
    else:
        print(f"✗ Feature config not found at: {config_path}")

if __name__ == "__main__":
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    test_model_files()
