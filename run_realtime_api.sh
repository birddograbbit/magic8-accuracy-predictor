#!/bin/bash

echo "🚀 Starting Real-Time Prediction API"
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
python src/prediction_api_realtime.py

