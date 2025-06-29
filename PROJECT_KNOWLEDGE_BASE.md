# Magic8 Accuracy Predictor - Project Knowledge Base

## Project Overview

The Magic8 Accuracy Predictor is a machine learning system designed to predict the win/loss outcomes of Magic8's 0DTE (zero days to expiration) options trading system. The project uses a phased approach, starting with a simple MVP using readily available data and gradually adding complexity.

**Repository**: https://github.com/birddograbbit/magic8-accuracy-predictor

**Trading Symbols**: SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA  
**Strategies**: Butterfly (debit), Iron Condor (credit), Vertical Spreads (credit)

## Current Status (As of June 29, 2025)

### Phase 1: MVP Implementation - 100% Complete ✅

**Completed**:
- ✅ Core Python implementation files
- ✅ Data preparation pipeline with correct target variable (prof_raw)
- ✅ XGBoost baseline model
- ✅ All IBKR data downloaded (9 symbols)
- ✅ Data processing with proper win/loss labels
- ✅ Fixed all technical issues (categorical columns, JSON serialization)

**Key Achievement**: Successfully identified and fixed the target variable issue. Now using `prof_raw` (Raw P/L at expiration) instead of `trad_profited`, increasing usable data from 301 to 30,649 records.

## Data Sources and Results

### 1. Normalized Trade Data ✅
- **Location**: `data/normalized/normalized_aggregated.csv`
- **Total Records**: 47,632
- **Records with Raw P/L**: 30,649 (64.3%)
- **Overall Win Rate**: 33.38%
- **Target Column**: `prof_raw` (Raw profit/loss at expiration)

### 2. IBKR Historical Data ✅
All symbols downloaded with 5-minute bars:
- SPX, SPY, XSP, NDX, QQQ, RUT, AAPL, TSLA (all ~59,220 records)
- VIX (123,170 records)

### 3. Processed Data ✅
- **Location**: `data/phase1_processed/`
- **Features**: 35 engineered features
- **Train**: 28,579 samples (21.3% wins)
- **Validation**: 9,526 samples (53.3% wins)
- **Test**: 9,527 samples (49.8% wins)

## Important Technical Details

### Target Variable
- **Column Used**: `prof_raw` - Raw P/L at expiration
- **Win Definition**: prof_raw > 0
- **Loss Definition**: prof_raw <= 0
- **Rationale**: Raw P/L represents pure trade quality without manual intervention

### Feature Categories (35 total)
1. **Temporal Features** (9): hour, minute, day_of_week, cyclical encodings, market indicators
2. **Price Features** (~6 per symbol): close, SMA, momentum, volatility, RSI, price position
3. **VIX Features** (7): level, SMA, change, regime indicators
4. **Strategy Features** (3): One-hot encoded (Butterfly, Iron_Condor, Vertical)
5. **Trade Features** (10): premium, risk, reward, probability, normalized metrics

### Class Distribution Analysis
The temporal split shows interesting patterns:
- **Training data** (older): 21.3% win rate
- **Validation/Test** (newer): ~50% win rate

This suggests the trading strategy improved significantly over time.

## Key Fixes Applied

1. **Target Variable**: Changed from `trad_profited` (301 records) to `prof_raw` (30,649 records)
2. **Categorical Columns**: Properly dropped after one-hot encoding
3. **JSON Serialization**: Fixed numpy type conversion issues
4. **Timezone Handling**: IBKR UTC → Eastern Time conversion

## Project Structure
```
magic8-accuracy-predictor/
├── data/
│   ├── normalized/          # Original trade data
│   ├── ibkr/               # Historical price data
│   └── phase1_processed/   # Clean processed data
├── src/
│   ├── phase1_data_preparation.py  # Main data pipeline
│   └── models/
│       └── xgboost_baseline.py     # Baseline model
├── models/                 # Saved models and results
├── plots/                  # Visualizations
└── logs/                   # Processing logs
```

## Next Steps

### Immediate (Phase 1 Completion)
1. Run XGBoost model with corrected data
2. Analyze feature importance
3. Evaluate performance by strategy
4. Optimize threshold for precision/recall balance

### Phase 2 (If >60% accuracy achieved)
1. Add cross-asset correlations
2. Market microstructure features
3. Advanced technical indicators
4. Ensemble methods or neural networks

### Phase 3 (Production)
1. Real-time prediction system
2. API deployment
3. Performance monitoring
4. Strategy-specific models

## Key Scripts

### Data Processing
```bash
python rebuild_data.py              # Complete rebuild with validation
python inspect_profit_columns.py    # Analyze profit columns
python diagnose_class_imbalance.py  # Temporal analysis
```

### Model Training
```bash
python src/models/xgboost_baseline.py  # Train and evaluate
```

### Verification
```bash
python verify_data.py     # Quick data check
python diagnose_features.py  # Feature analysis
```

## Success Metrics

### Phase 1 Targets
- **Accuracy**: >60% (vs 33.38% baseline)
- **Balanced metrics**: Good precision AND recall
- **Consistent performance**: Across all strategies
- **Interpretability**: Clear feature importance

### Current Baseline
- **Always predict loss**: 66.62% accuracy (but 0% recall)
- **Random prediction**: ~50% accuracy
- **Our target**: Significantly beat both baselines

## Important Insights

1. **Raw vs Managed P/L**: We use Raw P/L as it represents pure trade quality without external influence
2. **Temporal Performance Shift**: Win rate improved from ~21% to ~50% over time
3. **Data Coverage**: Only 64.3% of trades have Raw P/L data
4. **Strategy Distribution**: Mostly Butterfly trades, some Iron Condors, few Verticals

---

**Last Updated**: June 29, 2025, 6:00 PM  
**Phase 1 Status**: Complete - Ready for model evaluation  
**Next Action**: Run `python src/models/xgboost_baseline.py`
