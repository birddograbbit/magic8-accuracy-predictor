#!/usr/bin/env python3
"""
Entry point for Magic8 Prediction API.
Runs the API with uvicorn so reload and workers operate correctly.
"""

import subprocess
import sys
import os

def main():
    """Run the prediction API using uvicorn."""
    # Ensure we're in the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # Run the API using uvicorn with module path
    cmd = [sys.executable, "-m", "uvicorn", "src.prediction_api:app", "--reload"]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nAPI stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"API failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
