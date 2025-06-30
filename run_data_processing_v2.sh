#!/bin/bash

# Magic8 Data Processing Pipeline (Fixed V2)
# This script runs the complete data processing pipeline with timestamp fixes

echo "========================================="
echo "Magic8 Data Processing Pipeline V2"
echo "========================================="
echo ""

# Set the working directory
cd /Users/jt/magic8/magic8-accuracy-predictor

# Step 1: Analyze existing normalized data
echo "Step 1: Analyzing existing normalized data..."
echo "-----------------------------------------"
python analyze_existing_data.py
echo ""

# Step 2: Scan for timestamp issues
echo "Step 2: Scanning for timestamp issues..."
echo "-----------------------------------------"
python scan_timestamp_issues.py
echo ""

# Step 3: Test strategy parsing on sample folders
echo "Step 3: Testing strategy parsing fix on sample folders..."
echo "-----------------------------------------"
python test_strategy_parsing.py
echo ""

# Step 4: Run the fixed data processor V2
echo "Step 4: Running fixed data processor V2 (with timestamp fixes)..."
echo "-----------------------------------------"
python process_magic8_data_fixed_v2.py

# Check if processing was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "Processing Complete!"
    echo "========================================="
    echo ""
    echo "Output files have been saved to:"
    echo "  - data/processed_fixed_v2/magic8_trades_complete.csv"
    echo "  - data/processed_fixed_v2/strategy_analysis.json"
    echo "  - data/processed_fixed_v2/data_quality_report.json"
    echo "  - data/processed_fixed_v2/symbol_analysis.json"
    echo "  - data/processed_fixed_v2/timestamp_processing_stats.json"
    echo ""
    echo "Check the logs above for any warnings or errors."
else
    echo ""
    echo "ERROR: Data processing failed!"
    echo "Check the error messages above for details."
    exit 1
fi
