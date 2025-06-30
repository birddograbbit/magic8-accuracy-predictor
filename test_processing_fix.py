#!/usr/bin/env python3
"""
Test the data processing fix on a problematic file
"""

import pandas as pd
import sys

def test_single_file():
    """Test processing of a single problematic file"""
    
    test_file = "data/source/2023-01-24-98F8D/profit 20230124-211517.csv"
    
    print(f"Testing file: {test_file}")
    print("="*60)
    
    # Read the full CSV
    df = pd.read_csv(test_file)
    print(f"Original shape: {df.shape}")
    
    # Check the tail for summary stats
    print("\nLast 10 rows of original data:")
    print(df.tail(10)[['Day', 'Hour', 'Symbol', 'Name']].to_string())
    
    # Apply the cleaning logic
    def is_valid_date(date_str):
        if pd.isna(date_str):
            return False
        try:
            from datetime import datetime
            datetime.strptime(str(date_str), '%m-%d-%Y')
            return True
        except:
            return False
    
    # Find rows with invalid dates
    invalid_date_mask = ~df['Day'].apply(is_valid_date)
    invalid_rows = df[invalid_date_mask]
    
    print(f"\nFound {len(invalid_rows)} rows with invalid dates:")
    if len(invalid_rows) > 0:
        print("Sample invalid Day values:")
        print(invalid_rows['Day'].unique()[:20])
    
    # Clean the dataframe
    clean_df = df[~invalid_date_mask].copy()
    print(f"\nCleaned shape: {clean_df.shape}")
    print(f"Rows removed: {len(df) - len(clean_df)}")
    
    # Check if all remaining rows have valid symbols
    valid_symbols = ['SPX', 'SPY', 'RUT', 'QQQ', 'XSP', 'NDX', 'AAPL', 'TSLA']
    if 'Symbol' in clean_df.columns:
        valid_symbol_count = clean_df['Symbol'].isin(valid_symbols).sum()
        print(f"\nRows with valid symbols: {valid_symbol_count}/{len(clean_df)}")
    
    # Test timestamp creation on cleaned data
    print("\nTesting timestamp creation...")
    try:
        from datetime import datetime
        
        test_rows = min(5, len(clean_df))
        for i in range(test_rows):
            row = clean_df.iloc[i]
            day_str = str(row['Day'])
            hour_str = str(row['Hour'])
            
            try:
                ts = pd.to_datetime(f"{day_str} {hour_str}", format='%m-%d-%Y %H:%M')
                print(f"  Row {i}: '{day_str} {hour_str}' -> {ts}")
            except Exception as e:
                print(f"  Row {i}: '{day_str} {hour_str}' -> ERROR: {e}")
    except Exception as e:
        print(f"Error in timestamp test: {e}")
    
    print("\n✅ Test complete!")
    
    # Now test with the actual processor
    print("\n" + "="*60)
    print("Testing with Magic8DataProcessor...")
    
    try:
        # Import the processor
        sys.path.append('.')
        from process_magic8_complete import Magic8DataProcessor
        
        processor = Magic8DataProcessor()
        result_df = processor.process_profit_file(test_file, "2023-01-24")
        
        if result_df is not None:
            print(f"✅ Successfully processed! Result shape: {result_df.shape}")
            print(f"   Date range: {result_df['timestamp'].min()} to {result_df['timestamp'].max()}")
            print(f"   Strategies: {result_df['strategy'].unique()}")
            print(f"   Total profit: ${result_df['profit'].sum():.2f}")
        else:
            print("❌ Processing returned None")
            
    except Exception as e:
        print(f"❌ Error in processor test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_file()
