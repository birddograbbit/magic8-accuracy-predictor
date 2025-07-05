#!/usr/bin/env python3
"""Optimize probability thresholds per symbol and strategy using F1 score."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
from sklearn.metrics import f1_score, precision_recall_curve
from collections import defaultdict
from src.models.xgboost_symbol_specific import prepare_symbol_data


def optimize_threshold_f1(df: pd.DataFrame, model, features: list, debug=False):
    """Return best threshold for dataframe using F1 score."""
    # Prepare features and fill missing values
    X = df[features].fillna(0)
    y = df['target'].values
    
    # Get predictions
    dtest = xgb.DMatrix(X)
    proba = model.predict(dtest)
    
    if debug:
        print(f"  Prediction stats: min={proba.min():.3f}, max={proba.max():.3f}, mean={proba.mean():.3f}")
        print(f"  Target distribution: {np.bincount(y)}")
    
    # Try different thresholds
    thresholds = np.arange(0.1, 0.9, 0.05)
    best_f1 = 0
    best_threshold = 0.5
    
    for threshold in thresholds:
        pred = (proba >= threshold).astype(int)
        f1 = f1_score(y, pred, zero_division=0)
        
        if debug and (threshold in [0.3, 0.5, 0.7] or f1 > best_f1):
            tp = ((pred == 1) & (y == 1)).sum()
            fp = ((pred == 1) & (y == 0)).sum()
            fn = ((pred == 0) & (y == 1)).sum()
            tn = ((pred == 0) & (y == 0)).sum()
            print(f"  Threshold {threshold:.2f}: F1={f1:.3f}, TP={tp}, FP={fp}, FN={fn}, TN={tn}")
        
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold
    
    return best_threshold, best_f1


def optimize_threshold_precision_recall(df: pd.DataFrame, model, features: list, target_recall=0.8):
    """Alternative: optimize threshold for target recall."""
    X = df[features].fillna(0)
    y = df['target'].values
    
    dtest = xgb.DMatrix(X)
    proba = model.predict(dtest)
    
    # Get precision-recall curve
    precisions, recalls, thresholds = precision_recall_curve(y, proba)
    
    # Find threshold closest to target recall
    idx = np.argmin(np.abs(recalls - target_recall))
    if idx < len(thresholds):
        return thresholds[idx], f1_score(y, (proba >= thresholds[idx]).astype(int))
    else:
        return 0.5, 0.0


def main(data_dir: str, model_dir: str, debug: bool = False):
    data_dir = Path(data_dir)
    model_dir = Path(model_dir)
    thresholds = defaultdict(dict)
    thresholds_by_recall = defaultdict(dict)
    
    # Summary statistics
    all_thresholds = []
    all_f1_scores = []
    
    for csv_file in sorted(data_dir.glob('*_trades.csv')):
        sym = csv_file.stem.split('_')[0]
        model_file = model_dir / f"{csv_file.stem}_model.pkl"
        feature_file = model_dir / f"{csv_file.stem}_features.pkl"
        
        if not model_file.exists():
            print(f"Model not found for {sym}, skipping")
            continue
        
        print(f"\nProcessing {sym}...")
        features = joblib.load(feature_file)
        model = joblib.load(model_file)
        
        # Load and prepare data
        df = pd.read_csv(csv_file, low_memory=False)
        
        # Prepare data to create target column from profit
        df, _ = prepare_symbol_data(df)
        
        # Filter to only features used in model
        available_features = [f for f in features if f in df.columns]
        if len(available_features) < len(features):
            print(f"Warning: {len(features) - len(available_features)} features missing for {sym}")
        
        # Optimize thresholds by strategy
        for strategy in df['strategy'].unique():
            group = df[df['strategy'] == strategy].copy()
            
            if len(group) < 100:  # Need sufficient samples
                if debug:
                    print(f"  Skipping {strategy}: only {len(group)} samples")
                continue
                
            if group['target'].nunique() < 2:
                if debug:
                    print(f"  Skipping {strategy}: no target variation")
                continue
            
            try:
                # Method 1: Optimize for F1 score
                threshold, f1 = optimize_threshold_f1(
                    group, model, available_features, 
                    debug=(debug and strategy == df['strategy'].iloc[0])  # Debug first strategy only
                )
                # Cast to regular Python floats for JSON serialization
                thresholds[sym][strategy] = float(threshold)
                all_thresholds.append(float(threshold))
                all_f1_scores.append(float(f1))
                
                # Method 2: Optimize for 80% recall
                threshold_recall, _ = optimize_threshold_precision_recall(
                    group, model, available_features, target_recall=0.8
                )
                thresholds_by_recall[sym][strategy] = float(threshold_recall)
                
                print(f"  {strategy}: F1-optimal={threshold:.2f} (F1={f1:.3f}), " 
                      f"80%-recall={threshold_recall:.2f}")
                
            except Exception as e:
                print(f"  Error optimizing {strategy}: {e}")
                import traceback
                if debug:
                    traceback.print_exc()
    
    # Save both threshold sets
    out_path_f1 = model_dir / 'thresholds.json'
    out_path_recall = model_dir / 'thresholds_recall80.json'
    
    with open(out_path_f1, 'w') as f:
        json.dump(thresholds, f, indent=2)
    
    with open(out_path_recall, 'w') as f:
        json.dump(thresholds_by_recall, f, indent=2)
    
    print(f"\n=== Summary ===")
    print(f"F1-optimized thresholds saved to: {out_path_f1}")
    print(f"80%-recall thresholds saved to: {out_path_recall}")
    
    if all_thresholds:
        print(f"\nThreshold distribution:")
        print(f"  Mean: {np.mean(all_thresholds):.3f}")
        print(f"  Std:  {np.std(all_thresholds):.3f}")
        print(f"  Min:  {np.min(all_thresholds):.3f}")
        print(f"  Max:  {np.max(all_thresholds):.3f}")
        print(f"\nF1 score distribution:")
        print(f"  Mean: {np.mean(all_f1_scores):.3f}")
        print(f"  Min:  {np.min(all_f1_scores):.3f}")
        print(f"  Max:  {np.max(all_f1_scores):.3f}")


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Optimize thresholds')
    p.add_argument('data_dir', help='Directory with *_trades.csv files')
    p.add_argument('model_dir', help='Directory with trained models')
    p.add_argument('--debug', action='store_true', help='Enable debug output')
    args = p.parse_args()
    main(args.data_dir, args.model_dir, args.debug)
