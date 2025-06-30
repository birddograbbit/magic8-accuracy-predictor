#!/usr/bin/env python3
"""
Deep diagnostic script to understand the malformed rows issue
"""

import pandas as pd
import os

def deep_diagnose_csv():
    """Perform deep analysis of problematic CSV files"""
    
    # Test file with known issues
    test_file = "data/source/2023-01-13-8D96E/profit 20230113-212247.csv"
    
    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        return
        
    print(f"Analyzing: {test_file}")
    print("=" * 80)
    
    # Read the raw CSV to see all data
    df = pd.read_csv(test_file)
    
    print(f"\nDataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Check for rows where Symbol doesn't contain expected values
    valid_symbols = ['SPX', 'SPY', 'RUT', 'QQQ', 'XSP', 'NDX', 'AAPL', 'TSLA']
    
    print("\n--- Symbol Analysis ---")
    print(f"Total rows: {len(df)}")
    
    if 'Symbol' in df.columns:
        # Count valid symbols
        valid_symbol_mask = df['Symbol'].isin(valid_symbols)
        valid_count = valid_symbol_mask.sum()
        invalid_count = (~valid_symbol_mask).sum()
        
        print(f"Rows with valid symbols: {valid_count}")
        print(f"Rows with invalid symbols: {invalid_count}")
        
        # Show unique invalid symbols
        invalid_symbols = df[~valid_symbol_mask]['Symbol'].unique()
        print(f"\nInvalid symbols found: {invalid_symbols[:10].tolist()}")
        
        # Check Hour column for invalid symbol rows
        if 'Hour' in df.columns and invalid_count > 0:
            print("\n--- Hour column in invalid symbol rows ---")
            invalid_df = df[~valid_symbol_mask]
            print(f"Sample Hour values in invalid rows: {invalid_df['Hour'].head(10).tolist()}")
            
            # Check if Hour contains symbols
            hour_contains_symbols = invalid_df['Hour'].isin(valid_symbols)
            if hour_contains_symbols.any():
                print(f"\n⚠️  Found {hour_contains_symbols.sum()} rows where Hour column contains trading symbols!")
                print("Sample rows with symbols in Hour column:")
                print(invalid_df[hour_contains_symbols][['Hour', 'Symbol', 'Name']].head())
    
    # Check for completely empty or NaN rows
    print("\n--- Empty/NaN Row Analysis ---")
    nan_counts = df.isna().sum(axis=1)
    completely_empty = (nan_counts == len(df.columns)).sum()
    mostly_empty = (nan_counts > len(df.columns) * 0.8).sum()
    
    print(f"Completely empty rows: {completely_empty}")
    print(f"Mostly empty rows (>80% NaN): {mostly_empty}")
    
    # Check specific positions mentioned in errors
    print("\n--- Checking specific row positions ---")
    positions_to_check = [96, 193, 166, 265, 199]
    
    for pos in positions_to_check:
        if pos < len(df):
            print(f"\nRow {pos}:")
            row = df.iloc[pos]
            print(f"  Hour: '{row.get('Hour', 'N/A')}'")
            print(f"  Symbol: '{row.get('Symbol', 'N/A')}'")
            print(f"  Name: '{row.get('Name', 'N/A')}'")
            if pd.isna(row.get('Hour')) or pd.isna(row.get('Symbol')):
                print("  ⚠️  Contains NaN values!")
    
    # Look for pattern in problematic rows
    print("\n--- Pattern Analysis ---")
    
    # Check if there's a separator row or header row in the middle
    if 'Symbol' in df.columns:
        symbol_is_text = df['Symbol'].apply(lambda x: isinstance(x, str) and x == 'Symbol')
        if symbol_is_text.any():
            print(f"⚠️  Found {symbol_is_text.sum()} rows where Symbol column contains the text 'Symbol'")
            print("This suggests duplicate header rows in the data!")
            
    # Check last rows of file
    print("\n--- Last 5 rows ---")
    print(df.tail())
    
    # Try to identify where good data ends
    if 'Symbol' in df.columns and 'Hour' in df.columns:
        good_data_mask = df['Symbol'].isin(valid_symbols) & df['Hour'].notna()
        last_good_idx = df[good_data_mask].index.max()
        print(f"\n--- Data quality transition ---")
        print(f"Last good data row index: {last_good_idx}")
        print(f"Total rows after last good row: {len(df) - last_good_idx - 1}")
        
        if last_good_idx < len(df) - 1:
            print("\nRows after last good data:")
            print(df.iloc[last_good_idx:last_good_idx+5][['Hour', 'Symbol', 'Name']])

if __name__ == "__main__":
    deep_diagnose_csv()
