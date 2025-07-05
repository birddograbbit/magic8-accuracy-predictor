#!/usr/bin/env python3
"""Optimize probability thresholds for grouped models."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
from sklearn.metrics import f1_score
from collections import defaultdict
from src.models.xgboost_symbol_specific import prepare_symbol_data


def optimize_grouped_thresholds(data_dir: str, model_dir: str, debug: bool = False):
    """Optimize thresholds for grouped models (SPX_SPY and QQQ_AAPL_TSLA)."""
    data_dir = Path(data_dir)
    model_dir = Path(model_dir)
    
    # Define groups matching train_grouped_models.py
    groups = {
        "SPX_SPY": ["SPX", "SPY"],
        "QQQ_AAPL_TSLA": ["QQQ", "AAPL", "TSLA"],
    }
    
    thresholds = {}
    
    for group_name, symbols in groups.items():
        print(f"\nProcessing grouped model: {group_name}")
        
        # Check if model exists
        model_file = model_dir / f"{group_name}_combined_model.pkl"
        feature_file = model_dir / f"{group_name}_combined_features.pkl"
        
        if not model_file.exists():
            print(f"  Model not found, skipping")
            continue
        
        # Load model and features
        model = joblib.load(model_file)
        features = joblib.load(feature_file)
        
        # Load and combine data for symbols in group
        dfs = []
        for symbol in symbols:
            csv_file = data_dir / f"{symbol}_trades.csv"
            if csv_file.exists():
                df = pd.read_csv(csv_file, low_memory=False)
                df, _ = prepare_symbol_data(df)
                dfs.append(df)
            else:
                print(f"  Warning: No data file for {symbol}")
        
        if not dfs:
            print(f"  No data available for group")
            continue
        
        # Combine data
        combined_df = pd.concat(dfs, ignore_index=True)
        print(f"  Combined data: {len(combined_df)} samples from {len(dfs)} symbols")
        
        # Filter to available features
        available_features = [f for f in features if f in combined_df.columns]
        if len(available_features) < len(features):
            print(f"  Warning: {len(features) - len(available_features)} features missing")
        
        # Optimize thresholds by strategy
        thresholds[group_name] = {}
        
        for strategy in combined_df['strategy'].unique():
            group_data = combined_df[combined_df['strategy'] == strategy].copy()
            
            if len(group_data) < 100:
                continue
            
            if group_data['target'].nunique() < 2:
                continue
            
            # Prepare data
            X = group_data[available_features].fillna(0)
            y = group_data['target'].values
            
            # Get predictions
            dtest = xgb.DMatrix(X)
            proba = model.predict(dtest)
            
            # Find best threshold
            best_f1 = 0
            best_threshold = 0.5
            
            for threshold in np.arange(0.1, 0.9, 0.05):
                pred = (proba >= threshold).astype(int)
                f1 = f1_score(y, pred, zero_division=0)
                
                if f1 > best_f1:
                    best_f1 = f1
                    best_threshold = threshold
            
            thresholds[group_name][strategy] = best_threshold
            print(f"  {strategy}: threshold={best_threshold:.2f} (F1={best_f1:.3f})")
    
    # Save thresholds
    out_path = model_dir / 'thresholds_grouped.json'
    with open(out_path, 'w') as f:
        json.dump(thresholds, f, indent=2)
    
    print(f"\nGrouped thresholds saved to: {out_path}")


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Optimize thresholds for grouped models')
    p.add_argument('data_dir', help='Directory with *_trades.csv files')
    p.add_argument('model_dir', help='Directory with grouped models')
    p.add_argument('--debug', action='store_true', help='Enable debug output')
    args = p.parse_args()
    optimize_grouped_thresholds(args.data_dir, args.model_dir, args.debug)
