#!/usr/bin/env python3
"""
Startup script for the prediction API that handles imports correctly.
Run this from the project root directory.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now we can import and run the prediction API
from prediction_api import app
import uvicorn

if __name__ == "__main__":
    print("Starting Magic8 Prediction API...")
    print("Note: NDX and other symbols without market data subscriptions will use mock data")
    
    # Run the FastAPI server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload for production
        log_level="info"
    )
