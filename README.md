# Magic8 Accuracy Predictor

## Project Overview
This project predicts the accuracy (win/loss) of Magic8's 0DTE options trading systems. We use a phased approach, starting with a simple MVP using readily available data.

**Trading Symbols**: SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA  
**Strategies**: Butterfly, Iron Condor, Vertical, Sonar  
**Status**: Feature engineering optimized with 100x performance improvement!

## 🎉 Major Performance Breakthrough (June 30, 2025)

### 100x Faster Feature Engineering!
The `phase1_data_preparation.py` script has been optimized from **3+ hours to 2-5 minutes**:

**Problem**: Used inefficient apply/lambda for time-series merging (~537 billion comparisons)  
**Solution**: Replaced with `pd.merge_asof()` for efficient time-based joins  
**Result**: 100x+ performance improvement while maintaining accuracy

## 🚀 Quick Start (Updated)

### Step 1: Setup Environment
```bash
git clone https://github.com/birddograbbit/magic8-accuracy-predictor.git
cd magic8-accuracy-predictor

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Process Trade Data
```bash
# Run the optimized processor
python process_magic8_data_optimized_v2.py

# Copy to expected location
cp data/processed_optimized_v2/magic8_trades_complete.csv data/normalized/normalized_aggregated.csv
```

The processor automatically detects the available profit column. If your CSVs
don't have a `Profit` column (December 2023 onward) it will fall back to
`Raw` or `Managed`.

### Step 3: Run Optimized ML Pipeline
```bash
# Feature engineering - now runs in 2-5 minutes!
python src/phase1_data_preparation.py  # includes profit validation

# Train model
python src/models/xgboost_baseline.py
```

## 📊 Performance Improvements

### Data Processing
- **Before**: 2+ hours, memory issues
- **After**: 0.6 minutes for 1.5M records
- **Method**: Batch processing with 5K chunks

### Feature Engineering
- **Before**: 3+ hours (often never completed)
- **After**: 2-5 minutes
- **Method**: Using `pd.merge_asof()` instead of apply/lambda

## 📈 Data Statistics

**Total trades processed**: 1,527,804

**By Strategy**:
- Butterfly: 406,631 (26.62%)
- Iron Condor: 406,631 (26.62%)
- Vertical: 406,631 (26.62%)
- Sonar: 307,911 (20.15%)

**By Symbol**: All 8 symbols have good coverage (see PROJECT_KNOWLEDGE_BASE.md for details)

## 🎯 Phase 1 Goals & Features

### Target Metrics
- **Accuracy**: > 60% (baseline 50%)
- **Features**: ~70 engineered features
- **Feature Engineering Time**: 2-5 minutes (was 3+ hours)
- **Model Training Time**: < 5 minutes

### Feature Categories
1. **Temporal** (9): hour, minute, day_of_week, market indicators
2. **Price-Based** (~40): close, SMA, momentum, volatility, RSI per symbol
3. **VIX** (7): level, SMA, change, regime
4. **Strategy** (4): one-hot encoded
5. **Trade** (8): premium_normalized and risk_reward_ratio (raw risk/reward columns removed)

## 📁 Key Scripts

### Data Processing
- `process_magic8_data_optimized_v2.py` - Fast batch processor
- `run_data_processing_v2.sh` - Runner script

### ML Pipeline (Optimized)
- `src/phase1_data_preparation.py` - Feature engineering with merge_asof
- `src/models/xgboost_baseline.py` - Model training

### Utilities
- `test_strategy_parsing.py` - Test strategy extraction
- `analyze_existing_data.py` - Data analysis

## ⚡ Technical Optimizations

### 1. Time-Series Merging
```python
# Old (slow) approach - O(n×m)
df['feature'] = df['datetime'].apply(lambda x: self._get_nearest_value(price_df, x, col))

# New (fast) approach - O(n log m)
merged = pd.merge_asof(
    symbol_data.sort_values('interval_datetime'),
    price_features.sort_index(),
    left_on='interval_datetime',
    right_index=True,
    direction='nearest',
    tolerance=pd.Timedelta('10min')
)
```

### 2. Pre-calculated Indicators
Technical indicators (SMA, RSI, etc.) are now calculated once during data loading, not during feature merging.

### 3. Progress Tracking
Added time logging for each operation to identify bottlenecks.

## ✅ Phase 1 Results (July 1, 2025)

The optimized pipeline completed successfully with the following metrics:

- **Test Accuracy**: 0.8821
- **Test F1**: 0.8496
- **Test AUC ROC**: 0.9497

**Performance by Strategy**

- Butterfly: 75.98% accuracy
- Iron Condor: 96.24% accuracy
- Sonar: 88.70% accuracy
- Vertical: 91.92% accuracy

## 📊 Next Steps

1. Finalize real-time architecture for Phase&nbsp;2
2. Explore feature importance to guide new features
3. Experiment with ensemble models

## 📚 Documentation

- `PROJECT_KNOWLEDGE_BASE.md` - Comprehensive project details
- `PHASE1_PLAN.md` - Detailed implementation plan
- `PHASE1_SUMMARY.md` - Phase 1 progress with optimization details
- `IMPLEMENTATION_PLAN.md` - Full project roadmap

## ⚠️ Common Issues & Solutions

### Script taking hours to run
**Cause**: Using old version without merge_asof optimization  
**Solution**: Use the latest `src/phase1_data_preparation.py`

### Memory errors
**Cause**: Processing too much data at once  
**Solution**: The optimized version processes data in chunks

### Missing price data
**Cause**: IBKR data not downloaded for all symbols  
**Solution**: Run `./download_phase1_data.sh` for remaining symbols

---

**Repository**: https://github.com/birddograbbit/magic8-accuracy-predictor  
**Last Updated**: July 1, 2025 - Phase 1 complete  
**Key Achievement**: Feature engineering reduced from 3+ hours to 2-5 minutes!