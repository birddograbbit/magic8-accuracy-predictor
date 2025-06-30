#!/usr/bin/env python3
"""
Diagnostic script to examine CSV file structure issues
"""

import pandas as pd
import os
import glob

def diagnose_csv_structure():
    """Check the structure of problematic CSV files"""
    
    # Files mentioned in the error log
    problematic_dates = [
        "2024-10-22-8F452",
        "2024-10-23-60531",
        "2024-10-24-5B3BC",
        "2024-10-25-CDA2B",
        "2024-10-28-ACB3F",
        "2024-10-29-2965B",
        "2024-10-30-34EB7",
        "2024-10-31-3D1F0"
    ]
    
    source_dir = "data/source"
    
    for dir_name in problematic_dates:
        dir_path = os.path.join(source_dir, dir_name)
        
        if not os.path.exists(dir_path):
            print(f"\n❌ Directory not found: {dir_path}")
            continue
            
        print(f"\n📁 Checking {dir_name}:")
        
        # Find profit files
        profit_files = glob.glob(os.path.join(dir_path, "profit*.csv"))
        
        if not profit_files:
            print("  No profit files found")
            continue
            
        filepath = profit_files[0]
        print(f"  File: {os.path.basename(filepath)}")
        
        try:
            # Read the CSV
            df = pd.read_csv(filepath)
            
            # Print basic info
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {list(df.columns)}")
            
            # Check Hour column specifically
            if 'Hour' in df.columns:
                print("\n  Hour column analysis:")
                print(f"    First 5 values: {df['Hour'].head().tolist()}")
                print(f"    Unique values (first 10): {df['Hour'].unique()[:10].tolist()}")
                print(f"    Data type: {df['Hour'].dtype}")
                
                # Check for position 96 (mentioned in error)
                if len(df) > 96:
                    print(f"    Value at position 96: {df['Hour'].iloc[96]}")
                    print(f"    Row 96 data:")
                    print(df.iloc[96].to_dict())
            else:
                print("  ❌ No 'Hour' column found!")
                
            # Check for other time-related columns
            time_columns = [col for col in df.columns if 'time' in col.lower() or 'hour' in col.lower() or 'date' in col.lower()]
            if time_columns:
                print(f"\n  Time-related columns found: {time_columns}")
                
            # Show first few rows
            print("\n  First 3 rows:")
            print(df.head(3).to_string())
            
        except Exception as e:
            print(f"  ❌ Error reading file: {str(e)}")
    
    # Also check a working file for comparison
    print("\n\n📋 Checking a known working file for comparison:")
    working_dir = "2023-11-13-94502"  # From the document
    working_path = os.path.join(source_dir, working_dir)
    
    if os.path.exists(working_path):
        profit_files = glob.glob(os.path.join(working_path, "profit*.csv"))
        if profit_files:
            try:
                df = pd.read_csv(profit_files[0])
                print(f"  File: {os.path.basename(profit_files[0])}")
                print(f"  Columns: {list(df.columns)}")
                if 'Hour' in df.columns:
                    print(f"  Hour column sample: {df['Hour'].head().tolist()}")
            except Exception as e:
                print(f"  Error: {str(e)}")

if __name__ == "__main__":
    diagnose_csv_structure()
