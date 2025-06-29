#!/usr/bin/env python3
"""
Scan all CSV files in the source directory to identify timestamp formatting issues.
This will help us understand all the different timestamp formats and special characters.
"""

import os
import csv
from pathlib import Path
from collections import defaultdict
import re
import json

def scan_csv_files(source_path: str):
    """Scan all CSV files and identify timestamp issues."""
    
    source_dir = Path(source_path)
    issues = defaultdict(list)
    timestamp_formats = defaultdict(int)
    problematic_files = []
    total_files = 0
    
    # Pattern to detect non-printable characters
    non_printable_pattern = re.compile(r'[^\x20-\x7E]')
    
    for folder in sorted(source_dir.iterdir()):
        if not folder.is_dir():
            continue
        
        for file_path in folder.glob('*.csv'):
            total_files += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    
                    for row_num, row in enumerate(reader, 2):  # Start at 2 since header is line 1
                        # Check date and time fields
                        date_val = row.get('Date', '')
                        time_val = row.get('Time', '') or row.get('Hour', '')
                        
                        # Check for non-printable characters
                        if date_val:
                            non_printable = non_printable_pattern.findall(date_val)
                            if non_printable:
                                issues['non_printable_in_date'].append({
                                    'file': str(file_path),
                                    'row': row_num,
                                    'value': repr(date_val),
                                    'chars': [f'\\x{ord(c):02x}' for c in non_printable]
                                })
                                problematic_files.append(str(file_path))
                        
                        if time_val:
                            non_printable = non_printable_pattern.findall(time_val)
                            if non_printable:
                                issues['non_printable_in_time'].append({
                                    'file': str(file_path),
                                    'row': row_num,
                                    'value': repr(time_val),
                                    'chars': [f'\\x{ord(c):02x}' for c in non_printable]
                                })
                                problematic_files.append(str(file_path))
                        
                        # Track timestamp formats
                        if date_val:
                            # Remove non-printable characters for format detection
                            clean_date = non_printable_pattern.sub('', date_val)
                            if '-' in clean_date and clean_date.count('-') == 2:
                                parts = clean_date.split('-')
                                if len(parts[0]) == 2:  # MM-DD-YYYY
                                    timestamp_formats['MM-DD-YYYY'] += 1
                                elif len(parts[0]) == 4:  # YYYY-MM-DD
                                    timestamp_formats['YYYY-MM-DD'] += 1
                            elif '/' in clean_date:
                                timestamp_formats['slash_format'] += 1
                        
                        # Only check first 10 rows per file for performance
                        if row_num > 10:
                            break
                            
            except Exception as e:
                issues['file_errors'].append({
                    'file': str(file_path),
                    'error': str(e)
                })
    
    # Remove duplicates from problematic_files
    problematic_files = list(set(problematic_files))
    
    # Create summary
    summary = {
        'total_files_scanned': total_files,
        'files_with_issues': len(problematic_files),
        'issue_counts': {k: len(v) for k, v in issues.items()},
        'timestamp_formats': dict(timestamp_formats),
        'sample_issues': {
            'non_printable_in_date': issues['non_printable_in_date'][:5] if issues['non_printable_in_date'] else [],
            'non_printable_in_time': issues['non_printable_in_time'][:5] if issues['non_printable_in_time'] else []
        }
    }
    
    return summary, issues, problematic_files

def main():
    """Main execution function."""
    source_path = "/Users/jt/magic8/magic8-accuracy-predictor/data/source"
    
    print("Scanning for timestamp issues...")
    summary, issues, problematic_files = scan_csv_files(source_path)
    
    # Print summary
    print(f"\n{'='*60}")
    print("TIMESTAMP SCAN SUMMARY")
    print(f"{'='*60}")
    print(f"Total files scanned: {summary['total_files_scanned']}")
    print(f"Files with issues: {summary['files_with_issues']}")
    
    print(f"\nIssue breakdown:")
    for issue_type, count in summary['issue_counts'].items():
        print(f"  {issue_type}: {count}")
    
    print(f"\nTimestamp formats found:")
    for fmt, count in summary['timestamp_formats'].items():
        print(f"  {fmt}: {count}")
    
    # Show sample issues
    if summary['sample_issues']['non_printable_in_date']:
        print(f"\nSample non-printable characters in dates:")
        for issue in summary['sample_issues']['non_printable_in_date']:
            print(f"  File: {issue['file']}")
            print(f"  Row: {issue['row']}")
            print(f"  Value: {issue['value']}")
            print(f"  Chars: {issue['chars']}")
            print()
    
    if summary['sample_issues']['non_printable_in_time']:
        print(f"\nSample non-printable characters in times:")
        for issue in summary['sample_issues']['non_printable_in_time']:
            print(f"  File: {issue['file']}")
            print(f"  Row: {issue['row']}")
            print(f"  Value: {issue['value']}")
            print(f"  Chars: {issue['chars']}")
            print()
    
    # Save detailed report
    output_dir = Path("/Users/jt/magic8/magic8-accuracy-predictor/data/processed_fixed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / 'timestamp_issues_report.json', 'w') as f:
        json.dump({
            'summary': summary,
            'problematic_files': problematic_files[:20]  # First 20 files
        }, f, indent=2)
    
    print(f"\nDetailed report saved to: {output_dir / 'timestamp_issues_report.json'}")

if __name__ == "__main__":
    main()
