#!/usr/bin/env python3
"""Optimize probability thresholds per symbol and strategy using F1 score."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb

from collections import defaultdict
from src.models.xgboost_symbol_specific import prepare_symbol_data


def optimize_threshold(df: pd.DataFrame, model, features: list):
    """Return best threshold for dataframe using provided model."""
    X = df[features]
    y = df['target']
    dtest = xgb.DMatrix(X)
    proba = model.predict(dtest)
    thresholds = np.arange(0.1, 0.9, 0.05)
    best = 0
    best_th = 0.5
    for th in thresholds:
        pred = (proba >= th).astype(int)
        f1 = (2 * (pred & y).sum()) / (pred.sum() + y.sum() + 1e-9)
        if f1 > best:
            best = f1
            best_th = th
    return best_th


def main(data_dir: str, model_dir: str):
    data_dir = Path(data_dir)
    model_dir = Path(model_dir)
    thresholds = defaultdict(dict)
    
    for csv_file in data_dir.glob('*_trades.csv'):
        sym = csv_file.stem.split('_')[0]
        model_file = model_dir / f"{csv_file.stem}_model.pkl"
        feature_file = model_dir / f"{csv_file.stem}_features.pkl"
        
        if not model_file.exists():
            print(f"Model not found for {sym}, skipping")
            continue
            
        features = joblib.load(feature_file)
        model = joblib.load(model_file)
        
        # Load and prepare data
        df = pd.read_csv(csv_file, low_memory=False)
        
        # Prepare data to create target column from profit
        df, _ = prepare_symbol_data(df)
        
        # Filter to only features used in model
        available_features = [f for f in features if f in df.columns]
        if len(available_features) < len(features):
            print(f"Warning: Some features missing for {sym}")
        
        # Optimize thresholds by strategy
        for strategy, group in df.groupby('strategy'):
            if len(group) < 10:  # Skip strategies with too few samples
                continue
                
            if group['target'].nunique() < 2:
                print(f"Skipping {sym}-{strategy}: insufficient target variation")
                continue
                
            try:
                th = optimize_threshold(group, model, available_features)
                thresholds[sym][strategy] = th
                print(f"{sym}-{strategy}: {th:.2f}")
            except Exception as e:
                print(f"Error optimizing {sym}-{strategy}: {e}")

    out_path = model_dir / 'thresholds.json'
    with open(out_path, 'w') as f:
        json.dump(thresholds, f, indent=2)
    
    print(f"\nThresholds saved to: {out_path}")


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Optimize thresholds')
    p.add_argument('data_dir', help='Directory with *_trades.csv files')
    p.add_argument('model_dir', help='Directory with trained models')
    args = p.parse_args()
    main(args.data_dir, args.model_dir)
