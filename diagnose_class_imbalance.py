#!/usr/bin/env python
"""
Diagnose class imbalance and temporal distribution issues
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

def analyze_target_distribution():
    """Analyze target distribution over time"""
    print("Analyzing Target Distribution Over Time")
    print("=" * 70)
    
    # Load the normalized data
    df = pd.read_csv('data/normalized/normalized_aggregated.csv')
    df['interval_datetime'] = pd.to_datetime(df['interval_datetime'])
    
    # Create target from available data
    if 'trad_profited' in df.columns:
        df['target'] = df['trad_profited'].map({True: 1, False: 0})
    elif 'prof_profit' in df.columns:
        df['target'] = (df['prof_profit'] > 0).astype(int)
    
    # Remove NaN targets
    df_clean = df[df['target'].notna()].copy()
    
    print(f"Total records with target: {len(df_clean)}")
    print(f"Overall target distribution:")
    print(df_clean['target'].value_counts())
    print(f"Positive rate: {df_clean['target'].mean():.2%}")
    
    # Sort by time
    df_clean = df_clean.sort_values('interval_datetime')
    
    # Create monthly aggregation
    df_clean['year_month'] = df_clean['interval_datetime'].dt.to_period('M')
    monthly_stats = df_clean.groupby('year_month').agg({
        'target': ['count', 'sum', 'mean']
    }).round(3)
    
    print("\nMonthly Statistics:")
    print(monthly_stats.tail(12))  # Last 12 months
    
    # Check temporal splits
    n_samples = len(df_clean)
    train_end = int(n_samples * 0.6)
    val_end = int(n_samples * 0.8)
    
    train_data = df_clean.iloc[:train_end]
    val_data = df_clean.iloc[train_end:val_end]
    test_data = df_clean.iloc[val_end:]
    
    print("\nTemporal Split Analysis:")
    print(f"Train: {train_data['interval_datetime'].min()} to {train_data['interval_datetime'].max()}")
    print(f"  Samples: {len(train_data)}, Positive rate: {train_data['target'].mean():.2%}")
    
    print(f"Val: {val_data['interval_datetime'].min()} to {val_data['interval_datetime'].max()}")
    print(f"  Samples: {len(val_data)}, Positive rate: {val_data['target'].mean():.2%}")
    
    print(f"Test: {test_data['interval_datetime'].min()} to {test_data['interval_datetime'].max()}")
    print(f"  Samples: {len(test_data)}, Positive rate: {test_data['target'].mean():.2%}")
    
    # Plot positive rate over time
    plt.figure(figsize=(12, 6))
    
    # Calculate rolling positive rate
    df_clean['positive_rate_rolling'] = df_clean['target'].rolling(window=1000, min_periods=100).mean()
    
    plt.subplot(2, 1, 1)
    plt.plot(df_clean['interval_datetime'], df_clean['positive_rate_rolling'])
    plt.axhline(y=df_clean['target'].mean(), color='r', linestyle='--', label='Overall average')
    plt.axvline(x=train_data['interval_datetime'].max(), color='g', linestyle='--', label='Train/Val split')
    plt.axvline(x=val_data['interval_datetime'].max(), color='b', linestyle='--', label='Val/Test split')
    plt.ylabel('Positive Rate (Rolling 1000)')
    plt.title('Positive Rate Over Time')
    plt.legend()
    
    # Plot sample count by month
    plt.subplot(2, 1, 2)
    monthly_counts = df_clean.groupby(df_clean['interval_datetime'].dt.to_period('M')).size()
    monthly_counts.plot(kind='bar')
    plt.ylabel('Sample Count')
    plt.title('Monthly Sample Count')
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('plots/target_distribution_analysis.png', dpi=300)
    print("\nSaved plot to plots/target_distribution_analysis.png")
    
    # Check for specific time periods with issues
    print("\nChecking for problematic periods...")
    
    # Group by month and check for months with very low positive rates
    monthly_positive_rates = df_clean.groupby('year_month')['target'].mean()
    problematic_months = monthly_positive_rates[monthly_positive_rates < 0.01]
    
    if len(problematic_months) > 0:
        print(f"\n⚠️  Found {len(problematic_months)} months with <1% positive rate:")
        for month, rate in problematic_months.items():
            count = df_clean[df_clean['year_month'] == month].shape[0]
            print(f"  {month}: {rate:.2%} positive rate ({count} samples)")
    
    return df_clean

def analyze_by_symbol():
    """Analyze target distribution by trading symbol"""
    print("\n\nAnalyzing Target Distribution by Symbol")
    print("=" * 70)
    
    df = pd.read_csv('data/normalized/normalized_aggregated.csv')
    
    # Create target
    if 'trad_profited' in df.columns:
        df['target'] = df['trad_profited'].map({True: 1, False: 0})
    elif 'prof_profit' in df.columns:
        df['target'] = (df['prof_profit'] > 0).astype(int)
    
    df_clean = df[df['target'].notna()].copy()
    
    # Analyze by symbol
    symbol_stats = df_clean.groupby('pred_symbol').agg({
        'target': ['count', 'sum', 'mean']
    }).round(3)
    
    symbol_stats.columns = ['total_trades', 'wins', 'win_rate']
    symbol_stats = symbol_stats.sort_values('total_trades', ascending=False)
    
    print("Symbol Statistics:")
    print(symbol_stats)
    
    return symbol_stats

def suggest_solutions():
    """Suggest solutions for the class imbalance"""
    print("\n\nSuggested Solutions")
    print("=" * 70)
    
    print("1. **Stratified Temporal Split**: Instead of pure temporal split,")
    print("   use stratified sampling within time windows to ensure each")
    print("   split has a reasonable number of positive samples.")
    print()
    print("2. **Adjust Split Ratios**: Consider 70/15/15 split instead of")
    print("   60/20/20 to ensure more recent data (with potentially different")
    print("   patterns) is included in training.")
    print()
    print("3. **Class Weights**: The model already uses class weights, but")
    print("   you might need to adjust them manually for extreme imbalance.")
    print()
    print("4. **Threshold Tuning**: Instead of 0.5, find optimal threshold")
    print("   using validation set to balance precision/recall.")
    print()
    print("5. **Consider SMOTE**: For extreme imbalance, consider using")
    print("   SMOTE or ADASYN for synthetic minority oversampling.")

def main():
    # Create plots directory if it doesn't exist
    import os
    os.makedirs('plots', exist_ok=True)
    
    # Run analyses
    df = analyze_target_distribution()
    symbol_stats = analyze_by_symbol()
    suggest_solutions()
    
    print("\n" + "="*70)
    print("Analysis complete! Check plots/target_distribution_analysis.png")
    print("\nKey findings:")
    print("- The validation and test sets have almost no positive samples")
    print("- This suggests a temporal shift in trading performance")
    print("- You may need to use stratified splitting or adjust the time periods")

if __name__ == "__main__":
    main()
