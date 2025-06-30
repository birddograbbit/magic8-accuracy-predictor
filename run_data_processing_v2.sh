#!/bin/bash

# Run the v2 optimized processor with fixed CSV output

echo "Magic8 Data Processing - Version 2 (Fixed)"
echo "=========================================="
echo ""
echo "This version fixes the CSV output consistency issues"
echo ""

# Create output directory
mkdir -p data/processed_optimized_v2

# Run the processor
python process_magic8_data_optimized_v2.py

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Processing complete!"
    echo ""
    echo "Next steps:"
    echo "1. Verify the data:"
    echo "   python check_optimized_data.py  # Update path to processed_optimized_v2"
    echo ""
    echo "2. Use the new data for Phase 1:"
    echo "   cp data/processed_optimized_v2/magic8_trades_complete.csv data/normalized/normalized_aggregated.csv"
    echo ""
else
    echo "❌ Processing failed!"
    exit 1
fi
