#!/usr/bin/env python3
"""
Entry point for Magic8 Prediction API
Runs the API as a module to ensure proper package imports
"""

import subprocess
import sys
import os

def main():
    """Run the prediction API as a module."""
    # Ensure we're in the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # Run the API using -m flag to properly handle package imports
    cmd = [sys.executable, "-m", "src.prediction_api"]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nAPI stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"API failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
