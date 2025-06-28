#!/usr/bin/env python3
"""
Magic8 Data Normalizer (Large Scale Version)
This script normalizes all Magic8 trading data across multiple years into a
consolidated format aligned to 5-minute intervals from 9:35 AM to 4:00 PM EST.
Enhanced with progress tracking and memory optimization for large datasets.
"""

import os
import csv
from datetime import datetime, timedelta, timezone
import json
from typing import Dict, List, Any, Tuple
import re
from collections import defaultdict
import sys

class Magic8DataNormalizer:
    def __init__(self, base_path: str, analysis_file: str):
        self.base_path = base_path
        self.analysis_file = analysis_file
        self.analysis_data = {}
        self.normalized_data = []
        
        # EST timezone (UTC-5)
        self.est_offset = timedelta(hours=-5)
        
        # Trading hours in EST
        self.market_open = (9, 35)  # 9:35 AM
        self.market_close = (16, 0)  # 4:00 PM
        
        # Generate 5-minute intervals
        self.trading_intervals = self.generate_trading_intervals()
        
        # Progress tracking
        self.total_files = 0
        self.processed_files = 0
        self.error_count = 0
        self.total_records = 0
        
    def load_analysis_data(self):
        """Load the analysis results from JSON file."""
        print("Loading analysis data...")
        with open(self.analysis_file, 'r') as f:
            self.analysis_data = json.load(f)
        
        # Count total files
        for year_data in self.analysis_data.values():
            self.total_files += len(year_data.get('files', {}))
        
        print(f"Found {len(self.analysis_data)} year folders with {self.total_files} files total")
    
    def generate_trading_intervals(self) -> List[Tuple[int, int]]:
        """Generate all 5-minute intervals from 9:35 AM to 4:00 PM EST."""
        intervals = []
        current_time = datetime(2000, 1, 1, self.market_open[0], self.market_open[1])
        end_time = datetime(2000, 1, 1, self.market_close[0], self.market_close[1])
        
        while current_time <= end_time:
            intervals.append((current_time.hour, current_time.minute))
            current_time += timedelta(minutes=5)
        
        return intervals
    
    def parse_timestamp(self, timestamp_data: Dict[str, str], 
                       timestamp_format: Dict[str, Any], 
                       timezone_str: str) -> datetime:
        """Parse timestamp based on the format information."""
        try:
            if timestamp_format['type'] == 'single_column':
                # Single timestamp column
                timestamp_str = timestamp_data.get(timestamp_format['column'], '')
                
                # Handle ISO format with timezone (2022-12-12T09:35:03.089596-05:00)
                if 'T' in timestamp_str and ('+' in timestamp_str or timestamp_str.count('-') > 2):
                    # Parse ISO format
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    # Convert to naive datetime in EST
                    dt = dt.astimezone(timezone.utc).replace(tzinfo=None) - timedelta(hours=5)
                else:
                    # Parse regular format
                    dt = datetime.strptime(timestamp_str.strip(), timestamp_format['format'])
                
            elif timestamp_format['type'] == 'separate_columns':
                # Separate date and time columns
                date_str = timestamp_data.get(timestamp_format['date_column'], '')
                time_str = timestamp_data.get(timestamp_format['time_column'], '')
                combined_str = f"{date_str} {time_str}"
                format_str = f"{timestamp_format['date_format']} {timestamp_format['time_format']}"
                dt = datetime.strptime(combined_str.strip(), format_str)
                
            elif timestamp_format['type'] == 'day_hour_columns':
                # Day and Hour columns
                day_str = timestamp_data.get(timestamp_format['day_column'], '')
                hour_str = timestamp_data.get(timestamp_format['hour_column'], '')
                combined_str = f"{day_str} {hour_str}"
                format_str = f"{timestamp_format['day_format']} {timestamp_format['hour_format']}"
                dt = datetime.strptime(combined_str.strip(), format_str)
            
            else:
                return None
            
            # Convert to EST if needed
            if timezone_str == 'UTC':
                # Convert UTC to EST
                dt = dt - timedelta(hours=5)  # UTC to EST
            
            return dt
            
        except Exception as e:
            # Silently skip timestamp errors to avoid spam
            return None
    
    def normalize_to_interval(self, dt: datetime) -> Tuple[int, int]:
        """Normalize a datetime to the nearest 5-minute interval."""
        # Round to nearest 5 minutes
        minutes = dt.minute
        rounded_minutes = 5 * round(minutes / 5)
        
        if rounded_minutes == 60:
            hour = dt.hour + 1
            minute = 0
        else:
            hour = dt.hour
            minute = rounded_minutes
        
        return (hour, minute)
    
    def process_file(self, file_info: Dict[str, Any], year_folder: str) -> List[Dict[str, Any]]:
        """Process a single CSV file and return normalized records."""
        records = []
        file_type = file_info['type']
        file_path = file_info['path']
        
        # Skip files with unknown timestamp format
        if file_info.get('timestamp_format', {}).get('format') == 'unknown':
            self.error_count += 1
            return records
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Skip summary rows in profit files
                    if file_type == 'profit' and any(keyword in str(row.get('Day', '')) for keyword in 
                                                    ['Total', 'Symbol', 'Wins', 'Losses', 'Accuracy', 
                                                     'Profit', 'Butterfly', 'Iron Condor', 'Vertical', 
                                                     'Sonar', 'Risk', 'Reward', 'Ratio']):
                        continue
                    
                    # Parse timestamp
                    dt = self.parse_timestamp(row, file_info['timestamp_format'], 
                                            file_info['timezone'])
                    
                    if dt is None:
                        continue
                    
                    # Normalize to 5-minute interval
                    interval = self.normalize_to_interval(dt)
                    
                    # Skip if outside trading hours
                    if not self.is_trading_hours(interval):
                        continue
                    
                    # Create normalized record
                    record = {
                        'date': dt.strftime('%Y-%m-%d'),
                        'hour': interval[0],
                        'minute': interval[1],
                        'time_est': f"{interval[0]:02d}:{interval[1]:02d}",
                        'year_folder': year_folder,
                        'file_type': file_type,
                        'original_timestamp': self.get_original_timestamp(row, file_info)
                    }
                    
                    # Add file-specific fields
                    if file_type == 'prediction':
                        record.update(self.extract_prediction_fields(row))
                    elif file_type == 'trades':
                        record.update(self.extract_trades_fields(row))
                    elif file_type == 'delta':
                        record.update(self.extract_delta_fields(row))
                    elif file_type == 'profit':
                        record.update(self.extract_profit_fields(row))
                    
                    records.append(record)
                    self.total_records += 1
        
        except Exception as e:
            self.error_count += 1
            print(f"Error processing file {file_path}: {e}")
        
        return records
    
    def is_trading_hours(self, interval: Tuple[int, int]) -> bool:
        """Check if the interval is within trading hours."""
        hour, minute = interval
        start_minutes = self.market_open[0] * 60 + self.market_open[1]
        end_minutes = self.market_close[0] * 60 + self.market_close[1]
        interval_minutes = hour * 60 + minute
        
        return start_minutes <= interval_minutes <= end_minutes
    
    def get_original_timestamp(self, row: Dict[str, str], file_info: Dict[str, Any]) -> str:
        """Get the original timestamp string from the row."""
        tf = file_info['timestamp_format']
        
        if tf['type'] == 'single_column':
            return row.get(tf['column'], '')
        elif tf['type'] == 'separate_columns':
            return f"{row.get(tf['date_column'], '')} {row.get(tf['time_column'], '')}"
        elif tf['type'] == 'day_hour_columns':
            return f"{row.get(tf['day_column'], '')} {row.get(tf['hour_column'], '')}"
        
        return ''
    
    def extract_prediction_fields(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Extract fields from prediction files."""
        return {
            'symbol': row.get('Symbol', ''),
            'price': self.safe_float(row.get('Price', '')),
            'predicted': self.safe_float(row.get('Predicted', '')),
            'short_term': self.safe_float(row.get('ShortTerm', '')),
            'long_term': self.safe_float(row.get('LongTerm', '')),
            'closing': self.safe_float(row.get('Closing', '')),
            'difference': self.safe_float(row.get('Difference', ''))
        }
    
    def extract_trades_fields(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Extract fields from trades files."""
        fields = {
            'symbol': row.get('Symbol', ''),
            'strategy_name': row.get('Name', ''),
            'premium': self.safe_float(row.get('Premium', '')),
            'predicted': self.safe_float(row.get('Predicted', '')),
            'trade': row.get('Trade', '')
        }
        
        # Handle old format (2022) vs new format (2024+)
        if 'Probability' in row:
            # Old format
            fields.update({
                'probability': self.safe_float(row.get('Probability', '')),
                'closed': self.safe_float(row.get('Closed', '')),
                'profited': row.get('Profited', '').lower() == 'true',
                'expired': row.get('Expired', '').lower() == 'true'
            })
        else:
            # New format
            fields.update({
                'source': row.get('Source', ''),
                'risk': self.safe_float(row.get('Risk', '')),
                'expected_move': self.safe_float(row.get('ExpectedMove', '')),
                'low': self.safe_float(row.get('Low', '')),
                'high': self.safe_float(row.get('High', '')),
                'target1': self.safe_float(row.get('Target1', '')),
                'target2': self.safe_float(row.get('Target2', '')),
                'closing': self.safe_float(row.get('Closing', ''))
            })
        
        return fields
    
    def extract_delta_fields(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Extract fields from delta files."""
        return {
            'symbol': row.get('Symbol', ''),
            'price': self.safe_float(row.get('Price', '')),
            'call_delta': self.safe_float(row.get('CallDelta', '')),
            'put_delta': self.safe_float(row.get('PutDelta', '')),
            'predicted': self.safe_float(row.get('Predicted', '')),
            'short_term': self.safe_float(row.get('ShortTerm', '')),
            'long_term': self.safe_float(row.get('LongTerm', '')),
            'closing': self.safe_float(row.get('Closing', ''))
        }
    
    def extract_profit_fields(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Extract fields from profit files."""
        fields = {
            'symbol': row.get('Symbol', ''),
            'price': self.safe_float(row.get('Price', '')),
            'strategy_name': row.get('Name', ''),
            'premium': self.safe_float(row.get('Premium', '')),
            'predicted': self.safe_float(row.get('Predicted', '')),
            'trade': row.get('Trade', '')
        }
        
        # Handle old format (2023) vs new format (2024+)
        if 'Profit' in row:
            # Old format
            fields.update({
                'closed': self.safe_float(row.get('Closed', '')),
                'expired': row.get('Expired', '').lower() == 'true',
                'risk': self.safe_float(row.get('Risk', '')),
                'reward': self.safe_float(row.get('Reward', '')),
                'ratio': self.safe_float(row.get('Ratio', '')),
                'profit': self.safe_float(row.get('Profit', ''))
            })
        else:
            # New format
            fields.update({
                'low': self.safe_float(row.get('Low', '')),
                'high': self.safe_float(row.get('High', '')),
                'closed': self.safe_float(row.get('Closed', '')),
                'risk': self.safe_float(row.get('Risk', '')),
                'reward': self.safe_float(row.get('Reward', '')),
                'stop': self.safe_float(row.get('Stop', '')),
                'raw': self.safe_float(row.get('Raw', '')),
                'managed': self.safe_float(row.get('Managed', ''))
            })
        
        return fields
    
    def safe_float(self, value: str) -> float:
        """Safely convert string to float, returning None if conversion fails."""
        try:
            return float(value) if value else None
        except:
            return None
    
    def update_progress(self):
        """Update progress display."""
        self.processed_files += 1
        if self.processed_files % 10 == 0 or self.processed_files == self.total_files:
            percent = (self.processed_files / self.total_files * 100) if self.total_files > 0 else 0
            print(f"\rProgress: {self.processed_files}/{self.total_files} files ({percent:.1f}%) | "
                  f"Records: {self.total_records:,} | Errors: {self.error_count}", end='', flush=True)
    
    def normalize_all_data(self):
        """Process all files and create normalized dataset."""
        self.load_analysis_data()
        
        all_records = []
        
        # Sort year folders for consistent processing
        sorted_years = sorted(self.analysis_data.items())
        
        print("\nProcessing files...")
        for year_folder, year_data in sorted_years:
            for file_type, file_info in year_data['files'].items():
                records = self.process_file(file_info, year_folder)
                all_records.extend(records)
                self.update_progress()
        
        print(f"\n\nProcessing complete!")
        print(f"Total records extracted: {len(all_records):,}")
        
        # Sort records by date and time
        print("\nSorting records...")
        all_records.sort(key=lambda x: (x['date'], x['hour'], x['minute']))
        
        self.normalized_data = all_records
        return all_records
    
    def aggregate_by_interval(self) -> List[Dict[str, Any]]:
        """Aggregate all data by date and 5-minute interval."""
        print("\nAggregating data by intervals...")
        
        # Group records by date and interval
        interval_groups = defaultdict(list)
        
        for record in self.normalized_data:
            key = (record['date'], record['hour'], record['minute'])
            interval_groups[key].append(record)
        
        # Create aggregated records
        aggregated_data = []
        
        for (date, hour, minute), records in sorted(interval_groups.items()):
            # Initialize aggregated record
            agg_record = {
                'date': date,
                'hour': hour,
                'minute': minute,
                'time_est': f"{hour:02d}:{minute:02d}",
                'interval_datetime': f"{date} {hour:02d}:{minute:02d}:00",
                'record_count': len(records),
                'file_types': list(set(r['file_type'] for r in records))
            }
            
            # Aggregate data by file type
            for file_type in ['prediction', 'trades', 'delta', 'profit']:
                type_records = [r for r in records if r['file_type'] == file_type]
                if type_records:
                    # For simplicity, take the first record of each type
                    # In production, you might want to aggregate differently
                    prefix = file_type[:4]  # pred, trad, delt, prof
                    for key, value in type_records[0].items():
                        if key not in ['date', 'hour', 'minute', 'time_est', 
                                      'year_folder', 'file_type', 'original_timestamp']:
                            agg_record[f"{prefix}_{key}"] = value
            
            aggregated_data.append(agg_record)
        
        print(f"Created {len(aggregated_data):,} aggregated intervals")
        return aggregated_data
    
    def save_normalized_data(self, output_path: str):
        """Save normalized data to CSV files."""
        # Save raw normalized data in chunks to handle large files
        print("\nSaving raw normalized data...")
        raw_file = os.path.join(output_path, 'normalized_raw.csv')
        
        if self.normalized_data:
            # Get all unique fieldnames from ALL records
            print("Collecting all unique field names...")
            fieldnames = set()
            for i, record in enumerate(self.normalized_data):
                fieldnames.update(record.keys())
                if i % 10000 == 0:
                    print(f"\rScanning fields: {i:,}/{len(self.normalized_data):,} records", end='', flush=True)
            fieldnames = sorted(list(fieldnames))
            print(f"\nFound {len(fieldnames)} unique fields")
            
            # Write in chunks
            chunk_size = 50000
            with open(raw_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for i in range(0, len(self.normalized_data), chunk_size):
                    chunk = self.normalized_data[i:i+chunk_size]
                    writer.writerows(chunk)
                    print(f"\rWriting raw data: {min(i+chunk_size, len(self.normalized_data)):,}/{len(self.normalized_data):,} records", end='', flush=True)
            
            print(f"\n\nSaved raw normalized data to: {raw_file}")
            print(f"Total records: {len(self.normalized_data):,}")
        
        # Save aggregated data
        print("\nProcessing aggregated data...")
        aggregated_data = self.aggregate_by_interval()
        agg_file = os.path.join(output_path, 'normalized_aggregated.csv')
        
        if aggregated_data:
            # Get all unique fieldnames
            fieldnames = set()
            for record in aggregated_data:
                fieldnames.update(record.keys())
            fieldnames = sorted(list(fieldnames))
            
            with open(agg_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(aggregated_data)
            
            print(f"\nSaved aggregated data to: {agg_file}")
            print(f"Total intervals: {len(aggregated_data):,}")
        
        # Save summary statistics
        self.save_summary_statistics(output_path)
    
    def save_summary_statistics(self, output_path: str):
        """Save summary statistics about the normalized data."""
        print("\nGenerating summary statistics...")
        
        stats = {
            'total_records': len(self.normalized_data),
            'date_range': {
                'start': min(r['date'] for r in self.normalized_data) if self.normalized_data else None,
                'end': max(r['date'] for r in self.normalized_data) if self.normalized_data else None
            },
            'records_by_type': defaultdict(int),
            'records_by_year': defaultdict(int),
            'symbols': set(),
            'processing_stats': {
                'total_files': self.total_files,
                'processed_files': self.processed_files,
                'error_count': self.error_count
            }
        }
        
        for record in self.normalized_data:
            stats['records_by_type'][record['file_type']] += 1
            stats['records_by_year'][record['year_folder']] += 1
            if 'symbol' in record and record['symbol']:
                stats['symbols'].add(record['symbol'])
        
        stats['symbols'] = sorted(list(stats['symbols']))
        stats['records_by_type'] = dict(stats['records_by_type'])
        stats['records_by_year'] = dict(stats['records_by_year'])
        
        stats_file = os.path.join(output_path, 'normalization_stats.json')
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"\nSaved statistics to: {stats_file}")


def main():
    # Set paths
    base_path = "/Users/jt/magic8/magic8-accuracy-predictor/data/source"
    analysis_file = "/Users/jt/magic8/magic8-accuracy-predictor/data_analysis.json"
    output_path = "/Users/jt/magic8/magic8-accuracy-predictor/data/normalized"
    
    # Create output directory
    os.makedirs(output_path, exist_ok=True)
    
    # Create normalizer instance
    normalizer = Magic8DataNormalizer(base_path, analysis_file)
    
    # Normalize all data
    print("Magic8 Data Normalizer (Large Scale Version)")
    print("=" * 60)
    normalizer.normalize_all_data()
    
    # Save results
    normalizer.save_normalized_data(output_path)
    
    print("\nNormalization complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
