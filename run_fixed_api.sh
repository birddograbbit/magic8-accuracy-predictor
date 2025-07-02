#!/bin/bash
# Run the fixed API with proper feature calculation

echo "🚀 Starting Fixed Magic8 Prediction API..."
echo "========================================"

# Set Python path
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

echo -e "\n✅ Using fixed API with proper feature calculation"
echo "   - Calculates all 74 required features"
echo "   - No more constant 33.4% predictions!"
echo -e "\n   Access at: http://localhost:8000"
echo "   Press Ctrl+C to stop\n"

python src/prediction_api_simple_fixed.py
