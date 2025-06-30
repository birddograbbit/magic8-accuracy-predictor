#!/usr/bin/env python3
"""
Robust Magic8 Data Processing Pipeline
Handles all data format changes and edge cases in CSV files
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import json
import re

class Magic8DataProcessor:
    def __init__(self, source_dir='data/source', output_dir='data/normalized'):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.all_data = []
        self.format_stats = {
            'old_format': 0,
            'new_format': 0,
            'trades_format': 0,
            'errors': 0,
            'timestamp_errors': 0,
            'malformed_rows': 0,
            'recovered_rows': 0,
            'duplicate_headers': 0,
            'empty_rows': 0
        }
        self.valid_symbols = ['SPX', 'SPY', 'RUT', 'QQQ', 'XSP', 'NDX', 'AAPL', 'TSLA']
        self.valid_strategies = ['Butterfly', 'Iron Condor', 'Vertical', 'Sonar']
        
    def is_valid_time(self, time_str):
        """Check if a string is a valid time format"""
        if pd.isna(time_str):
            return False
        time_str = str(time_str).strip()
        # Check for HH:MM format
        if re.match(r'^\d{1,2}:\d{2}$', time_str):
            return True
        # Check for just hour
        if re.match(r'^\d{1,2}$', time_str):
            return True
        return False
        
    def clean_dataframe(self, df):
        """Remove duplicate headers, empty rows, and other data quality issues"""
        original_len = len(df)
        
        # Remove rows where Symbol column contains 'Symbol' (duplicate headers)
        if 'Symbol' in df.columns:
            duplicate_header_mask = df['Symbol'] == 'Symbol'
            duplicate_count = duplicate_header_mask.sum()
            if duplicate_count > 0:
                self.format_stats['duplicate_headers'] += duplicate_count
                df = df[~duplicate_header_mask]
                print(f"  Removed {duplicate_count} duplicate header rows")
        
        # Remove completely empty rows
        empty_mask = df.isna().all(axis=1)
        empty_count = empty_mask.sum()
        if empty_count > 0:
            self.format_stats['empty_rows'] += empty_count
            df = df[~empty_mask]
            print(f"  Removed {empty_count} empty rows")
        
        # Remove rows where Symbol is not in valid symbols list
        if 'Symbol' in df.columns:
            invalid_symbol_mask = ~df['Symbol'].isin(self.valid_symbols)
            invalid_count = invalid_symbol_mask.sum()
            if invalid_count > 0:
                # Before removing, check if these rows might have shifted data
                shifted_rows = 0
                for idx in df[invalid_symbol_mask].index:
                    row = df.loc[idx]
                    # Check if Hour column contains a symbol (indicating shifted data)
                    if 'Hour' in df.columns and row['Hour'] in self.valid_symbols:
                        shifted_rows += 1
                
                if shifted_rows > 0:
                    print(f"  Found {shifted_rows} rows with shifted data (symbol in Hour column)")
                    
                self.format_stats['malformed_rows'] += invalid_count
                df = df[~invalid_symbol_mask]
                print(f"  Removed {invalid_count} rows with invalid symbols")
        
        # Reset index after cleaning
        df = df.reset_index(drop=True)
        
        cleaned_count = original_len - len(df)
        if cleaned_count > 0:
            print(f"  Total rows removed during cleaning: {cleaned_count}")
            
        return df
        
    def process_profit_file(self, filepath, date_str):
        """Process a profit CSV file, handling format changes and data quality issues"""
        try:
            # Read the CSV
            df = pd.read_csv(filepath)
            
            # Clean the dataframe first
            df = self.clean_dataframe(df)
            
            if len(df) == 0:
                print(f"Warning: No valid data after cleaning in {filepath}")
                return None
            
            # Add date
            df['date'] = date_str
            
            # Handle timestamp creation
            if 'Hour' in df.columns:
                timestamps = []
                valid_time_count = 0
                
                for idx, row in df.iterrows():
                    hour_val = row['Hour']
                    
                    if self.is_valid_time(hour_val):
                        try:
                            # For HH:MM format
                            if ':' in str(hour_val):
                                ts = pd.to_datetime(f"{date_str} {hour_val}")
                            else:
                                # For just hour number
                                ts = pd.to_datetime(f"{date_str} {int(hour_val):02d}:00")
                            timestamps.append(ts)
                            valid_time_count += 1
                        except:
                            timestamps.append(pd.to_datetime(date_str))
                            self.format_stats['timestamp_errors'] += 1
                    else:
                        timestamps.append(pd.to_datetime(date_str))
                        if pd.notna(hour_val) and hour_val not in self.valid_symbols:
                            self.format_stats['timestamp_errors'] += 1
                
                df['timestamp'] = timestamps
                
                if valid_time_count < len(df) * 0.5:
                    print(f"  Warning: Only {valid_time_count}/{len(df)} rows had valid times")
            else:
                df['timestamp'] = pd.to_datetime(date_str)
            
            # Determine profit column
            if 'Profit' in df.columns:
                df['profit'] = pd.to_numeric(df['Profit'], errors='coerce')
                df['profit_source'] = 'Profit'
                self.format_stats['old_format'] += 1
                
            elif 'Raw' in df.columns and 'Managed' in df.columns:
                df['profit'] = pd.to_numeric(df['Raw'], errors='coerce')
                df['profit_source'] = 'Raw'
                df['managed_profit'] = pd.to_numeric(df['Managed'], errors='coerce')
                self.format_stats['new_format'] += 1
                
            else:
                print(f"Warning: No profit column found in {filepath}")
                self.format_stats['errors'] += 1
                return None
            
            # Standardize columns
            df['symbol'] = df['Symbol']
            df['strategy'] = df['Name']
            df['price'] = pd.to_numeric(df['Price'], errors='coerce')
            df['premium'] = pd.to_numeric(df['Premium'], errors='coerce')
            
            # Optional columns
            df['predicted'] = pd.to_numeric(df.get('Predicted', np.nan), errors='coerce')
            df['closed'] = pd.to_numeric(df.get('Closed', np.nan), errors='coerce')
            df['expired'] = df.get('Expired', np.nan)
            df['risk'] = pd.to_numeric(df.get('Risk', np.nan), errors='coerce')
            df['reward'] = pd.to_numeric(df.get('Reward', np.nan), errors='coerce')
            df['ratio'] = pd.to_numeric(df.get('Ratio', np.nan), errors='coerce')
            df['trade_description'] = df.get('Trade', '').astype(str)
            
            # Source info
            df['source_file'] = os.path.basename(filepath)
            df['format_year'] = int(date_str[:4])
            
            # Final validation
            required_checks = {
                'symbol': lambda x: x in self.valid_symbols,
                'strategy': lambda x: pd.notna(x) and (x in self.valid_strategies or 
                                                      any(s in str(x) for s in self.valid_strategies)),
                'profit': lambda x: pd.notna(x) and not np.isinf(x),
                'timestamp': lambda x: pd.notna(x)
            }
            
            valid_mask = pd.Series(True, index=df.index)
            for field, check in required_checks.items():
                if field in df.columns:
                    field_valid = df[field].apply(check)
                    valid_mask &= field_valid
            
            invalid_count = (~valid_mask).sum()
            if invalid_count > 0:
                print(f"  Final validation: dropping {invalid_count} invalid rows")
                df = df[valid_mask]
            
            if len(df) == 0:
                print(f"Error: No valid data remaining after validation in {filepath}")
                return None
                
            return df
            
        except Exception as e:
            print(f"Error processing {filepath}: {str(e)}")
            import traceback
            traceback.print_exc()
            self.format_stats['errors'] += 1
            return None
    
    def process_trades_file(self, filepath, date_str):
        """Process newer trades CSV files (after Aug 2024)"""
        try:
            df = pd.read_csv(filepath)
            
            # Clean the dataframe
            df = self.clean_dataframe(df)
            
            if len(df) == 0:
                print(f"Warning: No valid data after cleaning in {filepath}")
                return None
            
            df['date'] = date_str
            
            # Handle timestamp
            if 'Date' in df.columns and 'Time' in df.columns:
                df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], errors='coerce')
                failed = df['timestamp'].isna().sum()
                if failed > 0:
                    df.loc[df['timestamp'].isna(), 'timestamp'] = pd.to_datetime(date_str)
                    self.format_stats['timestamp_errors'] += failed
            else:
                df['timestamp'] = pd.to_datetime(date_str)
                
            # Map columns
            df['symbol'] = df['Symbol']
            df['strategy'] = df['Name']
            df['price'] = pd.to_numeric(df.get('Closing', np.nan), errors='coerce')
            df['premium'] = pd.to_numeric(df['Premium'], errors='coerce')
            df['predicted'] = pd.to_numeric(df.get('Predicted', np.nan), errors='coerce')
            df['closed'] = pd.to_numeric(df.get('Closing', np.nan), errors='coerce')
            df['risk'] = pd.to_numeric(df['Risk'], errors='coerce')
            df['trade_description'] = df['Trade'].astype(str)
            
            df['profit'] = np.nan
            df['profit_source'] = 'needs_calculation'
            
            df['source_file'] = os.path.basename(filepath)
            df['format_year'] = int(date_str[:4])
            
            self.format_stats['trades_format'] += 1
            
            # Validate
            valid_mask = df['symbol'].isin(self.valid_symbols) & df['symbol'].notna()
            invalid_count = (~valid_mask).sum()
            if invalid_count > 0:
                print(f"  Dropping {invalid_count} invalid rows from trades file")
                df = df[valid_mask]
                
            return df
            
        except Exception as e:
            print(f"Error processing trades file {filepath}: {str(e)}")
            self.format_stats['errors'] += 1
            return None
    
    def process_all_files(self):
        """Process all source files"""
        print(f"Processing files from {self.source_dir}...")
        
        dirs = sorted([d for d in os.listdir(self.source_dir) 
                      if os.path.isdir(os.path.join(self.source_dir, d))])
        
        total_dirs = len(dirs)
        print(f"Found {total_dirs} directories to process\n")
        
        processed_count = 0
        
        for i, dir_name in enumerate(dirs):
            if i % 50 == 0 and i > 0:
                print(f"\nProgress: {i}/{total_dirs} directories processed...")
                
            dir_path = os.path.join(self.source_dir, dir_name)
            date_str = dir_name[:10]
            
            # Validate date
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                continue
            
            # Process profit files
            profit_files = glob.glob(os.path.join(dir_path, 'profit*.csv'))
            if profit_files:
                df = self.process_profit_file(profit_files[0], date_str)
                if df is not None and len(df) > 0:
                    self.all_data.append(df)
                    processed_count += 1
            
            # Process trades files
            trades_files = glob.glob(os.path.join(dir_path, 'trades*.csv'))
            if trades_files and not profit_files:
                df = self.process_trades_file(trades_files[0], date_str)
                if df is not None and len(df) > 0:
                    self.all_data.append(df)
                    processed_count += 1
        
        print(f"\n✅ Processing complete!")
        print(f"Successfully processed {processed_count} files out of {total_dirs} directories")
        print(f"\nData quality statistics:")
        for key, value in self.format_stats.items():
            if value > 0:
                print(f"  {key}: {value:,}")
    
    def calculate_missing_profits(self, df):
        """Calculate profits for trades without them"""
        mask = df['profit_source'] == 'needs_calculation'
        
        if mask.sum() > 0:
            print(f"\nCalculating profits for {mask.sum()} trades...")
            
            calculated = 0
            for idx in df[mask].index:
                row = df.loc[idx]
                
                if pd.isna(row['closed']) or pd.isna(row['predicted']):
                    continue
                    
                if row['strategy'] in ['Iron Condor', 'Vertical']:
                    if abs(row['closed'] - row['predicted']) <= row['predicted'] * 0.01:
                        df.loc[idx, 'profit'] = row['premium']
                    else:
                        df.loc[idx, 'profit'] = -row['risk'] if pd.notna(row['risk']) else -row['premium'] * 10
                    calculated += 1
                        
                elif row['strategy'] in ['Butterfly', 'Sonar']:
                    if abs(row['closed'] - row['predicted']) <= row['predicted'] * 0.005:
                        df.loc[idx, 'profit'] = row.get('reward', row['premium'] * 2) - row['premium']
                    else:
                        df.loc[idx, 'profit'] = -row['premium']
                    calculated += 1
            
            print(f"  Calculated profits for {calculated} trades")
        
        return df
    
    def save_normalized_data(self):
        """Save all processed data"""
        if not self.all_data:
            print("No data to save!")
            return None
            
        print("\nCombining all data...")
        df = pd.concat(self.all_data, ignore_index=True)
        
        # Calculate missing profits
        df = self.calculate_missing_profits(df)
        
        # Create win column
        df['win'] = (df['profit'] > 0).astype(int)
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        # Save
        os.makedirs(self.output_dir, exist_ok=True)
        output_file = os.path.join(self.output_dir, 'normalized_complete.csv')
        df.to_csv(output_file, index=False)
        
        print(f"\n✅ Saved {len(df):,} trades to {output_file}")
        
        # Summary statistics
        print("\n=== SUMMARY STATISTICS ===")
        print(f"Total trades: {len(df):,}")
        print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"Overall win rate: {df['win'].mean():.2%}")
        print(f"Total profit: ${df['profit'].sum():,.2f}")
        
        # By strategy
        print("\n=== BY STRATEGY ===")
        for strategy in sorted(df['strategy'].unique()):
            strat_df = df[df['strategy'] == strategy]
            print(f"\n{strategy}:")
            print(f"  Trades: {len(strat_df):,}")
            print(f"  Win rate: {strat_df['win'].mean():.2%}")
            print(f"  Total profit: ${strat_df['profit'].sum():,.2f}")
            print(f"  Avg profit: ${strat_df['profit'].mean():.2f}")
        
        # By year
        print("\n=== BY YEAR ===")
        df['year'] = df['timestamp'].dt.year
        for year in sorted(df['year'].unique()):
            year_df = df[df['year'] == year]
            print(f"\n{year}:")
            print(f"  Trades: {len(year_df):,}")
            print(f"  Win rate: {year_df['win'].mean():.2%}")
            print(f"  Total profit: ${year_df['profit'].sum():,.2f}")
        
        # Save stats
        stats = {
            'total_trades': len(df),
            'date_range': f"{df['timestamp'].min()} to {df['timestamp'].max()}",
            'overall_win_rate': float(df['win'].mean()),
            'total_profit': float(df['profit'].sum()),
            'format_stats': self.format_stats,
            'symbols_processed': sorted(df['symbol'].unique().tolist()),
            'strategies_found': sorted(df['strategy'].unique().tolist())
        }
        
        stats_file = os.path.join(self.output_dir, 'processing_stats.json')
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
            
        print(f"\n✅ Stats saved to {stats_file}")
        
        return df

def main():
    """Run the complete data processing pipeline"""
    processor = Magic8DataProcessor()
    processor.process_all_files()
    df = processor.save_normalized_data()
    
    if df is not None:
        print("\n🎉 Data processing complete!")
        print("Next steps:")
        print("1. Run: python src/phase1_data_preparation.py")
        print("2. Run: python src/models/xgboost_baseline.py")
    
if __name__ == "__main__":
    main()
