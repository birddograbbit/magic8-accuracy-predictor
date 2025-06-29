#!/usr/bin/env python3
"""
Magic8 Data Processor - Fixed Version
This script correctly processes all Magic8 trading data based on the discoveries
from the data analysis, handling all file formats and strategy mislabeling issues.
"""

import os
import csv
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Tuple, Optional
import re
from collections import defaultdict
import pytz
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Magic8DataProcessor:
    def __init__(self, source_path: str, output_path: str):
        self.source_path = Path(source_path)
        self.output_path = Path(output_path)
        
        # Ensure output directory exists
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Trading hours in EST/EDT
        self.market_open = (9, 35)  # 9:35 AM
        self.market_close = (16, 0)  # 4:00 PM
        
        # All expected symbols
        self.expected_symbols = ['SPX', 'SPY', 'RUT', 'QQQ', 'XSP', 'NDX', 'AAPL', 'TSLA']
        
        # All strategies (correct names)
        self.strategies = ['Butterfly', 'Iron Condor', 'Vertical', 'Sonar']
        
        # Data quality tracking
        self.quality_issues = defaultdict(list)
        
        # Processed data storage
        self.all_trades = []
        
    def process_all_folders(self):
        """Process all date folders in the source directory."""
        folders = sorted([f for f in self.source_path.iterdir() if f.is_dir()])
        
        logger.info(f"Found {len(folders)} folders to process")
        
        for i, folder in enumerate(folders):
            if i % 50 == 0:
                logger.info(f"Processing folder {i+1}/{len(folders)}: {folder.name}")
            
            try:
                self.process_folder(folder)
            except Exception as e:
                logger.error(f"Error processing {folder.name}: {e}")
                self.quality_issues['folder_errors'].append({
                    'folder': folder.name,
                    'error': str(e)
                })
    
    def process_folder(self, folder: Path):
        """Process all files in a single date folder."""
        # Extract date from folder name
        folder_date = self.extract_date_from_folder(folder.name)
        if not folder_date:
            return
        
        # Get all CSV files in the folder
        files = {
            'profit': None,
            'delta': None,
            'trades': None
        }
        
        for file_path in folder.glob('*.csv'):
            if 'profit' in file_path.name:
                files['profit'] = file_path
            elif 'delta' in file_path.name:
                files['delta'] = file_path
            elif 'trades' in file_path.name:
                files['trades'] = file_path
        
        # Process profit file (always present)
        if files['profit']:
            self.process_profit_file(files['profit'], folder_date)
        
        # Process trades file if present (Nov 2024 onwards)
        if files['trades']:
            self.process_trades_file(files['trades'], folder_date)
    
    def extract_date_from_folder(self, folder_name: str) -> Optional[datetime]:
        """Extract date from folder name (YYYY-MM-DD-XXXXX format)."""
        match = re.match(r'(\d{4}-\d{2}-\d{2})', folder_name)
        if match:
            return datetime.strptime(match.group(1), '%Y-%m-%d')
        return None
    
    def process_profit_file(self, file_path: Path, folder_date: datetime):
        """Process a profit file, handling all format variations."""
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read first line to determine format
            first_line = f.readline().strip()
            f.seek(0)
            
            # Determine format based on header
            if first_line.startswith('Day,Hour'):
                self.process_profit_2023_format(f, folder_date)
            elif first_line.startswith('Date,Hour'):
                self.process_profit_2025_format(f, folder_date)
            else:
                # 2024 format or unknown
                self.process_profit_2024_format(f, folder_date)
    
    def process_profit_2023_format(self, file_obj, folder_date: datetime):
        """Process 2023 format profit files."""
        reader = csv.DictReader(file_obj)
        
        for row in reader:
            # Skip summary rows (they have different structure)
            if not row.get('Symbol') or row['Symbol'] in ['Symbol', 'Total', 'Expired', 'Failed']:
                continue
            
            # Skip strategy summary rows
            if any(strategy in row.get('Symbol', '') for strategy in self.strategies):
                continue
            
            trade = {
                'date': folder_date.strftime('%Y-%m-%d'),
                'time': row['Hour'],
                'symbol': row['Symbol'],
                'price': self.safe_float(row.get('Price')),
                'strategy': row['Name'],  # IMPORTANT: Use Name column, not Trade!
                'premium': self.safe_float(row.get('Premium')),
                'predicted': self.safe_float(row.get('Predicted')),
                'closed': self.safe_float(row.get('Closed')),
                'expired': row.get('Expired', '').lower() == 'true',
                'trade_description': row.get('Trade'),
                'risk': self.safe_float(row.get('Risk')),
                'reward': self.safe_float(row.get('Reward')),
                'ratio': self.safe_float(row.get('Ratio')),
                'profit': self.safe_float(row.get('Profit')),
                'source_file': 'profit',
                'format_year': 2023
            }
            
            # Validate and add trade
            self.validate_and_add_trade(trade, file_obj.name)
    
    def process_profit_2024_format(self, file_obj, folder_date: datetime):
        """Process 2024 format profit files."""
        reader = csv.DictReader(file_obj)
        
        for row in reader:
            # Skip summary rows
            if not row.get('Symbol') or row['Symbol'] in ['Symbol', 'Total', 'Expired', 'Failed']:
                continue
            
            # Skip strategy summary rows
            if any(strategy in row.get('Symbol', '') for strategy in self.strategies):
                continue
            
            trade = {
                'date': folder_date.strftime('%Y-%m-%d'),
                'time': row['Hour'],
                'symbol': row['Symbol'],
                'price': self.safe_float(row.get('Price')),
                'strategy': row['Name'],  # IMPORTANT: Use Name column!
                'premium': self.safe_float(row.get('Premium')),
                'predicted': self.safe_float(row.get('Predicted')),
                'low': self.safe_float(row.get('Low')),
                'high': self.safe_float(row.get('High')),
                'closed': self.safe_float(row.get('Closed')),
                'risk': self.safe_float(row.get('Risk')),
                'reward': self.safe_float(row.get('Reward')),
                'stop': self.safe_float(row.get('Stop')),
                'raw': self.safe_float(row.get('Raw')),
                'managed': self.safe_float(row.get('Managed')),
                'trade_description': row.get('Trade'),
                'source_file': 'profit',
                'format_year': 2024
            }
            
            # Validate and add trade
            self.validate_and_add_trade(trade, file_obj.name)
    
    def process_profit_2025_format(self, file_obj, folder_date: datetime):
        """Process 2025 format profit files."""
        reader = csv.DictReader(file_obj)
        
        for row in reader:
            # Skip summary rows
            if not row.get('Symbol') or row['Symbol'] in ['Symbol', 'Total', 'Expired', 'Failed']:
                continue
            
            # Skip strategy summary rows
            if any(strategy in row.get('Symbol', '') for strategy in self.strategies):
                continue
            
            trade = {
                'date': folder_date.strftime('%Y-%m-%d'),
                'time': row['Hour'],
                'symbol': row['Symbol'],
                'price': self.safe_float(row.get('Price')),
                'strategy': row['Name'],  # IMPORTANT: Use Name column!
                'premium': self.safe_float(row.get('Premium')),
                'predicted': self.safe_float(row.get('Predicted')),
                'low': self.safe_float(row.get('Low')),
                'high': self.safe_float(row.get('High')),
                'closing': self.safe_float(row.get('Closing')),
                'risk': self.safe_float(row.get('Risk')),
                'expected_premium': self.safe_float(row.get('ExpectedPremium')),
                'actual_premium': self.safe_float(row.get('ActualPremium')),
                'profit': self.safe_float(row.get('Profit')),
                'total_profit': self.safe_float(row.get('TotalProfit')),
                'trade_description': row.get('Trade'),
                'source_file': 'profit',
                'format_year': 2025
            }
            
            # Validate and add trade
            self.validate_and_add_trade(trade, file_obj.name)
    
    def process_trades_file(self, file_path: Path, folder_date: datetime):
        """Process a trades file (Nov 2024 onwards format)."""
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Parse UTC timestamp and convert to EST/EDT
                time_str = row.get('Time', '')
                dt = self.parse_trades_timestamp(row.get('Date'), time_str)
                
                if dt:
                    est_time = dt.strftime('%H:%M')
                else:
                    est_time = time_str
                
                trade = {
                    'date': folder_date.strftime('%Y-%m-%d'),
                    'time': est_time,
                    'symbol': row.get('Symbol'),
                    'strategy': row.get('Name'),  # IMPORTANT: Use Name column!
                    'premium': self.safe_float(row.get('Premium')),
                    'risk': self.safe_float(row.get('Risk')),
                    'expected_move': self.safe_float(row.get('ExpectedMove')),
                    'predicted': self.safe_float(row.get('Predicted')),
                    'closing': self.safe_float(row.get('Closing')),
                    'trade_description': row.get('Trade'),
                    'source_file': 'trades',
                    'format_year': 2024
                }
                
                # Only add if we don't already have this trade from profit file
                if not self.is_duplicate_trade(trade):
                    self.validate_and_add_trade(trade, file_path.name)
    
    def parse_trades_timestamp(self, date_str: str, time_str: str) -> Optional[datetime]:
        """Parse trades file timestamp (UTC) and convert to EST/EDT."""
        try:
            # Parse UTC timestamp
            dt_str = f"{date_str} {time_str}"
            dt_utc = datetime.strptime(dt_str, '%m-%d-%Y %H:%M')
            
            # Convert to EST/EDT
            utc_tz = pytz.UTC
            eastern_tz = pytz.timezone('US/Eastern')
            dt_utc = utc_tz.localize(dt_utc)
            dt_eastern = dt_utc.astimezone(eastern_tz)
            
            return dt_eastern
        except Exception as e:
            logger.warning(f"Failed to parse timestamp: {date_str} {time_str} - {e}")
            return None
    
    def is_duplicate_trade(self, trade: Dict) -> bool:
        """Check if this trade already exists (from profit file)."""
        for existing in self.all_trades:
            if (existing['date'] == trade['date'] and 
                existing['time'] == trade['time'] and
                existing['symbol'] == trade['symbol'] and
                existing['strategy'] == trade['strategy']):
                return True
        return False
    
    def validate_and_add_trade(self, trade: Dict, filename: str):
        """Validate trade data and add to collection."""
        # Check for data quality issues
        if trade['premium'] is not None and trade['premium'] < 0:
            self.quality_issues['negative_premiums'].append({
                'file': filename,
                'trade': f"{trade['date']} {trade['time']} {trade['symbol']} {trade['strategy']}",
                'premium': trade['premium']
            })
        
        if trade['premium'] == 0:
            self.quality_issues['zero_premiums'].append({
                'file': filename,
                'trade': f"{trade['date']} {trade['time']} {trade['symbol']} {trade['strategy']}"
            })
        
        # Validate strategy
        if trade['strategy'] not in self.strategies:
            self.quality_issues['unknown_strategies'].append({
                'file': filename,
                'strategy': trade['strategy'],
                'trade': trade['trade_description']
            })
        
        # Validate symbol
        if trade['symbol'] not in self.expected_symbols:
            self.quality_issues['unknown_symbols'].append({
                'file': filename,
                'symbol': trade['symbol']
            })
        
        # Add normalized timestamp
        trade['timestamp'] = f"{trade['date']} {trade['time']}:00"
        
        # Calculate win/loss if we have profit data
        if 'profit' in trade and trade['profit'] is not None:
            trade['win'] = 1 if trade['profit'] > 0 else 0
        
        self.all_trades.append(trade)
    
    def safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float."""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def save_processed_data(self):
        """Save all processed data to files."""
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(self.all_trades)
        
        # Sort by date and time
        df['datetime'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(['datetime', 'symbol', 'strategy'])
        
        # Save complete dataset
        output_file = self.output_path / 'magic8_trades_complete.csv'
        df.to_csv(output_file, index=False)
        logger.info(f"Saved {len(df)} trades to {output_file}")
        
        # Save strategy distribution analysis
        self.save_strategy_analysis(df)
        
        # Save data quality report
        self.save_quality_report()
        
        # Save symbol coverage analysis
        self.save_symbol_analysis(df)
    
    def save_strategy_analysis(self, df: pd.DataFrame):
        """Save strategy distribution analysis."""
        strategy_stats = {
            'total_trades': len(df),
            'by_strategy': df['strategy'].value_counts().to_dict(),
            'by_strategy_pct': (df['strategy'].value_counts() / len(df) * 100).round(2).to_dict(),
            'by_year_strategy': {}
        }
        
        # Analysis by year
        df['year'] = pd.to_datetime(df['date']).dt.year
        for year in sorted(df['year'].unique()):
            year_df = df[df['year'] == year]
            strategy_stats['by_year_strategy'][str(year)] = {
                'total': len(year_df),
                'distribution': year_df['strategy'].value_counts().to_dict(),
                'distribution_pct': (year_df['strategy'].value_counts() / len(year_df) * 100).round(2).to_dict()
            }
        
        output_file = self.output_path / 'strategy_analysis.json'
        with open(output_file, 'w') as f:
            json.dump(strategy_stats, f, indent=2)
        
        logger.info(f"Strategy Analysis:")
        for strategy, count in strategy_stats['by_strategy'].items():
            pct = strategy_stats['by_strategy_pct'][strategy]
            logger.info(f"  {strategy}: {count:,} trades ({pct}%)")
    
    def save_quality_report(self):
        """Save data quality issues report."""
        report = {
            'summary': {
                'total_trades': len(self.all_trades),
                'negative_premiums': len(self.quality_issues['negative_premiums']),
                'zero_premiums': len(self.quality_issues['zero_premiums']),
                'unknown_strategies': len(self.quality_issues['unknown_strategies']),
                'unknown_symbols': len(self.quality_issues['unknown_symbols']),
                'folder_errors': len(self.quality_issues['folder_errors'])
            },
            'details': dict(self.quality_issues)
        }
        
        output_file = self.output_path / 'data_quality_report.json'
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Data Quality Summary:")
        for issue, count in report['summary'].items():
            if count > 0:
                logger.warning(f"  {issue}: {count}")
    
    def save_symbol_analysis(self, df: pd.DataFrame):
        """Save symbol coverage analysis."""
        symbol_stats = {
            'expected_symbols': self.expected_symbols,
            'found_symbols': sorted(df['symbol'].unique().tolist()),
            'by_symbol': df['symbol'].value_counts().to_dict(),
            'by_symbol_strategy': {}
        }
        
        # Strategy distribution by symbol
        for symbol in df['symbol'].unique():
            symbol_df = df[df['symbol'] == symbol]
            symbol_stats['by_symbol_strategy'][symbol] = {
                'total': len(symbol_df),
                'strategies': symbol_df['strategy'].value_counts().to_dict()
            }
        
        output_file = self.output_path / 'symbol_analysis.json'
        with open(output_file, 'w') as f:
            json.dump(symbol_stats, f, indent=2)
        
        logger.info(f"Symbol Coverage:")
        for symbol in self.expected_symbols:
            if symbol in symbol_stats['by_symbol']:
                count = symbol_stats['by_symbol'][symbol]
                logger.info(f"  {symbol}: {count:,} trades")
            else:
                logger.warning(f"  {symbol}: NO DATA FOUND")


def main():
    """Main execution function."""
    # Set paths
    source_path = "/Users/jt/magic8/magic8-accuracy-predictor/data/source"
    output_path = "/Users/jt/magic8/magic8-accuracy-predictor/data/processed_fixed"
    
    # Create processor
    processor = Magic8DataProcessor(source_path, output_path)
    
    # Process all data
    logger.info("Starting Magic8 data processing (fixed version)...")
    processor.process_all_folders()
    
    # Save results
    logger.info("Saving processed data...")
    processor.save_processed_data()
    
    logger.info("Processing complete!")


if __name__ == "__main__":
    main()
