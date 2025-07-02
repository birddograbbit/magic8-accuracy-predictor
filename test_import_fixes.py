#!/usr/bin/env python3
"""
Test script to verify import fixes and API startup
"""

import subprocess
import sys
import os
import time
import requests

def test_direct_execution():
    """Test that direct execution fails as expected."""
    print("1. Testing direct execution (should fail)...")
    result = subprocess.run(
        [sys.executable, "src/prediction_api.py"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0 and "relative import" in result.stderr:
        print("   ✓ Direct execution correctly fails with import error")
        return True
    else:
        print("   ✗ Unexpected result from direct execution")
        return False

def test_module_execution():
    """Test that module execution works."""
    print("\n2. Testing module execution...")
    
    # Start the API as a background process
    proc = subprocess.Popen(
        [sys.executable, "-m", "src.prediction_api"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give it time to start
    time.sleep(5)
    
    try:
        # Check if API is responding
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("   ✓ API started successfully with module execution")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"   ✗ API returned status {response.status_code}")
            return False
    except requests.ConnectionError:
        print("   ✗ Could not connect to API")
        # Check stderr for errors
        stderr = proc.stderr.read()
        if stderr:
            print(f"   Error output: {stderr}")
        return False
    finally:
        # Clean up
        proc.terminate()
        proc.wait()

def test_startup_script():
    """Test the startup script."""
    print("\n3. Testing startup script...")
    
    # Make sure it's executable
    os.chmod("./run_prediction_api.py", 0o755)
    
    # Start the API
    proc = subprocess.Popen(
        ["./run_prediction_api.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give it time to start
    time.sleep(5)
    
    try:
        # Check if API is responding
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("   ✓ API started successfully with startup script")
            return True
        else:
            print(f"   ✗ API returned status {response.status_code}")
            return False
    except requests.ConnectionError:
        print("   ✗ Could not connect to API")
        return False
    finally:
        # Clean up
        proc.terminate()
        proc.wait()

def main():
    """Run all import tests."""
    print("Testing Python Import Fixes")
    print("=" * 50)
    
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    results = []
    
    # Test 1: Direct execution should fail
    results.append(test_direct_execution())
    
    # Test 2: Module execution should work
    results.append(test_module_execution())
    
    # Test 3: Startup script should work
    results.append(test_startup_script())
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"  Direct execution fails (expected): {'✓' if results[0] else '✗'}")
    print(f"  Module execution works: {'✓' if results[1] else '✗'}")
    print(f"  Startup script works: {'✓' if results[2] else '✗'}")
    
    if results[1] or results[2]:
        print("\n✅ Import fixes are working correctly!")
        print("\nRecommended ways to start the API:")
        print("  1. python -m src.prediction_api")
        print("  2. ./run_prediction_api.py")
        print("  3. ./start_api_with_checks.py")
    else:
        print("\n❌ Import fixes may need adjustment")

if __name__ == "__main__":
    main()
