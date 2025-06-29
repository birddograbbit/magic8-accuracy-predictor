# Timestamp Parsing Issue and Solution

## Problem Description

When running the data processing pipeline, we encountered timestamp parsing errors:

```
Failed to parse timestamp: 08-05-2024 13:35 - time data '\x0c08-05-2024 13:35' does not match format '%m-%d-%Y %H:%M'
```

The issue was caused by non-printable characters (specifically form feed `\x0c`) appearing at the beginning of some timestamp values in the CSV files.

## Root Cause

1. **Non-printable characters**: Some CSV files contain form feed characters (`\x0c`) or other non-printable characters in timestamp fields
2. **Multiple date formats**: The data uses different date formats across files (MM-DD-YYYY, YYYY-MM-DD, etc.)
3. **Encoding issues**: File encoding problems may introduce special characters

## Solution Implemented

### 1. Timestamp Issue Scanner (`scan_timestamp_issues.py`)
- Scans all CSV files to identify files with problematic timestamps
- Detects non-printable characters in date/time fields
- Generates a report of affected files and character types

### 2. Improved Data Processor (`process_magic8_data_fixed_v2.py`)
Key improvements:

#### a. Non-printable Character Removal
```python
def clean_string(self, value: str) -> str:
    """Remove non-printable characters from string."""
    if not value:
        return value
    return self.non_printable_pattern.sub('', value)
```

#### b. Flexible Timestamp Parsing
```python
def parse_timestamp_flexible(self, date_str: str, time_str: str = None) -> Optional[str]:
    # Clean strings first
    date_str = self.clean_string(date_str)
    time_str = self.clean_string(time_str)
    
    # Try multiple date formats
    date_formats = [
        '%m-%d-%Y',     # MM-DD-YYYY
        '%Y-%m-%d',     # YYYY-MM-DD
        '%m/%d/%Y',     # MM/DD/YYYY
        '%Y/%m/%d',     # YYYY/MM/DD
        '%d-%m-%Y',     # DD-MM-YYYY
        '%d/%m/%Y',     # DD/MM/YYYY
    ]
```

#### c. Row-level Error Handling
- Continues processing even when individual rows fail
- Logs errors without stopping the entire process
- Tracks failed rows for quality reporting

#### d. Timestamp Processing Statistics
- Tracks total timestamps processed
- Counts timestamps that required cleaning
- Records parsing failures
- Calculates success rate

### 3. Updated Pipeline Runner (`run_data_processing_v2.sh`)
Runs the complete pipeline with:
1. Existing data analysis
2. Timestamp issue scanning
3. Strategy parsing testing
4. Fixed data processing with V2 processor

## Usage

To run the fixed data processing pipeline:

```bash
# Make the script executable
chmod +x run_data_processing_v2.sh

# Run the complete pipeline
./run_data_processing_v2.sh
```

## Output Files

The fixed processor generates the following files in `data/processed_fixed_v2/`:

1. **magic8_trades_complete.csv** - Complete processed trade data
2. **strategy_analysis.json** - Strategy distribution statistics
3. **data_quality_report.json** - Data quality issues and counts
4. **symbol_analysis.json** - Symbol coverage analysis
5. **timestamp_processing_stats.json** - Timestamp cleaning statistics

## Verification

After running the pipeline, check:

1. **Timestamp Processing Stats**:
   ```json
   {
     "total_timestamps_processed": 123456,
     "timestamps_cleaned": 1234,
     "timestamps_failed": 10,
     "success_rate": 99.99
   }
   ```

2. **Strategy Distribution**:
   - Should show all 4 strategies: Butterfly, Iron Condor, Vertical, Sonar
   - Each strategy should have reasonable representation (not 97% Butterfly)

3. **Data Quality Report**:
   - Check for row_errors to see which specific rows failed
   - Review unknown_strategies to ensure all strategies are recognized

## Benefits of the Fix

1. **Robustness**: Handles corrupted or malformed timestamps gracefully
2. **Completeness**: Processes all data instead of failing on errors
3. **Transparency**: Provides detailed statistics on data cleaning
4. **Flexibility**: Supports multiple timestamp formats
5. **Quality Control**: Tracks and reports all data quality issues

## Future Improvements

1. Add support for more date formats if discovered
2. Implement automatic format detection
3. Add data validation before processing
4. Create pre-processing data cleaning utility

---

**Last Updated**: June 29, 2025  
**Version**: 2.0 (Fixed timestamp parsing)
