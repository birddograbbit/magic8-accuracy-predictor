#!/usr/bin/env python3
"""
Start the simplified prediction API with proper IB connection.
"""

import os
import sys
import subprocess
import socket
import time

def check_port(port):
    """Check if a port is in use."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('127.0.0.1', port))
        sock.close()
        return True
    except:
        return False

def main():
    print("Magic8 Prediction API (Simplified) - Startup")
    print("=" * 50)
    
    # Check for required files
    model_path = 'models/xgboost_phase1_model.pkl'
    if os.path.exists(model_path):
        print(f"✓ Model found: {model_path}")
    else:
        print(f"✗ Model not found: {model_path}")
        print("  Please ensure the model file exists")
        
    feature_path = 'data/phase1_processed/feature_info.json'
    if os.path.exists(feature_path):
        print(f"✓ Feature config found: {feature_path}")
    else:
        print(f"✗ Feature config not found: {feature_path}")
        print("  Please ensure the feature config exists")
        
    # Check IB Gateway
    if check_port(7497):
        print("✓ IB Gateway detected on port 7497")
    else:
        print("✗ IB Gateway not detected on port 7497")
        print("  Please start IB Gateway/TWS first")
        
    print("\n" + "=" * 50)
    print("Starting API server...")
    print("API will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop")
    print("=" * 50 + "\n")
    
    # Start the API
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "src.simple_ib.prediction_api_simple:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\nShutting down...")

if __name__ == "__main__":
    main()
