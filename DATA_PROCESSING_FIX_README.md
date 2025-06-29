# Magic8 Data Processing Fix

## Overview

This directory contains the fixed data processing scripts that correctly handle all Magic8 trading data based on the discoveries from our analysis.

## Key Issues Fixed

1. **Sonar Strategy Mislabeling** - The most critical fix
   - OLD: Parsed strategy from `Trade` column (e.g., "SELL -1 Iron Condor...")
   - NEW: Parse strategy from `Name` column (correctly shows "Sonar")

2. **Multiple File Format Support**
   - Handles 3 different profit file formats (2023, 2024, 2025)
   - Correctly maps columns for each year

3. **Timezone Handling**
   - Profit/Delta files: EST/EDT (no conversion needed)
   - Trades files: UTC → EST/EDT conversion

4. **Complete Symbol Coverage**
   - Includes all 8 symbols: SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA
   - AAPL/TSLA included from profit files even without trades data

5. **Data Quality Tracking**
   - Flags negative premiums
   - Tracks zero premiums
   - Reports unknown strategies/symbols

## Scripts

### Main Processing Script
- `process_magic8_data_fixed.py` - Complete data processor with all fixes

### Testing & Analysis Scripts
- `test_strategy_parsing.py` - Quick test to verify strategy parsing fix
- `analyze_existing_data.py` - Shows problems in existing normalized data
- `run_data_processing.sh` - Runs the complete pipeline

## Usage

### Quick Test
```bash
# Test strategy parsing on sample folders
python test_strategy_parsing.py
```

### Full Processing
```bash
# Run complete pipeline
./run_data_processing.sh

# Or run individually:
python process_magic8_data_fixed.py
```

### Manual Processing
```python
from process_magic8_data_fixed import Magic8DataProcessor

# Create processor
processor = Magic8DataProcessor(
    source_path="/path/to/data/source",
    output_path="/path/to/output"
)

# Process all data
processor.process_all_folders()
processor.save_processed_data()
```

## Output Files

The processor creates these files in `data/processed_fixed/`:

1. **magic8_trades_complete.csv** - All trades with correct strategies
2. **strategy_analysis.json** - Strategy distribution statistics
3. **symbol_analysis.json** - Symbol coverage analysis
4. **data_quality_report.json** - Data quality issues found

## Expected Results

After fixing the strategy parsing:

### Before (Incorrect)
- Butterfly: ~97%
- Iron Condor: ~3%
- Vertical: <1%
- Sonar: 0% (missing!)

### After (Correct)
- Butterfly: ~25%
- Iron Condor: ~25%
- Vertical: ~25%
- Sonar: ~25%

## Data Quality Notes

The processor will report these known issues:
- Some trades have negative premiums (data entry errors)
- Some trades have zero premiums
- Risk/Reward/Ratio fields are 0.0 in early 2023 data

These are logged but not excluded from processing.

## Performance

Processing ~600 daily folders takes approximately:
- Quick test: < 1 minute
- Full processing: 5-10 minutes

## Troubleshooting

If you see:
- "Sonar strategy is MISSING" - The old normalization script has the bug
- High Butterfly percentage (>90%) - Strategy parsing from wrong column
- Missing AAPL/TSLA - These only appear in profit files, not trades

## Next Steps

After running the fixed processor:
1. Verify strategy distribution is ~25% each
2. Check all 8 symbols are present
3. Use `magic8_trades_complete.csv` for ML model training
4. Review `data_quality_report.json` for any issues

---

Created: June 29, 2025
Author: Magic8 Data Team
