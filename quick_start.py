#!/usr/bin/env python3
"""
Quick Start Script for Magic8 Accuracy Predictor

This script helps you get started with the implementation:
1. Sets up the environment
2. Tests data loading
3. Runs initial data preparation
"""

import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is 3.7+"""
    if sys.version_info < (3, 7):
        print("Error: Python 3.7+ is required")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} detected")

def install_dependencies():
    """Install required packages"""
    print("\nInstalling dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("Error: Failed to install dependencies")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)

def test_data_loading():
    """Test if we can load the normalized data"""
    print("\nTesting data loading...")
    try:
        import pandas as pd
        df = pd.read_csv('data/normalized/normalized_aggregated.csv')
        print(f"✓ Successfully loaded {len(df)} records")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        
        # Check for required columns
        required_cols = ['interval_datetime', 'pred_price', 'trad_profited']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"Warning: Missing columns: {missing_cols}")
        else:
            print("✓ All required columns present")
            
    except FileNotFoundError:
        print("Error: normalized_aggregated.csv not found")
        print("Please run normalize_data.py first")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

def run_data_preparation():
    """Run the data preparation pipeline"""
    print("\nRunning data preparation pipeline...")
    try:
        # Add src to path
        sys.path.insert(0, 'src')
        from data_preparation import DataPreparation
        
        prep = DataPreparation()
        train_data, val_data, test_data = prep.run_pipeline()
        
        print("\n✓ Data preparation completed successfully!")
        print(f"\nData splits created in data/processed/:")
        print(f"  - train_data.csv: {len(train_data)} samples")
        print(f"  - val_data.csv: {len(val_data)} samples")
        print(f"  - test_data.csv: {len(test_data)} samples")
        
    except Exception as e:
        print(f"Error in data preparation: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you have internet connection (for VIX data)")
        print("2. Check if all dependencies are installed")
        print("3. Verify data/normalized/normalized_aggregated.csv exists")

def main():
    """Main execution"""
    print("=" * 60)
    print("Magic8 Accuracy Predictor - Quick Start")
    print("=" * 60)
    
    # Check Python version
    check_python_version()
    
    # Test data loading first
    test_data_loading()
    
    # Ask user if they want to install dependencies
    response = input("\nInstall/update dependencies? (y/n): ").lower()
    if response == 'y':
        install_dependencies()
    
    # Ask user if they want to run data preparation
    response = input("\nRun data preparation pipeline? (y/n): ").lower()
    if response == 'y':
        run_data_preparation()
    
    print("\n" + "=" * 60)
    print("Next steps:")
    print("1. Review IMPLEMENTATION_PLAN.md for detailed architecture")
    print("2. Explore the processed data in data/processed/")
    print("3. Clone QuantStock repository for model implementation")
    print("4. Start developing the binary classification models")
    print("=" * 60)

if __name__ == "__main__":
    main()
