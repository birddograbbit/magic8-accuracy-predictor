#!/bin/bash

# Magic8 Data Processing Script - Optimized Version
# This script runs the optimized data processor with incremental writing

echo "==================================="
echo "Magic8 Data Processing - Optimized"
echo "==================================="
echo ""
echo "This optimized version writes data incrementally to avoid memory issues"
echo "Expected processing time: 15-30 minutes (vs 2+ hours for the old version)"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Create output directory
echo "Creating output directory..."
mkdir -p data/processed_optimized

# Run the optimized processor
echo ""
echo "Starting optimized data processing..."
echo "Data will be written incrementally in batches of 5,000 trades"
echo ""

python process_magic8_data_optimized.py

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Data processing completed successfully!"
    echo ""
    echo "Output files created:"
    echo "  - data/processed_optimized/magic8_trades_complete.csv"
    echo "  - data/processed_optimized/strategy_analysis.json"
    echo "  - data/processed_optimized/symbol_analysis.json"
    echo "  - data/processed_optimized/data_quality_report.json"
    echo "  - data/processed_optimized/processing_stats.json"
    echo ""
    
    # Show quick stats
    if [ -f "data/processed_optimized/strategy_analysis.json" ]; then
        echo "Quick Summary:"
        python -c "
import json
with open('data/processed_optimized/strategy_analysis.json', 'r') as f:
    data = json.load(f)
    print(f'  Total trades processed: {data[\"total_trades\"]:,}')
    print('  Strategy distribution:')
    for strategy, count in data['by_strategy'].items():
        pct = data['by_strategy_pct'][strategy]
        print(f'    - {strategy}: {count:,} trades ({pct}%)')
"
    fi
else
    echo ""
    echo "❌ Error: Data processing failed!"
    echo "Check the logs above for error details."
    exit 1
fi

echo ""
echo "Processing complete!"
