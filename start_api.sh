#!/bin/bash
# Magic8 Accuracy Predictor API Startup Script
# Fixes Python path issues after cleanup

echo "🚀 Starting Magic8 Accuracy Predictor API..."
echo "📁 Setting Python path..."
export PYTHONPATH="/Users/jt/magic8/magic8-accuracy-predictor/src:$PYTHONPATH"

echo "🔍 Checking model availability..."
python -c "import joblib; joblib.load('models/xgboost_phase1_model.pkl'); print('✅ Model loads successfully')" || {
    echo "❌ Model loading failed"
    exit 1
}

echo "🎯 Starting API server..."
python src/prediction_api_simple.py
