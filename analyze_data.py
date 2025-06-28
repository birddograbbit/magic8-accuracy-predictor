#!/usr/bin/env python3
"""
Magic8 Data Analyzer
This script examines all CSV files in the Magic8 data directory and extracts
information about their structure, columns, and timestamp formats.
"""

import os
import csv
from datetime import datetime
import pandas as pd
import json
from typing import Dict, List, Any
import re

class Magic8DataAnalyzer:
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.file_info = {}
        self.timestamp_formats = {
            'prediction': '%m-%d-%Y %H:%M:%S',  # UTC
            'trades': ['%m-%d-%Y %H:%M:%S', '%m-%d-%Y', '%H:%M'],  # UTC, Date and Time separate in newer versions
            'delta': ['%m-%d-%Y %H:%M:%S', '%m-%d-%Y %H:%M:%S'],  # EST
            'profit': ['%m-%d-%Y', '%H:%M']  # EST, always separated
        }
        
    def analyze_all_files(self) -> Dict[str, Any]:
        """Analyze all CSV files in the data directory."""
        for year_folder in os.listdir(self.base_path):
            year_path = os.path.join(self.base_path, year_folder)
            if os.path.isdir(year_path) and not year_folder.startswith('.'):
                self.file_info[year_folder] = self.analyze_year_folder(year_path)
        
        return self.file_info
    
    def analyze_year_folder(self, year_path: str) -> Dict[str, Any]:
        """Analyze all CSV files in a year folder."""
        year_info = {
            'path': year_path,
            'files': {}
        }
        
        for filename in os.listdir(year_path):
            if filename.endswith('.csv'):
                file_path = os.path.join(year_path, filename)
                file_type = self.get_file_type(filename)
                if file_type:
                    year_info['files'][file_type] = self.analyze_csv_file(file_path, file_type)
        
        return year_info
    
    def get_file_type(self, filename: str) -> str:
        """Extract file type from filename."""
        filename_lower = filename.lower()
        if 'profit' in filename_lower:
            return 'profit'
        elif 'delta' in filename_lower:
            return 'delta'
        elif 'prediction' in filename_lower:
            return 'prediction'
        elif 'trades' in filename_lower:
            return 'trades'
        return None
    
    def analyze_csv_file(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Analyze a single CSV file."""
        file_info = {
            'path': file_path,
            'type': file_type,
            'columns': [],
            'row_count': 0,
            'timestamp_format': None,
            'timestamp_columns': [],
            'sample_data': [],
            'timezone': 'UTC' if file_type in ['prediction', 'trades'] else 'EST'
        }
        
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)
            file_info['columns'] = list(df.columns)
            file_info['row_count'] = len(df)
            
            # Identify timestamp columns
            file_info['timestamp_columns'] = self.identify_timestamp_columns(df)
            
            # Get sample data (first 5 rows)
            file_info['sample_data'] = df.head(5).to_dict('records')
            
            # Analyze timestamp format
            if file_info['timestamp_columns']:
                file_info['timestamp_format'] = self.analyze_timestamp_format(
                    df, file_info['timestamp_columns'], file_type
                )
            
        except Exception as e:
            file_info['error'] = str(e)
        
        return file_info
    
    def identify_timestamp_columns(self, df: pd.DataFrame) -> List[str]:
        """Identify columns that contain timestamp information."""
        timestamp_columns = []
        
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['when', 'date', 'time', 'day', 'hour']):
                timestamp_columns.append(col)
        
        return timestamp_columns
    
    def analyze_timestamp_format(self, df: pd.DataFrame, timestamp_columns: List[str], 
                                file_type: str) -> Dict[str, Any]:
        """Analyze the format of timestamp columns."""
        format_info = {}
        
        # Handle different timestamp column configurations
        if 'When' in timestamp_columns:
            # Single timestamp column
            sample_value = str(df['When'].iloc[0])
            format_info['type'] = 'single_column'
            format_info['column'] = 'When'
            format_info['sample'] = sample_value
            format_info['format'] = self.detect_datetime_format(sample_value)
            
        elif 'Date' in timestamp_columns and 'Time' in timestamp_columns:
            # Separate date and time columns
            format_info['type'] = 'separate_columns'
            format_info['date_column'] = 'Date'
            format_info['time_column'] = 'Time'
            format_info['date_sample'] = str(df['Date'].iloc[0])
            format_info['time_sample'] = str(df['Time'].iloc[0])
            format_info['date_format'] = self.detect_datetime_format(str(df['Date'].iloc[0]))
            format_info['time_format'] = self.detect_datetime_format(str(df['Time'].iloc[0]))
            
        elif 'Day' in timestamp_columns and 'Hour' in timestamp_columns:
            # Day and Hour columns (profit files)
            format_info['type'] = 'day_hour_columns'
            format_info['day_column'] = 'Day'
            format_info['hour_column'] = 'Hour'
            format_info['day_sample'] = str(df['Day'].iloc[0])
            format_info['hour_sample'] = str(df['Hour'].iloc[0])
            format_info['day_format'] = self.detect_datetime_format(str(df['Day'].iloc[0]))
            format_info['hour_format'] = self.detect_datetime_format(str(df['Hour'].iloc[0]))
        
        return format_info
    
    def detect_datetime_format(self, value: str) -> str:
        """Detect the datetime format of a string value."""
        # Common datetime formats to try
        formats = [
            '%m-%d-%Y %H:%M:%S',
            '%m-%d-%Y %H:%M',
            '%m-%d-%Y',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%H:%M:%S',
            '%H:%M'
        ]
        
        for fmt in formats:
            try:
                datetime.strptime(value.strip(), fmt)
                return fmt
            except:
                continue
        
        return 'unknown'
    
    def generate_summary_report(self) -> str:
        """Generate a summary report of all analyzed files."""
        report = []
        report.append("# Magic8 Data Analysis Report\n")
        report.append(f"Base Path: {self.base_path}\n")
        
        for year_folder, year_data in sorted(self.file_info.items()):
            report.append(f"\n## {year_folder}")
            report.append(f"Path: {year_data['path']}")
            
            for file_type, file_data in year_data['files'].items():
                report.append(f"\n### {file_type.upper()} File")
                report.append(f"- **File Path**: {file_data['path']}")
                report.append(f"- **Row Count**: {file_data['row_count']}")
                report.append(f"- **Timezone**: {file_data['timezone']}")
                report.append(f"- **Columns**: {', '.join(file_data['columns'])}")
                
                if file_data.get('timestamp_format'):
                    tf = file_data['timestamp_format']
                    report.append(f"- **Timestamp Type**: {tf.get('type', 'unknown')}")
                    if tf['type'] == 'single_column':
                        report.append(f"  - Column: {tf['column']}")
                        report.append(f"  - Format: {tf['format']}")
                        report.append(f"  - Sample: {tf['sample']}")
                    elif tf['type'] == 'separate_columns':
                        report.append(f"  - Date Column: {tf['date_column']} (format: {tf['date_format']})")
                        report.append(f"  - Time Column: {tf['time_column']} (format: {tf['time_format']})")
                        report.append(f"  - Samples: {tf['date_sample']} {tf['time_sample']}")
                    elif tf['type'] == 'day_hour_columns':
                        report.append(f"  - Day Column: {tf['day_column']} (format: {tf['day_format']})")
                        report.append(f"  - Hour Column: {tf['hour_column']} (format: {tf['hour_format']})")
                        report.append(f"  - Samples: {tf['day_sample']} {tf['hour_sample']}")
                
                if 'error' in file_data:
                    report.append(f"- **ERROR**: {file_data['error']}")
        
        return '\n'.join(report)
    
    def save_analysis_results(self, output_path: str):
        """Save analysis results to JSON and summary report."""
        # Save detailed JSON
        json_path = os.path.join(output_path, 'data_analysis.json')
        with open(json_path, 'w') as f:
            json.dump(self.file_info, f, indent=2, default=str)
        print(f"Saved detailed analysis to: {json_path}")
        
        # Save summary report
        report_path = os.path.join(output_path, 'data_analysis_report.md')
        with open(report_path, 'w') as f:
            f.write(self.generate_summary_report())
        print(f"Saved summary report to: {report_path}")


def main():
    # Set the base path for data
    base_path = "/Users/jt/magic8/magic8-accuracy-predictor/data/source"
    
    # Create analyzer instance
    analyzer = Magic8DataAnalyzer(base_path)
    
    # Analyze all files
    print("Analyzing Magic8 data files...")
    analyzer.analyze_all_files()
    
    # Save results
    output_path = "/Users/jt/magic8/magic8-accuracy-predictor"
    os.makedirs(output_path, exist_ok=True)
    analyzer.save_analysis_results(output_path)
    
    # Print summary
    print("\n" + analyzer.generate_summary_report())


if __name__ == "__main__":
    main()
