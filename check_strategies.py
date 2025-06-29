"""
Quick check on strategy distribution in the normalized data
"""

import pandas as pd
import numpy as np

def check_strategies():
    print("Checking Strategy Distribution")
    print("=" * 60)
    
    # Load the normalized data
    df = pd.read_csv('data/normalized/normalized_aggregated.csv')
    
    print(f"\nTotal records: {len(df):,}")
    
    # Check strategy column
    if 'prof_strategy_name' in df.columns:
        print("\nStrategy distribution:")
        strategy_counts = df['prof_strategy_name'].value_counts()
        print(strategy_counts)
        
        print("\nStrategy percentages:")
        strategy_pcts = df['prof_strategy_name'].value_counts(normalize=True) * 100
        print(strategy_pcts.round(2))
        
        # Check for any other strategy-related columns
        strategy_cols = [col for col in df.columns if 'strategy' in col.lower()]
        print(f"\nAll strategy-related columns: {strategy_cols}")
        
        # Check unique values
        print(f"\nUnique strategies: {df['prof_strategy_name'].unique()}")
        
        # Check for nulls
        print(f"\nNull values in prof_strategy_name: {df['prof_strategy_name'].isna().sum()}")
        
        # Check if there are variations in naming
        print("\nChecking for strategy name variations...")
        for val in df['prof_strategy_name'].unique():
            if pd.notna(val):
                print(f"  '{val}' (type: {type(val)})")
        
        # Sample some records to see raw data
        print("\nSample of strategy names:")
        print(df[['prof_strategy_name']].head(20))
        
        # Check if other columns might contain strategy info
        print("\nChecking other potential strategy columns...")
        for col in ['strategy', 'trade_type', 'type', 'order_type']:
            if col in df.columns:
                print(f"\n{col}:")
                print(df[col].value_counts())
    else:
        print("\nERROR: 'prof_strategy_name' column not found!")
        print(f"Available columns: {list(df.columns)}")
    
    # Look for any column that might indicate Iron Condor, Vertical, or Sonar
    print("\nSearching for strategy keywords in all columns...")
    keywords = ['iron', 'condor', 'vertical', 'sonar', 'butterfly', 'spread']
    
    for col in df.columns:
        if df[col].dtype == 'object':  # Only check string columns
            try:
                for keyword in keywords:
                    matches = df[col].astype(str).str.contains(keyword, case=False, na=False).sum()
                    if matches > 0:
                        print(f"  Found '{keyword}' in column '{col}': {matches} matches")
            except:
                pass

if __name__ == "__main__":
    check_strategies()
