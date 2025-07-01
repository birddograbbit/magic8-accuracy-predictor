#!/usr/bin/env python3
"""
Convert XGBoost model from native format to joblib format for real-time predictor.
This creates a wrapper that the real-time predictor can use.

Usage:
    python prepare_model_for_predictor.py
"""

import xgboost as xgb
import joblib
import json
import os
from pathlib import Path
import shutil

# Determine repository root so paths work regardless of current working dir
REPO_ROOT = Path(__file__).resolve().parent

# Import the model wrapper from the proper location
from src.models.model_wrappers import XGBoostModelWrapper


def convert_model():
    """Convert XGBoost model to joblib format."""
    
    # Paths
    model_dir = REPO_ROOT / 'models' / 'phase1'
    json_model_path = model_dir / 'xgboost_baseline.json'
    metadata_path = model_dir / 'model_metadata.json'
    scaler_path = model_dir / 'scaler.pkl'
    output_path = model_dir / 'xgboost_model.pkl'
    
    print(f"Converting XGBoost model for real-time predictor...")
    
    # Check if source files exist
    if not json_model_path.exists():
        print(f"❌ Model file not found: {json_model_path}")
        print("Please run 'python src/models/xgboost_baseline.py' first to train the model.")
        return False
    
    if not metadata_path.exists():
        print(f"❌ Metadata file not found: {metadata_path}")
        return False
    
    try:
        # Load the XGBoost model
        print(f"Loading XGBoost model from {json_model_path}")
        booster = xgb.Booster()
        booster.load_model(str(json_model_path))
        
        # Load metadata
        print(f"Loading metadata from {metadata_path}")
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        feature_names = metadata['feature_names']
        print(f"Found {len(feature_names)} features")
        
        # Load scaler if exists
        scaler = None
        if scaler_path.exists():
            print(f"Loading scaler from {scaler_path}")
            scaler = joblib.load(scaler_path)
        
        # Create wrapper
        print("Creating model wrapper...")
        wrapped_model = XGBoostModelWrapper(booster, feature_names, scaler)
        
        # Save as joblib
        print(f"Saving wrapped model to {output_path}")
        joblib.dump(wrapped_model, output_path)
        
        # Also copy to root models directory for backward compatibility
        root_model_path = REPO_ROOT / 'models' / 'xgboost_phase1_model.pkl'
        print(f"Creating copy at {root_model_path}")
        shutil.copy2(output_path, root_model_path)
        
        print("✅ Model conversion successful!")
        print(f"\nModel saved to:")
        print(f"  - {output_path}")
        print(f"  - {root_model_path}")
        
        # Test the model
        print("\nTesting model loading...")
        test_model = joblib.load(output_path)
        print(f"✓ Model loaded successfully")
        print(f"✓ Model version: {test_model.version}")
        print(f"✓ Number of features: {len(test_model.feature_names)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error converting model: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    # Create models directory if it doesn't exist
    (REPO_ROOT / 'models').mkdir(exist_ok=True)
    (REPO_ROOT / 'models' / 'phase1').mkdir(exist_ok=True)
    
    # Convert the model
    success = convert_model()
    
    if success:
        print("\n🎉 Model is ready for real-time predictions!")
        print("\nYou can now run:")
        print("  python quick_start.py")
    else:
        print("\n❌ Model conversion failed")
        print("\nMake sure you've trained the model first:")
        print("  python src/phase1_data_preparation.py")
        print("  python src/models/xgboost_baseline.py")


if __name__ == "__main__":
    main()
