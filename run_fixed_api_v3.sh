#!/bin/bash

echo "🚀 Starting Fixed Magic8 Prediction API v3..."
echo "========================================"
echo ""
echo "✅ Using improved API with MallocStackLogging fix"
echo "   - No more memory allocation warnings on macOS"
echo "   - Proper market data management"
echo "   - Improved error handling"
echo ""
echo "   Access at: http://localhost:8000"
echo "   Press Ctrl+C to stop"
echo ""

# Note: MallocStackLogging is already disabled in the Python script itself
# so we don't need to export it here

# Check if IB Gateway is running
if lsof -i:7497 >/dev/null 2>&1; then
    echo "✓ IB Gateway detected on port 7497"
else
    echo "⚠️  IB Gateway not detected - API will use mock data"
fi

# Set PYTHONPATH and run the API
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
python src/prediction_api_simple_fixed_v3.py