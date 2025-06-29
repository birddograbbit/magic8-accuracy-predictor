#!/usr/bin/env python
"""
Diagnostic script to check which features are being used vs excluded
"""

import pandas as pd
import json

print("Magic8 XGBoost Feature Diagnostic")
print("=" * 50)

# Load the processed data
train_df = pd.read_csv('data/phase1_processed/train_data.csv')

# Load feature info
with open('data/phase1_processed/feature_info.json', 'r') as f:
    feature_info = json.load(f)

original_features = feature_info['feature_names']
print(f"\nOriginal feature count: {len(original_features)}")

# Check for object columns
object_columns = []
numeric_columns = []
excluded_columns = []

for feature in original_features:
    if feature in train_df.columns:
        if train_df[feature].dtype == 'object':
            object_columns.append(feature)
        else:
            # Double check if it's truly numeric
            try:
                pd.to_numeric(train_df[feature], errors='raise')
                numeric_columns.append(feature)
            except:
                excluded_columns.append(feature)

print(f"\nObject/String columns found ({len(object_columns)}):")
for col in object_columns:
    sample_values = train_df[col].value_counts().head(3).index.tolist()
    print(f"  - {col}: {sample_values}")

print(f"\nNumeric columns kept ({len(numeric_columns)}):")
print(f"  Total: {len(numeric_columns)} features")

if excluded_columns:
    print(f"\nOther excluded columns ({len(excluded_columns)}):")
    for col in excluded_columns:
        print(f"  - {col}")

# Show feature groups
print("\nFeature breakdown by type:")
temporal = [f for f in numeric_columns if f in ['hour', 'minute', 'day_of_week', 'hour_sin', 'hour_cos', 'is_market_open', 'is_open_30min', 'is_close_30min', 'minutes_to_close']]
vix = [f for f in numeric_columns if f.startswith('vix')]
strategy = [f for f in numeric_columns if f.startswith('strategy_')]
price = [f for f in numeric_columns if any(f.startswith(s) for s in ['SPX_', 'SPY_', 'QQQ_', 'RUT_', 'NDX_', 'XSP_', 'AAPL_', 'TSLA_'])]
trade = [f for f in numeric_columns if f in ['premium_normalized', 'risk_reward_ratio', 'pred_predicted', 'pred_price', 'pred_difference', 'prof_premium', 'prof_risk', 'prof_reward', 'trad_probability', 'trad_expected_move']]

print(f"  - Temporal features: {len(temporal)}")
print(f"  - VIX features: {len(vix)}")
print(f"  - Strategy features (one-hot): {len(strategy)}")
print(f"  - Price features: {len(price)}")
print(f"  - Trade features: {len(trade)}")
print(f"  - Total: {len(numeric_columns)}")

print("\nReady to train XGBoost with clean numeric features!")
