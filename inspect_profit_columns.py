#!/usr/bin/env python
"""
Inspect the normalized data to find the correct profit columns
"""

import pandas as pd
import numpy as np

print("Inspecting Normalized Data Columns")
print("=" * 70)

# Load the normalized data
df = pd.read_csv('data/normalized/normalized_aggregated.csv', nrows=10)

print("\nAll columns in normalized data:")
for i, col in enumerate(df.columns):
    print(f"{i:3d}: {col}")

print("\n" + "="*70)
print("Looking for profit-related columns...")

# Load full data to check specific columns
df_full = pd.read_csv('data/normalized/normalized_aggregated.csv')

# Check profit-related columns
profit_cols = [col for col in df_full.columns if 'prof' in col.lower() or 'raw' in col.lower() or 'managed' in col.lower()]
print(f"\nProfit-related columns found: {len(profit_cols)}")
for col in profit_cols:
    non_null = df_full[col].notna().sum()
    if non_null > 0:
        print(f"\n{col}:")
        print(f"  Non-null values: {non_null}")
        print(f"  Data type: {df_full[col].dtype}")
        if df_full[col].dtype in ['float64', 'int64']:
            print(f"  Min: {df_full[col].min()}")
            print(f"  Max: {df_full[col].max()}")
            print(f"  Mean: {df_full[col].mean():.2f}")
            # Show distribution of positive/negative
            if 'raw' in col.lower() or 'profit' in col.lower():
                positive = (df_full[col] > 0).sum()
                negative = (df_full[col] <= 0).sum()
                print(f"  Positive (wins): {positive} ({positive/non_null:.1%})")
                print(f"  Negative/Zero (losses): {negative} ({negative/non_null:.1%})")

# Check trad_profited column
print("\n" + "="*70)
print("Checking trad_profited column:")
if 'trad_profited' in df_full.columns:
    print(f"  Non-null values: {df_full['trad_profited'].notna().sum()}")
    print(f"  Value counts: {df_full['trad_profited'].value_counts().to_dict()}")

# Look for the specific Raw profit column
print("\n" + "="*70)
print("Searching for 'Raw' profit column...")

raw_cols = [col for col in df_full.columns if 'raw' in col.lower()]
print(f"\nColumns containing 'raw': {raw_cols}")

# Check what profit columns have the most data
print("\n" + "="*70)
print("Profit columns by data availability:")
profit_coverage = []
for col in df_full.columns:
    if any(keyword in col.lower() for keyword in ['profit', 'raw', 'managed', 'p/l', 'pnl']):
        coverage = df_full[col].notna().sum()
        if coverage > 0:
            profit_coverage.append((col, coverage))

profit_coverage.sort(key=lambda x: x[1], reverse=True)
for col, coverage in profit_coverage[:10]:
    print(f"  {col}: {coverage} records ({coverage/len(df_full):.1%})")

# Save a sample of the data for inspection
print("\n" + "="*70)
print("Saving sample data for inspection...")
sample_cols = ['interval_datetime', 'pred_symbol', 'prof_strategy_name'] + profit_cols + ['trad_profited']
sample_cols = [col for col in sample_cols if col in df_full.columns]
df_full[sample_cols].head(20).to_csv('sample_profit_data.csv', index=False)
print("Sample saved to sample_profit_data.csv")
