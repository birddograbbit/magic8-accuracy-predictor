#!/bin/bash

# Script to replace old normalized data with new optimized data
# This prepares the data for Phase 1 pipeline

echo "Magic8 Data Replacement Script"
echo "=============================="
echo ""
echo "This script will replace the old normalized data with the new optimized data"
echo "for use in the Phase 1 machine learning pipeline."
echo ""

# Check if optimized data exists
if [ ! -f "data/processed_optimized/magic8_trades_complete.csv" ]; then
    echo "❌ ERROR: Optimized data not found!"
    echo "Please run: ./run_data_processing_optimized.sh first"
    exit 1
fi

# Backup old data
echo "Step 1: Backing up old normalized data..."
if [ -f "data/normalized/normalized_aggregated.csv" ]; then
    cp data/normalized/normalized_aggregated.csv data/normalized/normalized_aggregated_OLD_BACKUP.csv
    echo "✅ Old data backed up to: data/normalized/normalized_aggregated_OLD_BACKUP.csv"
else
    echo "⚠️  No old data found to backup"
fi

# Copy new data
echo ""
echo "Step 2: Copying new optimized data to normalized folder..."
cp data/processed_optimized/magic8_trades_complete.csv data/normalized/normalized_aggregated.csv
echo "✅ New data copied to: data/normalized/normalized_aggregated.csv"

# Copy analysis files
echo ""
echo "Step 3: Copying analysis reports..."
cp data/processed_optimized/*.json data/normalized/
echo "✅ Analysis reports copied"

# Verify the replacement
echo ""
echo "Step 4: Verifying the replacement..."
echo ""

# Quick check using Python
python -c "
import pandas as pd
df = pd.read_csv('data/normalized/normalized_aggregated.csv')
print(f'Total trades: {len(df):,}')
print(f'Columns: {list(df.columns)[:5]}...')
print('\nStrategy distribution:')
for strategy, count in df['strategy'].value_counts().items():
    pct = (count / len(df) * 100).round(2)
    print(f'  {strategy}: {count:,} ({pct}%)')
"

echo ""
echo "✅ Data replacement complete!"
echo ""
echo "You can now proceed with Phase 1:"
echo "  1. Download remaining IBKR data (if not done)"
echo "  2. Run: python src/phase1_data_preparation.py"
echo "  3. Train model: python src/models/xgboost_baseline.py"
echo ""
echo "To verify the new data, run:"
echo "  python check_optimized_data.py"
echo "  python compare_data_sources.py"
