#!/bin/bash

# Run the v3 optimized processor with delta tracking

echo "Magic8 Data Processing - Version 3 (Delta Integration)"
echo "====================================================="
echo ""
echo "This version tracks delta sheet integration"
echo ""

# Create output directory
mkdir -p data/processed_optimized_v3

# Run the processor
python process_magic8_data_optimized_v3.py

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Processing complete!"
    echo ""
    echo "Next steps:"
    echo "1. Verify the data:"
    echo "   python check_optimized_data.py  # Update path to processed_optimized_v3"
    echo ""
    echo "2. Use the new data for Phase 1:"
    echo "   cp data/processed_optimized_v3/magic8_trades_complete.csv data/normalized/normalized_aggregated.csv"
    echo ""
else
    echo "❌ Processing failed!"
    exit 1
fi
