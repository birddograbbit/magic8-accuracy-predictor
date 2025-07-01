#!/usr/bin/env python3
"""
Helper script to check and set up Magic8-Companion API.
This ensures Magic8-Companion is configured to provide data to the predictor.

Usage:
    python setup_companion_api.py [--companion-path /path/to/Magic8-Companion]
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse
import requests
import time


def find_companion_path():
    """Try to find Magic8-Companion path automatically."""
    possible_paths = [
        Path.home() / "Magic8-Companion",
        Path.home() / "projects" / "Magic8-Companion",
        Path.home() / "code" / "Magic8-Companion",
        Path("..") / "Magic8-Companion",
        Path("../..") / "Magic8-Companion"
    ]
    
    for path in possible_paths:
        if path.exists() and (path / "magic8_companion.py").exists():
            return path
    
    return None


def check_companion_running():
    """Check if Magic8-Companion is already running."""
    try:
        response = requests.get("http://localhost:8765/health", timeout=2)
        if response.status_code == 200:
            return True
    except:
        pass
    return False


def create_api_endpoints(companion_path):
    """Create API endpoints file for Magic8-Companion."""
    api_content = '''"""
API endpoints for Magic8-Companion to serve market data.
Add this to Magic8-Companion to enable data sharing with the predictor.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from typing import Dict, Any, Optional
import logging
import uvicorn

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Magic8-Companion Data API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Reference to companion instance (set by companion)
companion_instance = None


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Magic8-Companion",
        "api_version": "1.0.0"
    }


@app.get("/market/{symbol}")
async def get_market_data(symbol: str):
    """Get current market data for a symbol."""
    if not companion_instance:
        raise HTTPException(status_code=503, detail="Companion not initialized")
    
    try:
        # Get market data from IB connection
        contract = companion_instance.ib_manager.create_contract(symbol)
        ticker = companion_instance.ib_manager.ib.reqMktData(contract)
        
        # Wait briefly for data
        await asyncio.sleep(0.5)
        
        return {
            "symbol": symbol,
            "price": ticker.last if ticker.last else ticker.close,
            "bid": ticker.bid,
            "ask": ticker.ask,
            "volume": ticker.volume,
            "timestamp": ticker.time
        }
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vix")
async def get_vix_data():
    """Get current VIX data."""
    return await get_market_data("VIX")


@app.get("/option_chain/{symbol}")
async def get_option_chain(symbol: str, expiry: str):
    """Get option chain data."""
    if not companion_instance:
        raise HTTPException(status_code=503, detail="Companion not initialized")
    
    try:
        # This is a simplified version - expand based on your needs
        chains = companion_instance.ib_manager.ib.reqSecDefOptParams(
            symbol, "", "STK", 0
        )
        
        return {
            "symbol": symbol,
            "expiry": expiry,
            "chains": chains
        }
    except Exception as e:
        logger.error(f"Error getting option chain for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def start_api_server(companion, port=8765):
    """Start the API server."""
    global companion_instance
    companion_instance = companion
    
    logger.info(f"Starting API server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


# Add this to your Magic8-Companion main file:
# 
# if os.getenv('M8C_ENABLE_DATA_API', 'false').lower() == 'true':
#     from api_endpoints import start_api_server
#     import threading
#     api_thread = threading.Thread(
#         target=start_api_server, 
#         args=(self,), 
#         daemon=True
#     )
#     api_thread.start()
#     logger.info("Data API enabled on port 8765")
'''
    
    api_path = companion_path / "api_endpoints.py"
    api_path.write_text(api_content)
    print(f"✓ Created API endpoints file: {api_path.name}")
    
    return api_path


def create_start_script(companion_path):
    """Create a start script that enables the API."""
    script_content = '''#!/bin/bash
# Start Magic8-Companion with API enabled

echo "Starting Magic8-Companion with Data API enabled..."

# Enable API
export M8C_ENABLE_DATA_API=true

# Start companion
cd "$(dirname "$0")"
python -m magic8_companion "$@"
'''
    
    script_path = companion_path / "start_with_api.sh"
    script_path.write_text(script_content)
    script_path.chmod(0o755)  # Make executable
    print(f"✓ Created start script: {script_path.name}")
    
    return script_path


def show_manual_instructions():
    """Show manual integration instructions."""
    print("\n" + "="*60)
    print("Manual Integration Instructions")
    print("="*60)
    
    print("\n1. Add to Magic8-Companion's requirements.txt:")
    print("-"*40)
    print("fastapi>=0.100.0")
    print("uvicorn>=0.23.0")
    
    print("\n2. Add to magic8_companion.py main():")
    print("-"*40)
    print("""
# Enable data API if requested
if os.getenv('M8C_ENABLE_DATA_API', 'false').lower() == 'true':
    from api_endpoints import start_api_server
    import threading
    
    api_thread = threading.Thread(
        target=start_api_server,
        args=(companion,),
        daemon=True
    )
    api_thread.start()
    logger.info("Data API enabled on port 8765")
""")
    
    print("\n3. Start Magic8-Companion with API:")
    print("-"*40)
    print("export M8C_ENABLE_DATA_API=true")
    print("python -m magic8_companion")
    
    print("\n4. Test the API:")
    print("-"*40)
    print("curl http://localhost:8765/health")
    print("curl http://localhost:8765/market/SPX")


def test_companion_api():
    """Test if the API is working."""
    print("\nTesting Magic8-Companion API...")
    
    endpoints = [
        ("Health Check", "http://localhost:8765/health"),
        ("Market Data", "http://localhost:8765/market/SPX"),
        ("VIX Data", "http://localhost:8765/vix")
    ]
    
    working = 0
    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✓ {name}: Working")
                working += 1
            else:
                print(f"✗ {name}: Status {response.status_code}")
        except Exception as e:
            print(f"✗ {name}: {type(e).__name__}")
    
    return working > 0


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Set up Magic8-Companion API")
    parser.add_argument(
        '--companion-path',
        type=str,
        help='Path to Magic8-Companion directory'
    )
    parser.add_argument(
        '--test-only',
        action='store_true',
        help='Only test if API is working'
    )
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🎱 Magic8-Companion API Setup")
    print("="*60)
    
    # Test only mode
    if args.test_only:
        if test_companion_api():
            print("\n✅ API is working!")
        else:
            print("\n❌ API is not responding")
        return 0
    
    # Check if already running
    if check_companion_running():
        print("\n✓ Magic8-Companion is already running!")
        if test_companion_api():
            print("✓ API endpoints are working")
            return 0
        else:
            print("⚠️  But API endpoints are not responding")
            print("  Please restart with: export M8C_ENABLE_DATA_API=true")
    
    # Find companion path
    if args.companion_path:
        companion_path = Path(args.companion_path)
    else:
        companion_path = find_companion_path()
        
        if companion_path:
            print(f"✓ Found Magic8-Companion at: {companion_path}")
        else:
            print("❌ Could not find Magic8-Companion automatically")
            print("\nPlease either:")
            print("1. Specify path: python setup_companion_api.py --companion-path /path/to/Magic8-Companion")
            print("2. Or follow manual instructions below")
            show_manual_instructions()
            return 1
    
    if not companion_path.exists():
        print(f"❌ Magic8-Companion not found at: {companion_path}")
        show_manual_instructions()
        return 1
    
    # Create API files
    print("\nSetting up API endpoints...")
    create_api_endpoints(companion_path)
    create_start_script(companion_path)
    
    # Show instructions
    print("\n" + "="*60)
    print("✅ Setup Complete!")
    print("="*60)
    
    print("\nTo start Magic8-Companion with API:")
    print(f"1. cd {companion_path}")
    print("2. ./start_with_api.sh")
    print("\nOr manually:")
    print("   export M8C_ENABLE_DATA_API=true")
    print("   python -m magic8_companion")
    
    print("\nTo test:")
    print("   python setup_companion_api.py --test-only")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
