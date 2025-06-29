#!/bin/bash
# Run the complete Magic8 data processing pipeline

echo "========================================"
echo "Magic8 Data Processing Pipeline (Fixed)"
echo "========================================"
echo ""

# Change to project directory
cd /Users/jt/magic8/magic8-accuracy-predictor

# Step 1: Analyze existing data to show the problem
echo "Step 1: Analyzing existing normalized data..."
echo "----------------------------------------"
python analyze_existing_data.py
echo ""

# Step 2: Test strategy parsing fix
echo "Step 2: Testing strategy parsing fix on sample folders..."
echo "----------------------------------------"
python test_strategy_parsing.py
echo ""

# Step 3: Run the fixed data processor
echo "Step 3: Running fixed data processor..."
echo "----------------------------------------"
python process_magic8_data_fixed.py
echo ""

# Step 4: Show results
echo "Step 4: Summary of results..."
echo "----------------------------------------"
if [ -f "data/processed_fixed/strategy_analysis.json" ]; then
    echo "Strategy distribution from fixed processor:"
    python -c "
import json
with open('data/processed_fixed/strategy_analysis.json', 'r') as f:
    data = json.load(f)
    print(f\"Total trades: {data['total_trades']:,}\")
    print(\"\\nStrategy distribution:\")
    for strategy, count in sorted(data['by_strategy'].items()):
        pct = data['by_strategy_pct'][strategy]
        print(f\"  {strategy:15} : {count:6,} ({pct:5.1f}%)\")
"
else
    echo "ERROR: Strategy analysis file not found!"
fi

echo ""
echo "========================================"
echo "Pipeline complete!"
echo "========================================"
echo ""
echo "Output files:"
echo "  - data/processed_fixed/magic8_trades_complete.csv"
echo "  - data/processed_fixed/strategy_analysis.json"
echo "  - data/processed_fixed/symbol_analysis.json"
echo "  - data/processed_fixed/data_quality_report.json"
