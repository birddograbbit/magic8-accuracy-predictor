# Magic8 Accuracy Predictor

## Project Overview
This project predicts the accuracy (win/loss) of Magic8's 0DTE options trading systems. We use a phased approach, starting with a simple MVP using readily available data.

**Trading Symbols**: SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA  
**Strategies**: Butterfly, Iron Condor, Vertical, Sonar  
**Status**: Data processing complete, ML pipeline ready to run

## 🚀 Quick Start (Updated June 30, 2025)

### Step 1: Setup Environment
```bash
git clone https://github.com/birddograbbit/magic8-accuracy-predictor.git
cd magic8-accuracy-predictor

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Process Trade Data (✅ Complete)
```bash
# Use the optimized processor (1.5M trades in 0.6 minutes)
python process_magic8_data_optimized_v2.py

# Copy to expected location
cp data/processed_optimized_v2/magic8_trades_complete.csv data/normalized/normalized_aggregated.csv
```

### Step 3: Download IBKR Data (Partial)
```bash
# Ensure IBKR TWS/Gateway is running on port 7497
# We have SPX and VIX, need 7 more symbols
./download_phase1_data.sh
```

### Step 4: Run ML Pipeline
```bash
# IMPORTANT: Use the fixed version that handles column mapping
cp src/phase1_data_preparation_fixed.py src/phase1_data_preparation.py

# Process features
python src/phase1_data_preparation.py

# Train model
python src/models/xgboost_baseline.py
```

## 📊 Current Data Statistics

### Trade Data (✅ Processed)
- **Total Trades**: 1,527,804
- **Strategies**: 
  - Butterfly: 26.62%
  - Iron Condor: 26.62%
  - Vertical: 26.62%
  - Sonar: 20.15%
- **Processing Time**: 0.6 minutes

### IBKR Data Status
- ✅ Downloaded: SPX, VIX
- ❌ Need: SPY, RUT, NDX, QQQ, XSP, AAPL, TSLA

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

## 📁 Project Structure (Cleaned)

```
magic8-accuracy-predictor/
├── data/
│   ├── source/                    # Original CSV files
│   ├── processed_optimized_v2/    # Processed trade data
│   ├── normalized/                # Expected ML input location
│   ├── ibkr/                     # Market data
│   └── phase1_processed/         # ML features (created by pipeline)
├── src/
│   ├── phase1_data_preparation_fixed.py  # Use this version!
│   └── models/
│       └── xgboost_baseline.py
├── process_magic8_data_optimized_v2.py   # Data processor
├── run_data_processing_v2.sh             # Alternative runner
└── download_phase1_data.sh               # IBKR helper
```

## ⚠️ Important Notes

### Use Correct Versions
- **Data Processor**: `process_magic8_data_optimized_v2.py` (NOT older versions)
- **ML Pipeline**: `phase1_data_preparation_fixed.py` (handles column mapping)
- **Data Location**: Always copy to `data/normalized/normalized_aggregated.csv`

### Common Issues Fixed
1. **Column Mismatch**: Fixed script maps 'timestamp' → 'interval_datetime'
2. **Missing Sonar**: Now parsing strategy from correct column
3. **Memory Issues**: Batch processing prevents crashes

## 📈 Implementation Status

### ✅ Phase 1: MVP (75% Complete)
- ✅ Data processing pipeline
- ✅ All 4 strategies identified
- ✅ Column mapping fixed
- ⏳ ML model training (ready to run)
- ⏳ Feature importance analysis

### 📅 Phase 2: Enhancements (After Phase 1)
- Cross-asset correlations
- Market microstructure
- Advanced models (ensemble, neural nets)

### 📅 Phase 3: Production
- Real-time predictions
- API deployment
- Performance monitoring

## 🔧 Troubleshooting

### If phase1_data_preparation.py fails:
```bash
# You're using the wrong version! Use:
cp src/phase1_data_preparation_fixed.py src/phase1_data_preparation.py
```

### If data processing is slow:
```bash
# You're using old processor! Use:
python process_magic8_data_optimized_v2.py
```

### If strategies are missing:
```bash
# Check you're using v2 processor which parses 'Name' column correctly
```

## 📊 Next Steps

1. **Complete IBKR downloads** for remaining 7 symbols
2. **Run ML pipeline** with fixed scripts
3. **Analyze results** - feature importance, performance by strategy
4. **Clean up** old files per CLEANUP_PLAN.md
5. **Plan Phase 2** based on Phase 1 learnings

## 📚 Documentation

- `PROJECT_KNOWLEDGE_BASE.md` - Comprehensive project details
- `CLEANUP_PLAN.md` - File cleanup instructions
- `PHASE1_SUMMARY.md` - Phase 1 progress and plans
- `PROJECT_SUMMARY_NEXT_CHAT.md` - Quick status for continuity

---

**Repository**: https://github.com/birddograbbit/magic8-accuracy-predictor  
**Last Updated**: June 30, 2025  
**Contact**: Check repository for issues/discussions