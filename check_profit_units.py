#!/usr/bin/env python3
"""
Check profit values in source data to understand units
"""

import pandas as pd
import numpy as np
import os
import glob

def check_profit_units():
    """Analyze profit values to determine if they're in dollars or cents"""
    
    print("Checking profit values in source files...")
    print("="*60)
    
    # Sample files from different periods
    test_files = [
        "data/source/2023-01-24-98F8D/profit 20230124-211517.csv",
        "data/source/2023-11-22-5FB64/profit 20231122-212405.csv",  # After format change
        "data/source/2024-06-10-2CD32/profit 20240610-200703.csv",
        "data/source/2025-01-15-26F27/profit 20250115-210718.csv"
    ]
    
    all_profits = []
    
    for filepath in test_files:
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue
            
        print(f"\nAnalyzing: {os.path.basename(filepath)}")
        df = pd.read_csv(filepath)
        
        # Remove summary stats
        if 'Day' in df.columns:
            # Simple date validation
            valid_mask = df['Day'].astype(str).str.contains('-')
            df = df[valid_mask]
        
        # Check which profit columns exist
        profit_cols = []
        if 'Profit' in df.columns:
            profit_cols.append('Profit')
        if 'Raw' in df.columns:
            profit_cols.append('Raw')
        if 'Managed' in df.columns:
            profit_cols.append('Managed')
            
        print(f"Profit columns found: {profit_cols}")
        
        for col in profit_cols:
            profits = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(profits) > 0:
                print(f"\n{col} column statistics:")
                print(f"  Count: {len(profits)}")
                print(f"  Mean: ${profits.mean():.2f}")
                print(f"  Median: ${profits.median():.2f}")
                print(f"  Min: ${profits.min():.2f}")
                print(f"  Max: ${profits.max():.2f}")
                print(f"  Sample values: {profits.head(10).tolist()}")
                
                all_profits.extend(profits.tolist())
                
                # Check if values look like cents (all integers or values > 100 for small trades)
                if col in ['Raw', 'Managed']:
                    # For Iron Condor with 0.40 premium, profit should be 40 cents or $0.40
                    # But if showing as 40.0, it's likely cents
                    small_wins = profits[(profits > 0) & (profits < 100)]
                    if len(small_wins) > 0:
                        print(f"  Small wins sample: {small_wins.head(5).tolist()}")
                        
                    # Check against premium values
                    if 'Premium' in df.columns and 'Strategy' in df.columns:
                        # Get Iron Condor trades
                        ic_mask = df['Name'] == 'Iron Condor'
                        if ic_mask.sum() > 0:
                            ic_df = df[ic_mask].copy()
                            ic_df['profit_num'] = pd.to_numeric(ic_df[col], errors='coerce')
                            ic_df['premium_num'] = pd.to_numeric(ic_df['Premium'], errors='coerce')
                            
                            # For winning IC trades, profit should equal premium
                            ic_wins = ic_df[ic_df['profit_num'] > 0]
                            if len(ic_wins) > 0:
                                print(f"\n  Iron Condor analysis:")
                                print(f"    Sample IC wins (first 5):")
                                for idx in ic_wins.index[:5]:
                                    premium = ic_wins.loc[idx, 'premium_num']
                                    profit = ic_wins.loc[idx, 'profit_num']
                                    print(f"      Premium: ${premium:.2f}, Profit: ${profit:.2f}")
    
    # Overall analysis
    if all_profits:
        all_profits = np.array(all_profits)
        print("\n" + "="*60)
        print("OVERALL PROFIT ANALYSIS")
        print("="*60)
        print(f"Total profit values analyzed: {len(all_profits)}")
        print(f"Values that are integers: {np.sum(all_profits == all_profits.astype(int))}")
        print(f"Values > 100: {np.sum(all_profits > 100)}")
        print(f"Values between 0.01 and 1: {np.sum((all_profits > 0.01) & (all_profits < 1))}")
        
        # If most values are > 10 and integers, likely cents
        if np.median(np.abs(all_profits)) > 10:
            print("\n⚠️  LIKELY ISSUE: Profits appear to be in CENTS, not dollars!")
            print("   Median absolute value > 10 suggests cent units")
            print(f"   Converting to dollars would give median profit: ${np.median(np.abs(all_profits))/100:.2f}")

if __name__ == "__main__":
    check_profit_units()
