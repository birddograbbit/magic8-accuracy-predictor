#!/usr/bin/env python3
"""
Check for duplicate header rows in CSV files
"""

import pandas as pd
import os
import glob

def check_duplicate_headers():
    """Check CSV files for duplicate header rows"""
    
    # Files with known issues
    problem_files = [
        "data/source/2023-01-13-8D96E/profit 20230113-212247.csv",
        "data/source/2023-01-13-BF316/profit 20230113-224724.csv",
        "data/source/2023-01-19-301BF/profit 20230119-211240.csv",
        "data/source/2024-10-22-8F452/profit 20241022-200705.csv"
    ]
    
    for filepath in problem_files:
        if not os.path.exists(filepath):
            continue
            
        print(f"\n{'='*60}")
        print(f"Checking: {os.path.basename(filepath)}")
        print('='*60)
        
        # Read file line by line to find duplicate headers
        with open(filepath, 'r') as f:
            lines = f.readlines()
            
        # Find the header line
        header_line = lines[0].strip()
        header_columns = header_line.split(',')
        print(f"Header columns: {header_columns[:5]}...")  # Show first 5
        
        # Look for duplicate headers
        duplicate_positions = []
        for i, line in enumerate(lines[1:], 1):  # Skip first line
            if line.strip() == header_line:
                duplicate_positions.append(i)
                
        if duplicate_positions:
            print(f"\n⚠️  Found {len(duplicate_positions)} duplicate header rows at positions: {duplicate_positions[:10]}")
            
            # Show context around first duplicate
            if duplicate_positions:
                pos = duplicate_positions[0]
                print(f"\nContext around duplicate header at line {pos}:")
                for j in range(max(0, pos-2), min(len(lines), pos+3)):
                    prefix = ">>>" if j == pos else "   "
                    print(f"{prefix} Line {j}: {lines[j].strip()[:100]}...")
        else:
            print("✅ No duplicate headers found")
            
        # Now check with pandas
        print("\nChecking with pandas...")
        try:
            df = pd.read_csv(filepath)
            
            # Check if any row has 'Symbol' in the Symbol column
            if 'Symbol' in df.columns:
                symbol_duplicates = (df['Symbol'] == 'Symbol').sum()
                if symbol_duplicates > 0:
                    print(f"⚠️  Found {symbol_duplicates} rows where Symbol column contains 'Symbol'")
                    # Show indices
                    dup_indices = df[df['Symbol'] == 'Symbol'].index.tolist()
                    print(f"   At indices: {dup_indices[:10]}")
                    
            # Check Hour column at problematic indices
            if 'Hour' in df.columns:
                print(f"\nHour column at key positions:")
                positions = [96, 193, 166, 265, 199]
                for pos in positions:
                    if pos < len(df):
                        hour_val = df.iloc[pos]['Hour']
                        symbol_val = df.iloc[pos].get('Symbol', 'N/A')
                        print(f"  Position {pos}: Hour='{hour_val}', Symbol='{symbol_val}'")
                        
        except Exception as e:
            print(f"Error reading with pandas: {e}")

if __name__ == "__main__":
    check_duplicate_headers()
