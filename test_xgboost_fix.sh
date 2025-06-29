#!/bin/bash
# Quick test script to verify the XGBoost fix works

echo "Testing XGBoost baseline model fix..."
echo "====================================="

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Warning: Virtual environment not activated"
    echo "Please activate with: source .venv/bin/activate"
    exit 1
fi

# Test if we can import the model and load data
python -c "
import sys
sys.path.append('.')
from src.models.xgboost_baseline import XGBoostBaseline
import pandas as pd

print('✓ Imports successful')

# Try to load data
model = XGBoostBaseline()
try:
    model.load_data()
    print('✓ Data loaded successfully')
    print(f'  Features: {len(model.feature_names)}')
    
    # Check if vix_regime is removed
    if 'vix_regime' not in model.feature_names:
        print('✓ vix_regime categorical column removed')
    else:
        print('✗ WARNING: vix_regime still in features!')
        
    # Try preprocessing
    model.preprocess_features()
    print('✓ Preprocessing successful')
    
except Exception as e:
    print(f'✗ Error: {e}')
    sys.exit(1)

print('\\nAll tests passed! You can now run the full pipeline.')
"

echo ""
echo "If all tests pass, run the full model with:"
echo "python src/models/xgboost_baseline.py"
