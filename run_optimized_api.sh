#!/bin/bash

echo "🚀 Starting Optimized Magic8 Prediction API..."
echo "=========================================="
echo ""
echo "✅ Performance Optimizations:"
echo "   - Parallel market data fetching"
echo "   - Persistent ticker subscriptions"
echo "   - Pre-computed static features"
echo "   - Connection pooling (8 workers)"
echo "   - Increased cache TTL (60s)"
echo "   - Model warm-up on startup"
echo ""
echo "🎯 Target: <5s response time"
echo ""
echo "   Access at: http://localhost:8000"
echo "   Press Ctrl+C to stop"
echo ""

# Check if IB Gateway is running
if lsof -i:7497 >/dev/null 2>&1; then
    echo "✓ IB Gateway detected on port 7497"
else
    echo "⚠️  IB Gateway not detected - API will use mock data"
fi

# Set PYTHONPATH and run the API
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
python src/prediction_api_optimized.py