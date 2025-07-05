#!/usr/bin/env python3
"""
Magic8 Data Processor - Optimized Version 3
Fixes CSV output issues and properly tracks delta sheet integration
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
import time
import gc

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Magic8DataProcessorOptimized:
    def __init__(self, source_path: str, output_path: str, batch_size: int = 1000):
        self.source_path = Path(source_path)
        self.output_path = Path(output_path)
        self.batch_size = batch_size
        
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
        # Pre-create lists for easier diagnostics
        self.quality_issues = defaultdict(list, {
            "missing_profit": [],
            "duplicates": [],
            "bad_timestamps": []
        })
        
        # Current batch of trades
        self.current_batch = []
        self.total_trades_processed = 0

        # Track unique trades to detect duplicates
        self.seen_trade_keys = set()
        
        # Output file handle (keep open for appending)
        self.output_file = self.output_path / 'magic8_trades_complete.csv'
        self.first_write = True
        
        # Pattern to remove non-printable characters
        self.non_printable_pattern = re.compile(r'[^\x20-\x7E]')
        
        # Track timestamp cleaning stats
        self.timestamp_stats = {
            'total_timestamps': 0,
            'cleaned_timestamps': 0,
            'failed_timestamps': 0
        }
        
        # Strategy distribution tracking (incremental)
        self.strategy_counts = defaultdict(int)
        self.symbol_counts = defaultdict(int)
        
        # Performance tracking
        self.start_time = time.time()
        self.folders_processed = 0
        
        # Define expanded column order including all sheet fields
        self.column_order = [
            # Identity
            'date', 'time', 'timestamp', 'symbol', 'strategy',

            # Profit sheet
            'price', 'premium', 'predicted', 'closed', 'expired',
            'risk', 'reward', 'ratio', 'profit', 'win',

            # Trades sheet
            'source', 'expected_move', 'low', 'high',
            'target1', 'target2', 'predicted_trades', 'closing',
            'strike1', 'direction1', 'type1', 'bid1', 'ask1', 'mid1',
            'strike2', 'direction2', 'type2', 'bid2', 'ask2', 'mid2',
            'strike3', 'direction3', 'type3', 'bid3', 'ask3', 'mid3',
            'strike4', 'direction4', 'type4', 'bid4', 'ask4', 'mid4',

            # Delta sheet
            'call_delta', 'put_delta', 'predicted_delta',
            'short_term', 'long_term', 'closing_delta',

            # Metadata
            'trade_description', 'source_file', 'format_year'
        ]
        
    def clean_string(self, value: str) -> str:
        """Remove non-printable characters from string."""
        if not value:
            return value
        return self.non_printable_pattern.sub('', value)
    
    def write_batch(self):
        """Write current batch to CSV file with consistent columns."""
        if not self.current_batch:
            return
            
        df = pd.DataFrame(self.current_batch)
        
        # Ensure all expected columns exist
        for col in self.column_order:
            if col not in df.columns:
                df[col] = None
        
        # Sort by date and time (but don't add datetime column)
        if 'timestamp' in df.columns:
            df['temp_datetime'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.sort_values(['temp_datetime', 'symbol', 'strategy'])
            df = df.drop('temp_datetime', axis=1)
        
        # Select only the columns we want in the correct order
        df = df[self.column_order]
        
        # Write to CSV with proper quoting to handle commas in descriptions
        if self.first_write:
            df.to_csv(self.output_file, index=False, mode='w', quoting=csv.QUOTE_NONNUMERIC)
            self.first_write = False
            logger.info(f"Created output file: {self.output_file}")
        else:
            df.to_csv(self.output_file, index=False, mode='a', header=False, quoting=csv.QUOTE_NONNUMERIC)
        
        self.total_trades_processed += len(self.current_batch)
        logger.info(f"Wrote batch of {len(self.current_batch)} trades. Total: {self.total_trades_processed:,}")
        
        # Clear batch and force garbage collection
        self.current_batch = []
        gc.collect()
    
    def process_all_folders(self):
        """Process all date folders in the source directory."""
        folders = sorted([f for f in self.source_path.iterdir() if f.is_dir()])
        
        logger.info(f"Found {len(folders)} folders to process")
        logger.info(f"Using batch size: {self.batch_size}")
        
        for i, folder in enumerate(folders):
            folder_start = time.time()
            
            if i % 10 == 0:
                # Report progress and performance
                elapsed = time.time() - self.start_time
                folders_per_minute = (i + 1) / (elapsed / 60) if elapsed > 0 else 0
                eta_minutes = (len(folders) - i) / folders_per_minute if folders_per_minute > 0 else 0
                
                logger.info(f"Processing folder {i+1}/{len(folders)}: {folder.name}")
                logger.info(f"  Speed: {folders_per_minute:.1f} folders/min, ETA: {eta_minutes:.1f} min")
                logger.info(f"  Memory batch: {len(self.current_batch)} trades")
            
            try:
                self.process_folder(folder)
                
                # Write batch if it's getting large
                if len(self.current_batch) >= self.batch_size:
                    self.write_batch()
                    
            except Exception as e:
                logger.error(f"Error processing {folder.name}: {e}")
                self.quality_issues['folder_errors'].append({
                    'folder': folder.name,
                    'error': str(e)
                })
            
            self.folders_processed += 1
            
            # Log slow folders
            folder_time = time.time() - folder_start
            if folder_time > 5:  # More than 5 seconds
                logger.warning(f"  Slow folder: {folder.name} took {folder_time:.1f} seconds")
        
        # Write any remaining trades
        if self.current_batch:
            self.write_batch()
    
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
        
        # Merge data from profit, trades and delta files
        trades_data: Dict[str, Dict] = {}

        # 1. Profit file is base
        if files['profit']:
            profit_trades = self.process_profit_file(files['profit'], folder_date)
            for trade in profit_trades:
                key = self._create_trade_key(trade)
                trades_data[key] = trade

        # 2. Enhance with trades file
        if files['trades']:
            trades_info = self.process_trades_file_enhanced(files['trades'], folder_date)
            for trade in trades_info:
                key = self._create_trade_key(trade)
                if key in trades_data:
                    trades_data[key].update(trade)
                else:
                    trades_data[key] = trade

        # 3. Add delta sheet data with tracking
        if files['delta']:
            delta_data = self.process_delta_file(files['delta'], folder_date)
            delta_matches = 0

            for key, trade in trades_data.items():
                time_key = f"{trade.get('date')} {trade.get('time')}"
                if time_key in delta_data:
                    # Update trade with delta data
                    trade.update(delta_data[time_key])

                    # Mark that delta data was included
                    if trade.get('source_file'):
                        trade['source_file'] += ',delta'
                    else:
                        trade['source_file'] = 'delta'

                    delta_matches += 1

            logger.info(f"Matched {delta_matches}/{len(delta_data)} delta records")

        # Add merged trades to batch
        for trade in trades_data.values():
            self.validate_and_add_trade(trade, str(folder))

    def _create_trade_key(self, trade: Dict) -> str:
        """Create a unique key for matching trades across sheets."""
        return f"{trade.get('date')}_{trade.get('time')}_{trade.get('symbol')}_{trade.get('strategy')}"
    
    def extract_date_from_folder(self, folder_name: str) -> Optional[datetime]:
        """Extract date from folder name (YYYY-MM-DD-XXXXX format)."""
        match = re.match(r'(\d{4}-\d{2}-\d{2})', folder_name)
        if match:
            return datetime.strptime(match.group(1), '%Y-%m-%d')
        return None
    
    def parse_timestamp_flexible(self, date_str: str, time_str: str = None) -> Optional[str]:
        """Parse timestamp with multiple format support and cleaning."""
        self.timestamp_stats['total_timestamps'] += 1
        
        try:
            # Clean date string
            if date_str:
                original_date = date_str
                date_str = self.clean_string(date_str)
                if original_date != date_str:
                    self.timestamp_stats['cleaned_timestamps'] += 1
            
            # Clean time string
            if time_str:
                original_time = time_str
                time_str = self.clean_string(time_str)
                if original_time != time_str:
                    self.timestamp_stats['cleaned_timestamps'] += 1
            
            # Try different date formats
            date_formats = [
                '%m-%d-%Y',     # MM-DD-YYYY
                '%Y-%m-%d',     # YYYY-MM-DD
                '%m/%d/%Y',     # MM/DD/YYYY
                '%Y/%m/%d',     # YYYY/MM/DD
                '%d-%m-%Y',     # DD-MM-YYYY
                '%d/%m/%Y',     # DD/MM/YYYY
            ]
            
            parsed_date = None
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            
            if not parsed_date:
                self.timestamp_stats['failed_timestamps'] += 1
                return None
            
            # If we have a time string, parse it
            if time_str:
                # Handle both HH:MM and H:MM formats
                time_parts = time_str.split(':')
                if len(time_parts) >= 2:
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    return f"{parsed_date.strftime('%Y-%m-%d')} {hour:02d}:{minute:02d}:00"
            
            return parsed_date.strftime('%Y-%m-%d')
            
        except Exception as e:
            self.timestamp_stats['failed_timestamps'] += 1
            return None
    
    def process_profit_file(self, file_path: Path, folder_date: datetime) -> List[Dict]:
        """Process a profit file, handling all format variations."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Read first line to determine format
            first_line = f.readline().strip()
            f.seek(0)
            
            # Determine format based on header
            if first_line.startswith('Day,Hour'):
                trades = self.process_profit_2023_format(f, folder_date, file_path)
            elif first_line.startswith('Date,Hour'):
                trades = self.process_profit_2025_format(f, folder_date, file_path)
            else:
                # 2024 format or unknown
                trades = self.process_profit_2024_format(f, folder_date, file_path)

        return trades
    
    def process_profit_2023_format(self, file_obj, folder_date: datetime, file_path: Path) -> List[Dict]:
        """Process 2023 format profit files."""
        reader = csv.DictReader(file_obj)
        trades = []

        for row_num, row in enumerate(reader, 2):
            try:
                # Skip summary rows
                if not row.get('Symbol') or row['Symbol'] in ['Symbol', 'Total', 'Expired', 'Failed']:
                    continue
                
                # Skip strategy summary rows
                if any(strategy in row.get('Symbol', '') for strategy in self.strategies):
                    continue
                
                # Clean and parse timestamp
                date_str = self.clean_string(row.get('Day', ''))
                time_str = self.clean_string(row.get('Hour', ''))
                
                # Use folder date if date parsing fails
                if date_str:
                    timestamp = self.parse_timestamp_flexible(date_str, time_str)
                else:
                    timestamp = f"{folder_date.strftime('%Y-%m-%d')} {time_str}:00" if time_str else None
                
                if not timestamp:
                    timestamp = f"{folder_date.strftime('%Y-%m-%d')} 09:35:00"  # Default to market open
                
                trade = {
                    'date': timestamp.split()[0] if timestamp else folder_date.strftime('%Y-%m-%d'),
                    'time': timestamp.split()[1][:5] if timestamp and len(timestamp.split()) > 1 else '09:35',
                    'symbol': self.clean_string(row.get('Symbol', '')),
                    'price': self.safe_float(row.get('Price')),
                    'strategy': self.clean_string(row.get('Name', '')),  # IMPORTANT: Use Name column
                    'premium': self.safe_float(row.get('Premium')),
                    'predicted': self.safe_float(row.get('Predicted')),
                    'closed': self.safe_float(row.get('Closed')),
                    'expired': row.get('Expired', '').lower() == 'true',
                    'trade_description': self.clean_string(row.get('Trade', '')),  # Clean to remove problematic chars
                    'risk': self.safe_float(row.get('Risk')),
                    'reward': self.safe_float(row.get('Reward')),
                    'ratio': self.safe_float(row.get('Ratio')),
                    'profit': self.safe_float(row.get('Profit') or row.get('Raw') or row.get('Managed')),
                    'source_file': 'profit',
                    'format_year': folder_date.year,
                    'timestamp': timestamp
                }

                if trade['profit'] is None:
                    self.quality_issues['missing_profit'].append({
                        'file': str(file_path),
                        'row': row_num,
                        'available_columns': list(row.keys())
                    })
                
                trades.append(trade)
                
            except Exception as e:
                self.quality_issues['row_errors'].append({
                    'file': str(file_path),
                    'row': row_num,
                    'error': str(e)
                })

        return trades

    def process_profit_2024_format(self, file_obj, folder_date: datetime, file_path: Path) -> List[Dict]:
        """Process 2024 format profit files."""
        reader = csv.DictReader(file_obj)
        trades = []

        for row_num, row in enumerate(reader, 2):
            try:
                # Skip summary rows
                if not row.get('Symbol') or row['Symbol'] in ['Symbol', 'Total', 'Expired', 'Failed']:
                    continue
                
                # Skip strategy summary rows
                if any(strategy in row.get('Symbol', '') for strategy in self.strategies):
                    continue
                
                # Clean and get time
                time_str = self.clean_string(row.get('Hour', ''))
                
                trade = {
                    'date': folder_date.strftime('%Y-%m-%d'),
                    'time': time_str if time_str else '09:35',
                    'symbol': self.clean_string(row.get('Symbol', '')),
                    'price': self.safe_float(row.get('Price')),
                    'strategy': self.clean_string(row.get('Name', '')),  # IMPORTANT: Use Name column
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
                    'profit': self.safe_float(row.get('Profit') or row.get('Raw') or row.get('Managed')),
                    'trade_description': self.clean_string(row.get('Trade', '')),
                    'source_file': 'profit',
                    'format_year': folder_date.year,
                    'timestamp': f"{folder_date.strftime('%Y-%m-%d')} {time_str}:00" if time_str else None
                }

                if trade['profit'] is None:
                    self.quality_issues['missing_profit'].append({
                        'file': str(file_path),
                        'row': row_num,
                        'available_columns': list(row.keys())
                    })
                
                trades.append(trade)
                
            except Exception as e:
                self.quality_issues['row_errors'].append({
                    'file': str(file_path),
                    'row': row_num,
                    'error': str(e)
                })

        return trades
    
    def process_profit_2025_format(self, file_obj, folder_date: datetime, file_path: Path) -> List[Dict]:
        """Process 2025 format profit files."""
        reader = csv.DictReader(file_obj)
        trades = []

        for row_num, row in enumerate(reader, 2):
            try:
                # Skip summary rows
                if not row.get('Symbol') or row['Symbol'] in ['Symbol', 'Total', 'Expired', 'Failed']:
                    continue
                
                # Skip strategy summary rows
                if any(strategy in row.get('Symbol', '') for strategy in self.strategies):
                    continue
                
                # Clean and get time
                time_str = self.clean_string(row.get('Hour', ''))
                
                trade = {
                    'date': folder_date.strftime('%Y-%m-%d'),
                    'time': time_str if time_str else '09:35',
                    'symbol': self.clean_string(row.get('Symbol', '')),
                    'price': self.safe_float(row.get('Price')),
                    'strategy': self.clean_string(row.get('Name', '')),  # IMPORTANT: Use Name column
                    'premium': self.safe_float(row.get('Premium')),
                    'predicted': self.safe_float(row.get('Predicted')),
                    'low': self.safe_float(row.get('Low')),
                    'high': self.safe_float(row.get('High')),
                    'closing': self.safe_float(row.get('Closing')),
                    'risk': self.safe_float(row.get('Risk')),
                    'expected_premium': self.safe_float(row.get('ExpectedPremium')),
                    'actual_premium': self.safe_float(row.get('ActualPremium')),
                    'profit': self.safe_float(row.get('Profit') or row.get('Raw') or row.get('Managed')),
                    'total_profit': self.safe_float(row.get('TotalProfit')),
                    'trade_description': self.clean_string(row.get('Trade', '')),
                    'source_file': 'profit',
                    'format_year': folder_date.year,
                    'timestamp': f"{folder_date.strftime('%Y-%m-%d')} {time_str}:00" if time_str else None
                }

                if trade['profit'] is None:
                    self.quality_issues['missing_profit'].append({
                        'file': str(file_path),
                        'row': row_num,
                        'available_columns': list(row.keys())
                    })
                
                trades.append(trade)
                
            except Exception as e:
                self.quality_issues['row_errors'].append({
                    'file': str(file_path),
                    'row': row_num,
                    'error': str(e)
                })

        return trades
    
    def process_trades_file_enhanced(self, file_path: Path, folder_date: datetime) -> List[Dict]:
        """Process trades file with full strike breakdown."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            trades = []

            for row_num, row in enumerate(reader, 2):
                try:
                    # Clean and parse timestamp
                    date_str = self.clean_string(row.get('Date', ''))
                    time_str = self.clean_string(row.get('Time', ''))
                    
                    # Parse UTC timestamp and convert to EST/EDT
                    dt = self.parse_trades_timestamp(date_str, time_str)
                    
                    if dt:
                        est_time = dt.strftime('%H:%M')
                        trade_date = dt.strftime('%Y-%m-%d')
                    else:
                        est_time = time_str if time_str else '09:35'
                        trade_date = folder_date.strftime('%Y-%m-%d')
                    
                    trade = {
                        'date': trade_date,
                        'time': est_time,
                        'symbol': self.clean_string(row.get('Symbol', '')),
                        'strategy': self.clean_string(row.get('Name', '')),
                        'premium': self.safe_float(row.get('Premium')),
                        'profit': self.safe_float(row.get('Profit') or row.get('Raw') or row.get('Managed')),
                        'risk': self.safe_float(row.get('Risk')),
                        'expected_move': self.safe_float(row.get('ExpectedMove')),
                        'low': self.safe_float(row.get('Low')),
                        'high': self.safe_float(row.get('High')),
                        'target1': self.safe_float(row.get('Target1')),
                        'target2': self.safe_float(row.get('Target2')),
                        'predicted_trades': self.safe_float(row.get('Predicted')),
                        'closing': self.safe_float(row.get('Closing')),

                        'strike1': self.safe_float(row.get('Strike1')),
                        'direction1': self.clean_string(row.get('Direction1', '')),
                        'type1': self.clean_string(row.get('Type1', '')),
                        'bid1': self.safe_float(row.get('Bid1')),
                        'ask1': self.safe_float(row.get('Ask1')),
                        'mid1': self.safe_float(row.get('Mid1')),

                        'strike2': self.safe_float(row.get('Strike2')),
                        'direction2': self.clean_string(row.get('Direction2', '')),
                        'type2': self.clean_string(row.get('Type2', '')),
                        'bid2': self.safe_float(row.get('Bid2')),
                        'ask2': self.safe_float(row.get('Ask2')),
                        'mid2': self.safe_float(row.get('Mid2')),

                        'strike3': self.safe_float(row.get('Strike3')),
                        'direction3': self.clean_string(row.get('Direction3', '')),
                        'type3': self.clean_string(row.get('Type3', '')),
                        'bid3': self.safe_float(row.get('Bid3')),
                        'ask3': self.safe_float(row.get('Ask3')),
                        'mid3': self.safe_float(row.get('Mid3')),

                        'strike4': self.safe_float(row.get('Strike4')),
                        'direction4': self.clean_string(row.get('Direction4', '')),
                        'type4': self.clean_string(row.get('Type4', '')),
                        'bid4': self.safe_float(row.get('Bid4')),
                        'ask4': self.safe_float(row.get('Ask4')),
                        'mid4': self.safe_float(row.get('Mid4')),

                        'trade_description': self.clean_string(row.get('Trade', '')),
                        'source_file': 'trades',
                        'format_year': folder_date.year,
                        'timestamp': f"{trade_date} {est_time}:00"
                    }

                    if trade['profit'] is None:
                        self.quality_issues['missing_profit'].append({
                            'file': str(file_path),
                            'row': row_num,
                            'available_columns': list(row.keys())
                        })
                    
                    trades.append(trade)
                        
                except Exception as e:
                    self.quality_issues['row_errors'].append({
                        'file': str(file_path),
                        'row': row_num,
                        'error': str(e)
                    })

        return trades
    
    def parse_trades_timestamp(self, date_str: str, time_str: str) -> Optional[datetime]:
        """Parse trades file timestamp (UTC) and convert to EST/EDT."""
        try:
            # Try to parse with flexible format
            timestamp_str = self.parse_timestamp_flexible(date_str, time_str)
            if not timestamp_str:
                return None
            
            # Parse the cleaned timestamp
            dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            # Convert to EST/EDT
            utc_tz = pytz.UTC
            eastern_tz = pytz.timezone('US/Eastern')
            dt_utc = utc_tz.localize(dt)
            dt_eastern = dt_utc.astimezone(eastern_tz)
            
            return dt_eastern

        except Exception as e:
            return None

    def process_delta_file(self, file_path: Path, folder_date: datetime) -> Dict[str, Dict]:
        """Process delta sheet for prediction indicators."""
        delta_data = {}

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)

            for row in reader:
                when = self.clean_string(row.get('When', ''))
                if when:
                    time_part = when.split()[-1] if ' ' in when else ''
                    time_key = f"{folder_date.strftime('%Y-%m-%d')} {time_part}"

                    delta_data[time_key] = {
                        'call_delta': self.safe_float(row.get('CallDelta')),
                        'put_delta': self.safe_float(row.get('PutDelta')),
                        'predicted_delta': self.safe_float(row.get('Predicted')),
                        'short_term': self.safe_float(row.get('ShortTerm')),
                        'long_term': self.safe_float(row.get('LongTerm')),
                        'closing_delta': self.safe_float(row.get('Closing'))
                    }

        return delta_data
    
    def validate_and_add_trade(self, trade: Dict, filename: str):
        """Validate trade data and add to current batch."""
        # Update strategy and symbol counts
        if trade.get('strategy'):
            self.strategy_counts[trade['strategy']] += 1
        if trade.get('symbol'):
            self.symbol_counts[trade['symbol']] += 1
        
        # Check for data quality issues
        if trade.get('premium') is not None and trade['premium'] < 0:
            self.quality_issues['negative_premiums'].append({
                'file': filename,
                'trade': f"{trade.get('date', '')} {trade.get('time', '')} {trade.get('symbol', '')} {trade.get('strategy', '')}",
                'premium': trade['premium']
            })
        
        if trade.get('premium') == 0:
            self.quality_issues['zero_premiums'].append({
                'file': filename,
                'trade': f"{trade.get('date', '')} {trade.get('time', '')} {trade.get('symbol', '')} {trade.get('strategy', '')}"
            })
        
        # Validate strategy
        if trade.get('strategy') and trade['strategy'] not in self.strategies:
            self.quality_issues['unknown_strategies'].append({
                'file': filename,
                'strategy': trade['strategy'],
                'trade': trade.get('trade_description', '')
            })
        
        # Validate symbol
        if trade.get('symbol') and trade['symbol'] not in self.expected_symbols:
            self.quality_issues['unknown_symbols'].append({
                'file': filename,
                'symbol': trade['symbol']
            })
        
        # Calculate win/loss if we have profit data
        if 'profit' in trade and trade['profit'] is not None:
            trade['win'] = 1 if trade['profit'] > 0 else 0
        else:
            trade['win'] = None
        
        # Detect duplicate trades using key of date/time/symbol/strategy
        key = self._create_trade_key(trade)
        if key in self.seen_trade_keys:
            self.quality_issues['duplicates'].append({
                'file': filename,
                'key': key
            })
            return
        self.seen_trade_keys.add(key)

        # Ensure all expected fields exist
        for field in self.column_order:
            if field not in trade:
                trade[field] = None

        # Validate timestamp format and format_year
        if trade.get('timestamp'):
            try:
                dt = pd.to_datetime(trade['timestamp'])
                if dt.year != trade.get('format_year'):
                    trade['format_year'] = dt.year
            except Exception:
                self.quality_issues['bad_timestamps'].append({
                    'file': filename,
                    'value': trade.get('timestamp')
                })
                trade['timestamp'] = None

        self.current_batch.append(trade)
    
    def safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float."""
        if value is None or value == '':
            return None
        try:
            # Clean string if it's a string
            if isinstance(value, str):
                value = self.clean_string(value)
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def save_final_reports(self):
        """Save final analysis reports after all processing."""
        # Save strategy distribution
        strategy_stats = {
            'total_trades': self.total_trades_processed,
            'by_strategy': dict(self.strategy_counts),
            'by_strategy_pct': {k: round(v/self.total_trades_processed*100, 2) for k, v in self.strategy_counts.items()} if self.total_trades_processed > 0 else {}
        }
        
        output_file = self.output_path / 'strategy_analysis.json'
        with open(output_file, 'w') as f:
            json.dump(strategy_stats, f, indent=2)
        
        logger.info(f"\nStrategy Analysis:")
        for strategy, count in sorted(self.strategy_counts.items()):
            pct = round(count/self.total_trades_processed*100, 2) if self.total_trades_processed > 0 else 0
            logger.info(f"  {strategy}: {count:,} trades ({pct}%)")
        
        # Save data quality report
        report = {
            'summary': {
                'total_trades': self.total_trades_processed,
                'negative_premiums': len(self.quality_issues['negative_premiums']),
                'zero_premiums': len(self.quality_issues['zero_premiums']),
                'unknown_strategies': len(self.quality_issues['unknown_strategies']),
                'unknown_symbols': len(self.quality_issues['unknown_symbols']),
                'folder_errors': len(self.quality_issues['folder_errors']),
                'row_errors': len(self.quality_issues['row_errors']),
                'duplicates': len(self.quality_issues['duplicates']),
                'bad_timestamps': len(self.quality_issues['bad_timestamps'])
            },
            'details': dict(self.quality_issues) if sum(len(v) for v in self.quality_issues.values()) < 1000 else {}
        }
        
        output_file = self.output_path / 'data_quality_report.json'
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save symbol analysis
        symbol_stats = {
            'expected_symbols': self.expected_symbols,
            'found_symbols': list(self.symbol_counts.keys()),
            'by_symbol': dict(self.symbol_counts)
        }
        
        output_file = self.output_path / 'symbol_analysis.json'
        with open(output_file, 'w') as f:
            json.dump(symbol_stats, f, indent=2)
        
        logger.info(f"\nSymbol Coverage:")
        for symbol in self.expected_symbols:
            if symbol in self.symbol_counts:
                count = self.symbol_counts[symbol]
                logger.info(f"  {symbol}: {count:,} trades")
            else:
                logger.warning(f"  {symbol}: NO DATA FOUND")
        
        # Save timestamp stats
        stats = {
            'total_timestamps_processed': self.timestamp_stats['total_timestamps'],
            'timestamps_cleaned': self.timestamp_stats['cleaned_timestamps'],
            'timestamps_failed': self.timestamp_stats['failed_timestamps'],
            'success_rate': round((1 - self.timestamp_stats['failed_timestamps'] / max(1, self.timestamp_stats['total_timestamps'])) * 100, 2) if self.timestamp_stats['total_timestamps'] > 0 else 100,
            'total_processing_time_minutes': round((time.time() - self.start_time) / 60, 2),
            'folders_processed': self.folders_processed,
            'average_time_per_folder_seconds': round((time.time() - self.start_time) / max(1, self.folders_processed), 2)
        }
        
        output_file = self.output_path / 'processing_stats.json'
        with open(output_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"\nProcessing Statistics:")
        logger.info(f"  Total time: {stats['total_processing_time_minutes']:.1f} minutes")
        logger.info(f"  Average per folder: {stats['average_time_per_folder_seconds']:.1f} seconds")
        logger.info(f"  Trades processed: {self.total_trades_processed:,}")


def main():
    """Main execution function."""
    # Set paths
    source_path = "/Users/jt/magic8/magic8-accuracy-predictor/data/source"
    output_path = "/Users/jt/magic8/magic8-accuracy-predictor/data/processed_optimized_v3"
    
    # Create processor with batch size
    processor = Magic8DataProcessorOptimized(source_path, output_path, batch_size=5000)
    
    # Process all data
    logger.info("Starting Magic8 data processing (optimized v3)...")
    logger.info("This version tracks delta sheet integration")
    
    processor.process_all_folders()
    
    # Save final reports
    logger.info("\nSaving final analysis reports...")
    processor.save_final_reports()
    
    logger.info("\nProcessing complete!")
    logger.info(f"Output saved to: {output_path}")


if __name__ == "__main__":
    main()
