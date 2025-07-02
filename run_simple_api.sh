#!/bin/bash
# Quick test of the simplified solution

echo "Testing Simplified IB Connection (All in One File)"
echo "=================================================="

echo -e "\n1. Testing direct IB connection..."
python test_direct_ib.py

if [ $? -eq 0 ]; then
    echo -e "\n✓ IB connection works!"
    echo -e "\n2. Starting API server..."
    echo "   Access at: http://localhost:8000"
    echo "   Docs at: http://localhost:8000/docs"
    echo -e "\n   Press Ctrl+C to stop\n"
    
    python -m uvicorn src.prediction_api_simple:app --host 0.0.0.0 --port 8000
else
    echo -e "\n✗ IB connection failed"
    echo "  Check that IB Gateway is running on port 7497"
fi
