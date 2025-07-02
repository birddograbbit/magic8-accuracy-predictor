#!/usr/bin/env python3
"""
Enhanced startup script for Magic8 Prediction API
Includes pre-flight checks and better error handling
"""

import os
import sys
import subprocess
import time
import socket
from pathlib import Path

def check_port_available(port):
    """Check if a port is available."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result != 0

def check_ibkr_gateway():
    """Check if IBKR Gateway is running."""
    if check_port_available(7497):
        print("⚠️  IBKR Gateway not detected on port 7497")
        print("   Please start IBKR Gateway/TWS first")
        return False
    print("✓ IBKR Gateway detected on port 7497")
    return True

def check_model_file():
    """Check if model file exists."""
    model_path = Path("models/xgboost_phase1_model.pkl")
    if not model_path.exists():
        print(f"⚠️  Model file not found: {model_path}")
        alt_paths = [
            "models/xgboost_phase1.pkl",
            "models/phase1/xgboost_model.pkl"
        ]
        for alt in alt_paths:
            if Path(alt).exists():
                print(f"   Found alternative at: {alt}")
                print(f"   Consider copying to: {model_path}")
                break
        return False
    print(f"✓ Model file found: {model_path}")
    return True

def check_feature_config():
    """Check if feature config exists."""
    config_path = Path("data/phase1_processed/feature_info.json")
    if not config_path.exists():
        print(f"⚠️  Feature config not found: {config_path}")
        return False
    print(f"✓ Feature config found: {config_path}")
    return True

def main():
    """Run pre-flight checks and start the API."""
    print("Magic8 Prediction API - Pre-flight Checks")
    print("=" * 50)
    
    # Check working directory
    if not Path("src/prediction_api.py").exists():
        print("❌ Error: Must run from magic8-accuracy-predictor directory")
        sys.exit(1)
    
    # Run checks
    checks_passed = True
    
    if not check_model_file():
        checks_passed = False
        
    if not check_feature_config():
        checks_passed = False
        
    if not check_ibkr_gateway():
        print("\n   You can still start the API, but it will use mock data only")
        response = input("   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    if not checks_passed:
        print("\n⚠️  Some checks failed. The API may not work correctly.")
        response = input("Start anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Check if API port is available
    if not check_port_available(8000):
        print("\n❌ Port 8000 is already in use")
        print("   Another instance may be running")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("Starting Magic8 Prediction API...")
    print("API will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop")
    print("=" * 50 + "\n")
    
    # Start the API
    try:
        # Run as a module to ensure proper imports
        subprocess.run([sys.executable, "-m", "src.prediction_api"], check=True)
    except KeyboardInterrupt:
        print("\n\nAPI stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ API failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
