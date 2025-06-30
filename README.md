# Magic8 Accuracy Predictor

## Project Overview
This project predicts the accuracy (win/loss) of Magic8's 0DTE options trading systems. We use a phased approach, starting with a simple MVP using readily available data.

**Trading Symbols**: SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA  
**Strategies**: Butterfly, Iron Condor, Vertical, Sonar  
**Status**: Data processing pipeline fixed (June 30, 2025 evening update)

## 🚨 Important Update (June 30, 2025 - Evening)

### Fixed: CSV Processing Issues
The data processing was failing due to **summary statistics appended to the end of CSV files**. These rows don't contain trading data and were causing timestamp parsing errors.

**Solution**: The updated `process_magic8_complete.py` now:
- Removes rows with invalid dates (summary stats)
- Handles the proper date format (`MM-DD-YYYY`)
- Validates all data before processing
- Provides detailed logging of what's being cleaned

## 🚀 Quick Start (Updated)

### Step 1: Setup Environment
```bash
git clone https://github.com/birddograbbit/magic8-accuracy-predictor.git
cd magic8-accuracy-predictor

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Process Trade Data (Use Fixed Version)
```bash
# Run the FIXED processor that handles summary stats
python process_magic8_complete.py

# This will create:
# - data/normalized/normalized_complete.csv
# - data/normalized/processing_stats.json
```

### Step 3: Test the Fix (Optional)
```bash
# Test on a single problematic file
python test_processing_fix.py

# Check for issues in your CSV files
python check_duplicate_headers.py
python diagnose_csv_structure.py
```

### Step 4: Run ML Pipeline
```bash
# Update pipeline to use new data file
sed -i '' 's/normalized_aggregated.csv/normalized_complete.csv/g' src/phase1_data_preparation.py

# Process features
python src/phase1_data_preparation.py

# Train model
python src/models/xgboost_baseline.py
```

## 📊 Data Quality Issues Fixed

### Problem: Summary Statistics in CSV Files
Many CSV files have summary rows appended at the end:
```
# Normal trading data:
01-24-2023,09:35,SPX,4000.48,Butterfly,...

# Summary stats at end (causing errors):
Butterfly,100
Butterfly Expired,50
Butterfly Failed,50
Butterfly Accuracy,50%
...
```

### Solution Applied
- Validates date format (`MM-DD-YYYY`) for each row
- Removes any row without a valid date
- Provides detailed logging of cleaning process
- Preserves all valid trading data

## 📈 Expected Results

After running the fixed pipeline:
- **Total trades**: ~1.5M (varies based on cleaning)
- **Realistic win rates**: 50-70% range
- **Accurate profit tracking**: Uses correct profit columns
- **All strategies included**: Butterfly, Iron Condor, Vertical, Sonar

## 🎯 Phase 1 Goals & Features

### Target Metrics
- **Accuracy**: > 60% (baseline 50%)
- **Features**: ~70 engineered features
- **Training Time**: < 5 minutes

### Feature Categories
1. **Temporal** (9): hour, minute, day_of_week, market indicators
2. **Price-Based** (~40): close, SMA, momentum, volatility, RSI per symbol
3. **VIX** (7): level, SMA, change, regime
4. **Strategy** (4): one-hot encoded
5. **Trade** (10): premium, risk, reward, ratios

## 📁 Key Scripts

### Data Processing
- `process_magic8_complete.py` - Main processor (use this!)
- `test_processing_fix.py` - Test the fix
- `diagnose_csv_structure.py` - Diagnose CSV issues
- `check_duplicate_headers.py` - Find problematic rows

### ML Pipeline
- `src/phase1_data_preparation.py` - Feature engineering
- `src/models/xgboost_baseline.py` - Model training

## ⚠️ Common Issues & Solutions

### "time data 'YYYY-MM-DD NDX' doesn't match format"
**Cause**: Summary statistics at end of CSV files  
**Solution**: Use `process_magic8_complete.py` which removes these rows

### Many rows being dropped
**Cause**: Invalid data in summary sections  
**Solution**: This is expected - only valid trading rows are kept

### Missing strategies
**Cause**: Using old data processor  
**Solution**: Use the complete processor which handles all formats

## 📊 Next Steps

1. **Run fixed processor** on all data
2. **Download IBKR data** for remaining symbols
3. **Train ML model** with clean data
4. **Analyze results** by strategy and time period
5. **Optimize** underperforming strategies

## 📚 Documentation

- `PROJECT_KNOWLEDGE_BASE.md` - Comprehensive project details
- `PHASE1_PLAN.md` - Detailed implementation plan
- `PHASE1_SUMMARY.md` - Phase 1 progress
- `IMPLEMENTATION_PLAN.md` - Full project roadmap

---

**Repository**: https://github.com/birddograbbit/magic8-accuracy-predictor  
**Last Updated**: June 30, 2025 (Evening - Fixed CSV processing)  
**Key Fix**: Handles summary statistics in CSV files correctly