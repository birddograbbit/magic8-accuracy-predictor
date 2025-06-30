# Magic8 Accuracy Predictor

## Project Overview
This project predicts the accuracy (win/loss) of Magic8's 0DTE options trading systems. We use a phased approach, starting with a simple MVP using readily available data.

**Trading Symbols**: SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA  
**Strategies**: Butterfly, Iron Condor, Vertical, Sonar  
**Status**: Feature engineering optimized with 100x performance improvement!

## 🎉 Major Performance Breakthrough (June 30, 2025 - Latest)

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

### Step 3: Run Optimized ML Pipeline
```bash
# Feature engineering - now runs in 2-5 minutes!
python src/phase1_data_preparation.py

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
5. **Trade** (10): premium, risk, reward, ratios

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

## 📊 Next Steps

1. **Download IBKR data** for remaining 7 symbols
2. **Run optimized pipeline** (2-5 minutes)
3. **Train XGBoost model** (<5 minutes)
4. **Analyze results** by strategy and time
5. **Plan Phase 2** based on feature importance

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
**Last Updated**: June 30, 2025 (4:30 PM - 100x Performance Improvement)  
**Key Achievement**: Feature engineering reduced from 3+ hours to 2-5 minutes!