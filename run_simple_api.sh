#!/bin/bash
# Magic8 Accuracy Predictor API Startup Script
# Updated for cleaned repository structure

echo "🚀 Magic8 Accuracy Predictor - Quick Start"
echo "=========================================="

# Set Python path to resolve module imports after cleanup
echo "📁 Setting Python path..."
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

echo -e "\n🔍 1. Testing model availability..."
python -c "import joblib; joblib.load('models/xgboost_phase1_model.pkl'); print('✅ Model loads successfully')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Model loaded successfully!"
    echo -e "\n🎯 2. Starting API server..."
    echo "   Access at: http://localhost:8000"
    echo "   Health check: http://localhost:8000/"
    echo "   API docs: http://localhost:8000/docs"
    echo -e "\n   Press Ctrl+C to stop\n"
    
    python src/prediction_api_simple.py
else
    echo "❌ Model loading failed"
    echo "   Make sure you have:"
    echo "   - Run the ML training pipeline"
    echo "   - Have models/xgboost_phase1_model.pkl file"
    echo "   - Installed requirements: pip install -r requirements.txt"
    exit 1
fi
