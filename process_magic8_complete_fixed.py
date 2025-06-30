#!/usr/bin/env python3
"""
Fixed Magic8 Data Processing Pipeline
Handles all data format changes correctly and robustly handles timestamp parsing errors
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import json

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
            'timestamp_errors': 0
        }
        
    def process_profit_file(self, filepath, date_str):
        """Process a profit CSV file, handling format changes"""
        try:
            df = pd.read_csv(filepath)
            
            # Add date
            df['date'] = date_str
            
            # Handle timestamp creation more robustly
            if 'Hour' in df.columns:
                # Check if Hour column actually contains hour data
                # by trying to convert the first non-null value
                first_hour = df['Hour'].dropna().astype(str).iloc[0] if not df['Hour'].dropna().empty else None
                
                if first_hour and (first_hour.isdigit() or ':' in str(first_hour)):
                    # Hour column seems valid
                    try:
                        df['timestamp'] = pd.to_datetime(date_str + ' ' + df['Hour'].astype(str), 
                                                        format='%Y-%m-%d %H:%M', 
                                                        errors='coerce')
                    except:
                        # If format doesn't match, try without specific format
                        df['timestamp'] = pd.to_datetime(date_str + ' ' + df['Hour'].astype(str), 
                                                        errors='coerce')
                    
                    # Count how many timestamps failed
                    failed_timestamps = df['timestamp'].isna().sum()
                    if failed_timestamps > 0:
                        print(f"Warning: {failed_timestamps} timestamps failed to parse in {filepath}")
                        self.format_stats['timestamp_errors'] += failed_timestamps
                        
                        # For failed timestamps, just use the date
                        df.loc[df['timestamp'].isna(), 'timestamp'] = pd.to_datetime(date_str)
                else:
                    # Hour column contains non-time data (like symbols)
                    print(f"Warning: 'Hour' column contains non-time data in {filepath}, using date only")
                    df['timestamp'] = pd.to_datetime(date_str)
            else:
                # No Hour column, just use date
                df['timestamp'] = pd.to_datetime(date_str)
            
            # Determine profit column based on available columns
            if 'Profit' in df.columns:
                # Old format (before Nov 2023)
                df['profit'] = df['Profit']
                df['profit_source'] = 'Profit'
                self.format_stats['old_format'] += 1
                
            elif 'Raw' in df.columns and 'Managed' in df.columns:
                # New format (after Nov 2023)
                # Use Raw profit as the primary source
                df['profit'] = df['Raw']
                df['profit_source'] = 'Raw'
                df['managed_profit'] = df['Managed']
                self.format_stats['new_format'] += 1
                
            else:
                print(f"Warning: No profit column found in {filepath}")
                self.format_stats['errors'] += 1
                return None
            
            # Standardize column names
            df['symbol'] = df['Symbol']
            df['strategy'] = df['Name']
            df['price'] = df['Price']
            df['premium'] = df['Premium']
            
            # Handle different column availability
            df['predicted'] = df.get('Predicted', np.nan)
            df['closed'] = df.get('Closed', np.nan)
            
            # For old format, extract from Trade description if needed
            if 'Expired' in df.columns:
                df['expired'] = df['Expired']
            else:
                df['expired'] = np.nan
                
            # Risk/Reward handling
            df['risk'] = df.get('Risk', np.nan)
            df['reward'] = df.get('Reward', np.nan)
            df['ratio'] = df.get('Ratio', np.nan)
            
            # Trade description
            df['trade_description'] = df.get('Trade', '')
            
            # Add source info
            df['source_file'] = os.path.basename(filepath)
            df['format_year'] = int(date_str[:4])
            
            # Filter out any rows where critical fields are missing
            required_fields = ['symbol', 'strategy', 'profit']
            valid_mask = df[required_fields].notna().all(axis=1)
            invalid_count = (~valid_mask).sum()
            
            if invalid_count > 0:
                print(f"Warning: Dropping {invalid_count} rows with missing critical data from {filepath}")
                df = df[valid_mask]
            
            return df
            
        except Exception as e:
            print(f"Error processing {filepath}: {str(e)}")
            self.format_stats['errors'] += 1
            return None
    
    def process_trades_file(self, filepath, date_str):
        """Process newer trades CSV files (after Aug 2024)"""
        try:
            df = pd.read_csv(filepath)
            
            # These files have a different structure
            # Map to our standard format
            df['date'] = date_str
            
            # Handle timestamp creation for trades files
            if 'Date' in df.columns and 'Time' in df.columns:
                try:
                    df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], errors='coerce')
                    
                    # For failed timestamps, use the date_str
                    failed_timestamps = df['timestamp'].isna().sum()
                    if failed_timestamps > 0:
                        print(f"Warning: {failed_timestamps} timestamps failed in trades file {filepath}")
                        df.loc[df['timestamp'].isna(), 'timestamp'] = pd.to_datetime(date_str)
                except:
                    df['timestamp'] = pd.to_datetime(date_str)
            else:
                df['timestamp'] = pd.to_datetime(date_str)
                
            df['symbol'] = df['Symbol']
            df['strategy'] = df['Name']
            df['price'] = df.get('Closing', np.nan)
            df['premium'] = df['Premium']
            df['predicted'] = df.get('Predicted', np.nan)
            df['closed'] = df.get('Closing', np.nan)
            df['risk'] = df['Risk']
            df['trade_description'] = df['Trade']
            
            # Trades files don't have profit - mark for later calculation
            df['profit'] = np.nan
            df['profit_source'] = 'needs_calculation'
            
            df['source_file'] = os.path.basename(filepath)
            df['format_year'] = int(date_str[:4])
            
            self.format_stats['trades_format'] += 1
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
        
        for i, dir_name in enumerate(dirs):
            if i % 50 == 0:
                print(f"Processing directory {i+1}/{total_dirs}...")
                
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
            
            # Also check for trades files (newer format)
            trades_files = glob.glob(os.path.join(dir_path, 'trades*.csv'))
            if trades_files and not profit_files:  # Only if no profit file
                df = self.process_trades_file(trades_files[0], date_str)
                if df is not None and len(df) > 0:
                    self.all_data.append(df)
        
        print(f"\nProcessing complete!")
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
        
        # Save stats
        stats = {
            'total_trades': len(df),
            'date_range': f"{df['timestamp'].min()} to {df['timestamp'].max()}",
            'overall_win_rate': float(df['win'].mean()),
            'total_profit': float(df['profit'].sum()),
            'format_stats': self.format_stats,
            'symbols_processed': list(df['symbol'].unique()),
            'strategies_found': list(df['strategy'].unique())
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
