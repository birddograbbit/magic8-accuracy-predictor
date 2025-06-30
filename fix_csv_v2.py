#!/usr/bin/env python3
"""
Fix CSV parsing issues - Version 2
Handles missing fields without losing data
"""

import csv
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def analyze_csv_structure(file_path: str, sample_size: int = 1000):
    """Analyze the CSV structure to understand the issue."""
    logger.info(f"Analyzing CSV structure...")
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        # Read header
        header_line = f.readline().strip()
        header_fields = header_line.split(',')
        expected_fields = len(header_fields)
        
        logger.info(f"Header has {expected_fields} fields: {header_fields}")
        
        # Analyze field counts
        field_counts = {}
        line_samples = {}
        
        for i, line in enumerate(f):
            if i >= sample_size:
                break
                
            field_count = len(line.strip().split(','))
            field_counts[field_count] = field_counts.get(field_count, 0) + 1
            
            # Store samples of different field counts
            if field_count not in line_samples and len(line_samples) < 5:
                line_samples[field_count] = line.strip()
        
        logger.info(f"\nField count distribution (first {sample_size} lines):")
        for count, freq in sorted(field_counts.items()):
            logger.info(f"  {count} fields: {freq} lines")
        
        # Show samples
        logger.info(f"\nSample lines:")
        for count, sample in sorted(line_samples.items()):
            logger.info(f"  {count} fields: {sample[:100]}...")
            
        return header_fields, field_counts


def fix_csv_missing_fields(input_path: str, output_path: str):
    """Fix CSV by adding missing fields to incomplete rows."""
    logger.info(f"\nFixing CSV by handling missing fields...")
    
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as infile:
        # Read and parse header
        header_line = infile.readline()
        reader = csv.reader([header_line])
        header_fields = next(reader)
        num_expected_fields = len(header_fields)
        
        logger.info(f"Expected {num_expected_fields} fields")
        
        # Check if 'datetime' is the potentially missing field
        if 'datetime' in header_fields:
            datetime_index = header_fields.index('datetime')
            logger.info(f"'datetime' field is at index {datetime_index}")
        
        # Process file
        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(header_fields)
            
            lines_processed = 0
            lines_fixed = 0
            lines_unchanged = 0
            
            for line_num, line in enumerate(infile, start=2):
                try:
                    # Parse line
                    reader = csv.reader([line])
                    fields = next(reader)
                    
                    if len(fields) == num_expected_fields:
                        # Correct number of fields
                        writer.writerow(fields)
                        lines_unchanged += 1
                    elif len(fields) == num_expected_fields - 1:
                        # Missing one field - likely the datetime column
                        # Add empty field at the end (where datetime usually is)
                        fields.append('')
                        writer.writerow(fields)
                        lines_fixed += 1
                    else:
                        # Handle other cases by padding or truncating
                        if len(fields) < num_expected_fields:
                            # Pad with empty fields
                            while len(fields) < num_expected_fields:
                                fields.append('')
                        else:
                            # Too many fields - try to combine extras
                            # This might be due to commas in descriptions
                            if len(fields) > num_expected_fields and 'trade_description' in header_fields:
                                desc_index = header_fields.index('trade_description')
                                # Combine extra fields into trade_description
                                extra_fields = len(fields) - num_expected_fields
                                combined_desc = ','.join(fields[desc_index:desc_index + extra_fields + 1])
                                new_fields = fields[:desc_index] + [combined_desc] + fields[desc_index + extra_fields + 1:]
                                fields = new_fields[:num_expected_fields]
                            else:
                                # Just truncate
                                fields = fields[:num_expected_fields]
                        
                        writer.writerow(fields)
                        lines_fixed += 1
                    
                    lines_processed += 1
                    
                    if lines_processed % 100000 == 0:
                        logger.info(f"Processed {lines_processed:,} lines...")
                        
                except Exception as e:
                    logger.warning(f"Error on line {line_num}: {e}")
                    continue
            
            logger.info(f"\nProcessing complete:")
            logger.info(f"  Lines processed: {lines_processed:,}")
            logger.info(f"  Lines unchanged: {lines_unchanged:,}")
            logger.info(f"  Lines fixed: {lines_fixed:,}")
            
            return lines_processed


def verify_fixed_file(file_path: str):
    """Verify the fixed file can be loaded and check its contents."""
    logger.info(f"\nVerifying fixed file...")
    
    try:
        # Load with pandas
        df = pd.read_csv(file_path, low_memory=False)
        logger.info(f"✅ File successfully loaded!")
        logger.info(f"   Total rows: {len(df):,}")
        logger.info(f"   Columns: {list(df.columns)}")
        
        # Check for null values in key columns
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            logger.info(f"\nNull values per column:")
            for col, count in null_counts[null_counts > 0].items():
                logger.info(f"   {col}: {count:,}")
        
        # Strategy distribution
        if 'strategy' in df.columns:
            logger.info(f"\nStrategy distribution:")
            strategy_counts = df['strategy'].value_counts()
            total_trades = len(df)
            for strategy, count in strategy_counts.items():
                pct = (count / total_trades * 100)
                logger.info(f"   {strategy}: {count:,} ({pct:.2f}%)")
        
        # Check if we have all expected rows
        logger.info(f"\nExpected rows: 1,527,804")
        logger.info(f"Recovered rows: {len(df):,}")
        recovery_rate = (len(df) / 1527804 * 100)
        logger.info(f"Recovery rate: {recovery_rate:.1f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error loading file: {e}")
        return False


def main():
    """Main function to fix CSV issues."""
    input_path = "data/processed_optimized/magic8_trades_complete.csv"
    output_path = "data/processed_optimized/magic8_trades_complete_fixed.csv"
    
    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    # Step 1: Analyze the structure
    logger.info("Step 1: Analyzing CSV structure...")
    header_fields, field_counts = analyze_csv_structure(input_path, sample_size=10000)
    
    # Step 2: Fix the CSV
    logger.info("\nStep 2: Fixing CSV...")
    total_rows = fix_csv_missing_fields(input_path, output_path)
    
    # Step 3: Verify the fix
    logger.info("\nStep 3: Verifying fixed file...")
    if verify_fixed_file(output_path):
        logger.info(f"\n✅ Fix successful!")
        logger.info(f"Fixed file saved as: {output_path}")
        logger.info("\nTo use the fixed file, run:")
        logger.info(f"  mv {output_path} {input_path}")
    else:
        logger.error(f"\n❌ Fix failed - please check the output")


if __name__ == "__main__":
    main()
