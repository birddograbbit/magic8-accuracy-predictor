#!/usr/bin/env python3
"""Optimize probability thresholds per symbol using F1 score."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb

from src.models.xgboost_symbol_specific import train_symbol_model


def optimize_threshold(symbol_csv: Path, model_path: Path, features: list):
    df = pd.read_csv(symbol_csv)
    X = df[features]
    y = df['target']
    dtest = xgb.DMatrix(X)
    model = joblib.load(model_path)
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
    thresholds = {}
    for csv_file in data_dir.glob('*_trades.csv'):
        sym = csv_file.stem.split('_')[0]
        model_file = model_dir / f"{csv_file.stem}_model.pkl"
        feature_file = model_dir / f"{csv_file.stem}_features.pkl"
        if not model_file.exists():
            continue
        features = joblib.load(feature_file)
        th = optimize_threshold(csv_file, model_file, features)
        thresholds[sym] = th
        print(f"{sym}: {th:.2f}")
    out_path = model_dir / 'thresholds.json'
    with open(out_path, 'w') as f:
        json.dump(thresholds, f, indent=2)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Optimize thresholds')
    p.add_argument('data_dir')
    p.add_argument('model_dir')
    args = p.parse_args()
    main(args.data_dir, args.model_dir)
