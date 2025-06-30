#!/usr/bin/env python3
"""
Fixed Magic8 Data Processing Pipeline
Properly handles summary statistics at the end of CSV files
Fixed JSON serialization for numpy types
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
            'summary_rows_removed': 0,
            'total_rows_processed': 0
        }
        self.valid_symbols = ['SPX', 'SPY', 'RUT', 'QQQ', 'XSP', 'NDX', 'AAPL', 'TSLA']
        self.valid_strategies = ['Butterfly', 'Iron Condor', 'Vertical', 'Sonar']
        
    def is_valid_date(self, date_str):
        """Check if a string is a valid date in MM-DD-YYYY format"""
        if pd.isna(date_str):
            return False
        try:
            # Try to parse the date
            datetime.strptime(str(date_str), '%m-%d-%Y')
            return True
        except:
            return False
            
    def is_valid_time(self, time_str):
        """Check if a string is a valid time format"""
        if pd.isna(time_str):
            return False
        time_str = str(time_str).strip()
        # Check for HH:MM format
        if re.match(r'^\d{1,2}:\d{2}$', time_str):
            return True
        return False
        
    def clean_dataframe(self, df):
        """Remove summary statistics and invalid rows from dataframe"""
        original_len = len(df)
        
        # Remove rows where Day column doesn't contain a valid date
        # This will remove the summary statistics at the end
        if 'Day' in df.columns:
            valid_date_mask = df['Day'].apply(self.is_valid_date)
            invalid_date_count = (~valid_date_mask).sum()
            
            if invalid_date_count > 0:
                # Log what we're removing
                print(f"  Removing {invalid_date_count} rows with invalid dates (likely summary stats)")
                # Show a sample of what's being removed
                invalid_rows = df[~valid_date_mask]
                if len(invalid_rows) <= 5:
                    print(f"  Sample removed: {invalid_rows['Day'].tolist()}")
                else:
                    print(f"  Sample removed: {invalid_rows['Day'].head(5).tolist()}")
                
                self.format_stats['summary_rows_removed'] += int(invalid_date_count)
                df = df[valid_date_mask].copy()
        
        # Also remove rows where Symbol is not in valid symbols
        if 'Symbol' in df.columns:
            valid_symbol_mask = df['Symbol'].isin(self.valid_symbols)
            invalid_symbol_count = (~valid_symbol_mask).sum()
            
            if invalid_symbol_count > 0:
                print(f"  Removing {invalid_symbol_count} rows with invalid symbols")
                df = df[valid_symbol_mask].copy()
        
        # Remove any completely empty rows
        if len(df) > 0:
            non_empty_mask = ~df.isna().all(axis=1)
            empty_count = (~non_empty_mask).sum()
            if empty_count > 0:
                print(f"  Removing {empty_count} empty rows")
                df = df[non_empty_mask].copy()
        
        # Reset index after cleaning
        df = df.reset_index(drop=True)
        
        cleaned_count = original_len - len(df)
        if cleaned_count > 0:
            print(f"  Total rows cleaned: {cleaned_count} (from {original_len} to {len(df)})")
            
        return df
        
    def process_profit_file(self, filepath, date_str):
        """Process a profit CSV file, handling format changes"""
        try:
            # Read the CSV
            df = pd.read_csv(filepath)
            
            # Clean the dataframe first (remove summary stats)
            df = self.clean_dataframe(df)
            
            if len(df) == 0:
                print(f"Warning: No valid data after cleaning in {filepath}")
                return None
            
            # Add date column for consistency
            df['date'] = date_str
            
            # Create timestamp - handle both old and new date formats
            if 'Day' in df.columns and 'Hour' in df.columns:
                timestamps = []
                
                for idx, row in df.iterrows():
                    try:
                        # Combine Day and Hour
                        day_str = str(row['Day'])
                        hour_str = str(row['Hour'])
                        
                        if self.is_valid_time(hour_str):
                            # Parse the full datetime
                            datetime_str = f"{day_str} {hour_str}"
                            ts = pd.to_datetime(datetime_str, format='%m-%d-%Y %H:%M')
                        else:
                            # Just use the date
                            ts = pd.to_datetime(day_str, format='%m-%d-%Y')
                            
                        timestamps.append(ts)
                    except Exception as e:
                        # Fallback to just the directory date
                        timestamps.append(pd.to_datetime(date_str))
                        self.format_stats['timestamp_errors'] += 1
                
                df['timestamp'] = timestamps
            else:
                # No Day/Hour columns, use directory date
                df['timestamp'] = pd.to_datetime(date_str)
            
            # Determine profit column based on available columns
            if 'Profit' in df.columns:
                # Old format (before Nov 2023)
                df['profit'] = pd.to_numeric(df['Profit'], errors='coerce')
                df['profit_source'] = 'Profit'
                self.format_stats['old_format'] += 1
                
            elif 'Raw' in df.columns and 'Managed' in df.columns:
                # New format (after Nov 2023)
                df['profit'] = pd.to_numeric(df['Raw'], errors='coerce')
                df['profit_source'] = 'Raw'
                df['managed_profit'] = pd.to_numeric(df['Managed'], errors='coerce')
                self.format_stats['new_format'] += 1
                
            else:
                print(f"Warning: No profit column found in {filepath}")
                self.format_stats['errors'] += 1
                return None
            
            # Standardize column names
            df['symbol'] = df['Symbol']
            df['strategy'] = df['Name']
            df['price'] = pd.to_numeric(df['Price'], errors='coerce')
            df['premium'] = pd.to_numeric(df['Premium'], errors='coerce')
            
            # Handle optional columns
            df['predicted'] = pd.to_numeric(df.get('Predicted', np.nan), errors='coerce')
            df['closed'] = pd.to_numeric(df.get('Closed', np.nan), errors='coerce')
            
            # Handle Expired column
            if 'Expired' in df.columns:
                # Convert string True/False to boolean
                df['expired'] = df['Expired'].astype(str).str.lower() == 'true'
            else:
                df['expired'] = np.nan
                
            # Risk/Reward handling
            df['risk'] = pd.to_numeric(df.get('Risk', np.nan), errors='coerce')
            df['reward'] = pd.to_numeric(df.get('Reward', np.nan), errors='coerce')
            df['ratio'] = pd.to_numeric(df.get('Ratio', np.nan), errors='coerce')
            
            # Trade description
            df['trade_description'] = df.get('Trade', '').astype(str)
            
            # Add source info
            df['source_file'] = os.path.basename(filepath)
            df['format_year'] = int(date_str[:4])
            
            # Final validation - ensure we have valid trading data
            valid_mask = (
                df['symbol'].isin(self.valid_symbols) & 
                df['strategy'].notna() & 
                df['profit'].notna() & 
                ~np.isinf(df['profit']) &
                df['timestamp'].notna()
            )
            
            invalid_count = (~valid_mask).sum()
            if invalid_count > 0:
                print(f"  Dropping {invalid_count} rows that failed final validation")
                df = df[valid_mask]
            
            self.format_stats['total_rows_processed'] += len(df)
            
            return df
            
        except Exception as e:
            print(f"Error processing {filepath}: {str(e)}")
            self.format_stats['errors'] += 1
            return None
    
    def process_trades_file(self, filepath, date_str):
        """Process newer trades CSV files (after Aug 2024)"""
        try:
            df = pd.read_csv(filepath)
            
            # Clean the dataframe
            df = self.clean_dataframe(df)
            
            if len(df) == 0:
                return None
            
            # These files have a different structure
            df['date'] = date_str
            
            # Handle timestamp creation for trades files
            if 'Date' in df.columns and 'Time' in df.columns:
                df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], errors='coerce')
                failed_timestamps = df['timestamp'].isna().sum()
                if failed_timestamps > 0:
                    df.loc[df['timestamp'].isna(), 'timestamp'] = pd.to_datetime(date_str)
            else:
                df['timestamp'] = pd.to_datetime(date_str)
                
            df['symbol'] = df['Symbol']
            df['strategy'] = df['Name']
            df['price'] = pd.to_numeric(df.get('Closing', np.nan), errors='coerce')
            df['premium'] = pd.to_numeric(df['Premium'], errors='coerce')
            df['predicted'] = pd.to_numeric(df.get('Predicted', np.nan), errors='coerce')
            df['closed'] = pd.to_numeric(df.get('Closing', np.nan), errors='coerce')
            df['risk'] = pd.to_numeric(df['Risk'], errors='coerce')
            df['trade_description'] = df['Trade'].astype(str)
            
            # Trades files don't have profit - mark for later calculation
            df['profit'] = np.nan
            df['profit_source'] = 'needs_calculation'
            
            df['source_file'] = os.path.basename(filepath)
            df['format_year'] = int(date_str[:4])
            
            self.format_stats['trades_format'] += 1
            self.format_stats['total_rows_processed'] += len(df)
            
            return df
            
        except Exception as e:
            print(f"Error processing trades file {filepath}: {str(e)}")
            self.format_stats['errors'] += 1
            return None
    
    def process_all_files(self):
        """Process all source files"""
        print(f"Processing files from {self.source_dir}...")
        
        # Get all subdirectories
        dirs = sorted([d for d in os.listdir(self.source_dir) 
                      if os.path.isdir(os.path.join(self.source_dir, d))])
        
        total_dirs = len(dirs)
        print(f"Found {total_dirs} directories to process")
        
        processed_count = 0
        
        for i, dir_name in enumerate(dirs):
            if i % 50 == 0:
                print(f"\nProcessing directory {i+1}/{total_dirs}...")
                
            dir_path = os.path.join(self.source_dir, dir_name)
            
            # Extract date from directory name
            date_str = dir_name[:10]  # e.g., "2023-11-13"
            
            # Validate date format
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                print(f"Warning: Invalid date format in directory name: {dir_name}")
                continue
            
            # Look for profit files
            profit_files = glob.glob(os.path.join(dir_path, 'profit*.csv'))
            if profit_files:
                df = self.process_profit_file(profit_files[0], date_str)
                if df is not None and len(df) > 0:
                    self.all_data.append(df)
                    processed_count += 1
            
            # Also check for trades files (newer format)
            trades_files = glob.glob(os.path.join(dir_path, 'trades*.csv'))
            if trades_files and not profit_files:  # Only if no profit file
                df = self.process_trades_file(trades_files[0], date_str)
                if df is not None and len(df) > 0:
                    self.all_data.append(df)
                    processed_count += 1
        
        print(f"\nProcessing complete!")
        print(f"Successfully processed {processed_count} files out of {total_dirs} directories")
        print(f"Format statistics: {self.format_stats}")
    
    def calculate_missing_profits(self, df):
        """Calculate profits for trades that don't have them"""
        mask = df['profit_source'] == 'needs_calculation'
        
        if mask.sum() > 0:
            print(f"Calculating profits for {mask.sum()} trades...")
            
            # Simple profit calculation based on strategy type
            for idx in df[mask].index:
                row = df.loc[idx]
                
                if pd.isna(row['closed']) or pd.isna(row['predicted']):
                    continue
                    
                if row['strategy'] in ['Iron Condor', 'Vertical']:
                    # Credit strategies
                    if abs(row['closed'] - row['predicted']) <= row['predicted'] * 0.01:
                        df.loc[idx, 'profit'] = row['premium']
                    else:
                        df.loc[idx, 'profit'] = -row['risk'] if pd.notna(row['risk']) else -row['premium'] * 10
                        
                elif row['strategy'] in ['Butterfly', 'Sonar']:
                    # Debit strategies
                    if abs(row['closed'] - row['predicted']) <= row['predicted'] * 0.005:
                        df.loc[idx, 'profit'] = row.get('reward', row['premium'] * 2) - row['premium']
                    else:
                        df.loc[idx, 'profit'] = -row['premium']
        
        return df
    
    def save_normalized_data(self):
        """Combine and save all processed data"""
        if not self.all_data:
            print("No data to save!")
            return
            
        print("\nCombining all data...")
        df = pd.concat(self.all_data, ignore_index=True)
        
        # Calculate any missing profits
        df = self.calculate_missing_profits(df)
        
        # Create win column
        df['win'] = (df['profit'] > 0).astype(int)
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        # Save to CSV
        os.makedirs(self.output_dir, exist_ok=True)
        output_file = os.path.join(self.output_dir, 'normalized_complete.csv')
        df.to_csv(output_file, index=False)
        
        print(f"\n✅ Saved {len(df)} trades to {output_file}")
        
        # Print summary statistics
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
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj
        
        # Save stats
        stats = {
            'total_trades': int(len(df)),
            'date_range': f"{df['timestamp'].min()} to {df['timestamp'].max()}",
            'overall_win_rate': float(df['win'].mean()),
            'total_profit': float(df['profit'].sum()),
            'format_stats': convert_numpy_types(self.format_stats),
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
    
    print("\n🎉 Data processing complete!")
    print("You can now use 'data/normalized/normalized_complete.csv' for your ML pipeline")
    
if __name__ == "__main__":
    main()
