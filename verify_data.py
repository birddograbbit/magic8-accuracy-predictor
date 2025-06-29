#!/usr/bin/env python
"""
Quick test of XGBoost model with corrected data
"""

import sys
import pandas as pd
import json

print("Testing XGBoost Model with Corrected Data")
print("=" * 60)

# Check the processed data
try:
    with open('data/phase1_processed/feature_info.json', 'r') as f:
        feature_info = json.load(f)
    
    print("✓ Data successfully processed")
    print(f"  Features: {feature_info['n_features']}")
    print(f"  Train samples: {feature_info['train_samples']}")
    print(f"  Train class distribution: {feature_info['class_distribution']['train']}")
    print(f"  Val class distribution: {feature_info['class_distribution']['val']}")
    print(f"  Test class distribution: {feature_info['class_distribution']['test']}")
    
    # Calculate win rates
    for split in ['train', 'val', 'test']:
        dist = feature_info['class_distribution'][split]
        if 1 in dist:
            total = sum(dist.values())
            win_rate = dist[1] / total * 100
            print(f"  {split.capitalize()} win rate: {win_rate:.1f}%")
    
    print("\nNow you can run the XGBoost model:")
    print("python src/models/xgboost_baseline.py")
    
except Exception as e:
    print(f"✗ Error: {e}")
    print("Please run: python rebuild_data.py first")
    sys.exit(1)
