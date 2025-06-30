#!/usr/bin/env python3
"""
Fix CSV parsing issues in the optimized data
"""

import csv
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def diagnose_csv_issues(file_path: str):
    """Diagnose CSV parsing issues by reading line by line."""
    logger.info(f"Diagnosing CSV issues in {file_path}")
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        # Read header
        header = f.readline().strip()
        header_fields = header.split(',')
        expected_fields = len(header_fields)
        
        logger.info(f"Header has {expected_fields} fields")
        logger.info(f"Header fields: {header_fields}")
        
        # Check each line
        problematic_lines = []
        line_num = 1
        
        for line in f:
            line_num += 1
            # Count fields (basic split - doesn't handle quoted fields)
            field_count = len(line.strip().split(','))
            
            if field_count != expected_fields:
                problematic_lines.append({
                    'line_num': line_num,
                    'field_count': field_count,
                    'line': line.strip()[:200]  # First 200 chars
                })
                
                if len(problematic_lines) <= 10:
                    logger.warning(f"Line {line_num}: Expected {expected_fields} fields, found {field_count}")
                    logger.warning(f"  Preview: {line.strip()[:100]}...")
        
        logger.info(f"\nTotal problematic lines: {len(problematic_lines)}")
        return problematic_lines, header_fields


def fix_csv_with_proper_quoting(input_path: str, output_path: str):
    """Fix CSV by reading with pandas chunk by chunk and re-writing with proper quoting."""
    logger.info(f"Attempting to fix CSV using pandas chunks...")
    
    fixed_rows = 0
    total_rows = 0
    
    # First, try to read what we can
    chunks = []
    chunk_size = 100000
    
    try:
        # Read in chunks, handling errors
        for chunk_num in range(0, 20):  # Process up to 2M rows
            skip_rows = chunk_num * chunk_size
            
            try:
                chunk = pd.read_csv(
                    input_path,
                    nrows=chunk_size,
                    skiprows=range(1, skip_rows + 1) if skip_rows > 0 else None,
                    on_bad_lines='skip',
                    encoding='utf-8',
                    encoding_errors='ignore'
                )
                chunks.append(chunk)
                total_rows += len(chunk)
                logger.info(f"Read chunk {chunk_num + 1}: {len(chunk)} rows")
                
                if len(chunk) < chunk_size:
                    break
                    
            except Exception as e:
                logger.error(f"Error reading chunk {chunk_num + 1}: {e}")
                break
        
        if chunks:
            # Combine all chunks
            df = pd.concat(chunks, ignore_index=True)
            logger.info(f"Successfully read {len(df)} rows")
            
            # Write with proper quoting
            df.to_csv(output_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
            logger.info(f"Wrote fixed CSV to {output_path}")
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to fix with pandas: {e}")
        return False


def fix_csv_line_by_line(input_path: str, output_path: str):
    """Fix CSV by processing line by line with proper CSV handling."""
    logger.info("Fixing CSV line by line with proper escaping...")
    
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as infile:
        # Read header
        header = infile.readline()
        
        # Parse header properly
        reader = csv.reader([header])
        header_fields = next(reader)
        num_fields = len(header_fields)
        
        logger.info(f"Expected fields: {num_fields}")
        
        # Write fixed file
        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(header_fields)
            
            # Process lines
            lines_processed = 0
            lines_fixed = 0
            lines_skipped = 0
            
            for line_num, line in enumerate(infile, start=2):
                try:
                    # Parse line with csv reader
                    reader = csv.reader([line])
                    fields = next(reader)
                    
                    if len(fields) == num_fields:
                        writer.writerow(fields)
                        lines_processed += 1
                    elif len(fields) > num_fields:
                        # Try to fix by combining extra fields in trade_description
                        # Assume extra commas are in the trade_description field (usually one of the last)
                        fixed_fields = fields[:num_fields-1]
                        # Combine extra fields into the last field
                        combined_last = ','.join(fields[num_fields-1:])
                        fixed_fields.append(combined_last)
                        writer.writerow(fixed_fields)
                        lines_fixed += 1
                    else:
                        lines_skipped += 1
                        if lines_skipped <= 10:
                            logger.warning(f"Skipping line {line_num}: has {len(fields)} fields")
                    
                    if (lines_processed + lines_fixed) % 100000 == 0:
                        logger.info(f"Processed {lines_processed + lines_fixed:,} lines...")
                        
                except Exception as e:
                    lines_skipped += 1
                    if lines_skipped <= 10:
                        logger.warning(f"Error on line {line_num}: {e}")
            
            logger.info(f"\nProcessing complete:")
            logger.info(f"  Lines processed: {lines_processed:,}")
            logger.info(f"  Lines fixed: {lines_fixed:,}")
            logger.info(f"  Lines skipped: {lines_skipped:,}")
            logger.info(f"  Total output: {lines_processed + lines_fixed:,}")


def main():
    """Main function to fix CSV issues."""
    input_path = "data/processed_optimized/magic8_trades_complete.csv"
    output_path = "data/processed_optimized/magic8_trades_complete_fixed.csv"
    
    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    # First diagnose the issues
    logger.info("Step 1: Diagnosing CSV issues...")
    problematic_lines, header_fields = diagnose_csv_issues(input_path)
    
    # Try pandas fix first (faster)
    logger.info("\nStep 2: Attempting pandas-based fix...")
    if not fix_csv_with_proper_quoting(input_path, output_path):
        # Fall back to line-by-line fix
        logger.info("\nStep 3: Using line-by-line fix...")
        fix_csv_line_by_line(input_path, output_path)
    
    # Verify the fix
    logger.info("\nStep 4: Verifying fixed file...")
    try:
        df = pd.read_csv(output_path)
        logger.info(f"✅ Fixed file successfully loaded!")
        logger.info(f"   Total rows: {len(df):,}")
        logger.info(f"   Columns: {list(df.columns)}")
        
        # Quick stats
        if 'strategy' in df.columns:
            logger.info("\nStrategy distribution in fixed file:")
            for strategy, count in df['strategy'].value_counts().items():
                pct = (count / len(df) * 100).round(2)
                logger.info(f"   {strategy}: {count:,} ({pct}%)")
        
        # Rename fixed file to original
        logger.info(f"\n✅ Fix successful! Fixed file saved as: {output_path}")
        logger.info("To use the fixed file, run:")
        logger.info(f"  mv {output_path} {input_path}")
        
    except Exception as e:
        logger.error(f"❌ Fixed file still has issues: {e}")


if __name__ == "__main__":
    main()
