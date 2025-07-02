#!/usr/bin/env python
"""
Quick test script to verify IBKR data loading works correctly after timezone fixes
"""

import pandas as pd
import os
from datetime import datetime

def test_ibkr_data_loading():
    """Test loading IBKR data files and check timezone handling"""
    
    print("Testing IBKR Data Loading...")
    print("=" * 60)
    
    ibkr_path = 'data/ibkr'
    
    # List all CSV files
    csv_files = [f for f in os.listdir(ibkr_path) if f.endswith('.csv')]
    
    for file in csv_files:
        filepath = os.path.join(ibkr_path, file)
        print(f"\n📁 Testing: {file}")
        
        try:
            # Load the data
            df = pd.read_csv(filepath)
            print(f"  ✓ Loaded {len(df)} rows")
            
            # Check date column
            if 'date' in df.columns:
                # Parse dates
                df['date'] = pd.to_datetime(df['date'])
                
                # Check if timezone aware
                has_tz = df['date'].dt.tz is not None
                print(f"  ✓ Has timezone: {has_tz}")
                
                if has_tz:
                    # Show timezone
                    print(f"  ✓ Timezone: {df['date'].dt.tz}")
                    
                    # Convert to timezone-naive
                    df['date'] = df['date'].dt.tz_localize(None)
                    print(f"  ✓ Converted to timezone-naive")
                
                # Show date range
                print(f"  ✓ Date range: {df['date'].min()} to {df['date'].max()}")
                
                # Check ordering
                is_sorted = df['date'].is_monotonic_increasing
                print(f"  ✓ Data is sorted (oldest first): {is_sorted}")
                
                # Sample data
                print(f"  ✓ First timestamp: {df['date'].iloc[0]}")
                print(f"  ✓ Last timestamp: {df['date'].iloc[-1]}")
                
            else:
                print("  ⚠️  No 'date' column found")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Test complete!")

def test_normalized_data():
    """Test loading normalized trade data"""
    
    print("\n\nTesting Normalized Trade Data...")
    print("=" * 60)
    
    normalized_path = 'data/normalized/normalized_aggregated.csv'
    
    if os.path.exists(normalized_path):
        try:
            # Load the data
            df = pd.read_csv(normalized_path, nrows=100)  # Just first 100 rows for testing
            print(f"✓ Loaded normalized data")
            
            if 'interval_datetime' in df.columns:
                # Parse dates
                df['interval_datetime'] = pd.to_datetime(df['interval_datetime'])
                
                # Check if timezone aware
                has_tz = df['interval_datetime'].dt.tz is not None
                print(f"✓ Has timezone: {has_tz}")
                
                if has_tz:
                    print(f"✓ Timezone: {df['interval_datetime'].dt.tz}")
                
                # Show sample
                print(f"✓ Sample timestamp: {df['interval_datetime'].iloc[0]}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    else:
        print(f"⚠️  Normalized data not found at {normalized_path}")
    
    print("=" * 60)

if __name__ == "__main__":
    test_ibkr_data_loading()
    test_normalized_data()
