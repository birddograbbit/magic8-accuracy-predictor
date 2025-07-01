# Magic8 Accuracy Predictor

## Project Overview
This project predicts the accuracy (win/loss) of Magic8's 0DTE options trading systems using machine learning. 

**Trading Symbols**: SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA  
**Strategies**: Butterfly, Iron Condor, Vertical, Sonar  
**Status**: ✅ Phase 1 Complete - 88.21% Test Accuracy Achieved!

## 🎉 Phase 1 Successfully Completed (July 1, 2025)

### Outstanding Results
- **Test Accuracy**: 88.21% (target was >60%)
- **AUC-ROC**: 0.9497 (excellent discrimination)
- **Training Time**: 2 minutes 29 seconds
- **Feature Engineering**: 2-5 minutes (was 3+ hours)
- **Data Processing**: 0.6 minutes for 1.5M trades

### Performance by Strategy
- **Iron Condor**: 96.24% accuracy (best performer)
- **Vertical**: 91.92% accuracy
- **Sonar**: 88.70% accuracy  
- **Butterfly**: 75.98% accuracy (most challenging)

## 🚀 Quick Start Guide

### Step 1: Setup Environment
```bash
git clone https://github.com/birddograbbit/magic8-accuracy-predictor.git
cd magic8-accuracy-predictor

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Process Trade Data
```bash
# Run the optimized processor (0.6 minutes for 1.5M trades)
python process_magic8_data_optimized_v2.py

# Copy to expected location
cp data/processed_optimized_v2/magic8_trades_complete.csv data/normalized/normalized_aggregated.csv
```

### Step 3: Download Market Data (if needed)
```bash
# Download IBKR historical data for all symbols
./download_phase1_data.sh

# Or download individually
python ibkr_downloader.py --symbols "STOCK:SPY" --bar_sizes "5 mins" --duration "5 Y"
```

### Step 4: Run ML Pipeline
```bash
# Feature engineering (2-5 minutes)
python src/phase1_data_preparation.py

# Train XGBoost model (2-3 minutes)
python src/models/xgboost_baseline.py

# This training command automatically saves a wrapped model for the
# real-time predictor at `models/phase1/xgboost_model.pkl` (and a copy
# at `models/xgboost_phase1_model.pkl`).
```

### Step 5: Make Predictions (Next Phase)
```bash
# Example prediction script (to be implemented)
python predict_trades_example.py
```

## 📊 Key Results

### Model Performance
- **Training Accuracy**: 85.86%
- **Validation Accuracy**: 85.72%  
- **Test Accuracy**: 88.21%
- **F1 Score**: 0.8496
- **AUC-ROC**: 0.9497

### Top Feature Importance
1. `pred_price` (9726.73) - Predicted price from Magic8
2. `strategy_Butterfly` (1747.91) - Strategy indicator
3. `pred_difference` (943.14) - Price prediction error
4. `prof_premium` (643.03) - Trade premium
5. `strategy_Iron Condor` (418.84) - Strategy indicator

### Data Statistics
- **Total trades**: 1,085,312 (with valid profit data)
- **Win Rate**: 54.30% (realistic for trading system)
- **Date Range**: Jan 2023 - Jun 2025 (2.5 years)
- **Training samples**: 916,682

## 📁 Project Structure

```
magic8-accuracy-predictor/
├── src/
│   ├── phase1_data_preparation.py    # Feature engineering pipeline
│   ├── models/
│   │   └── xgboost_baseline.py      # XGBoost model
│   └── evaluation/                  # Performance analysis
├── data/
│   ├── source/                      # Original CSV files
│   ├── normalized/                  # Processed trade data
│   ├── ibkr/                       # Market data (5-min bars)
│   └── phase1_processed/           # ML-ready features
├── models/
│   └── phase1/                     # Saved trained models
├── process_magic8_data_optimized_v2.py  # Data processor
├── run_data_processing_v2.sh           # Processing runner
└── download_phase1_data.sh            # IBKR data helper
```

## 🔧 Technical Details

### Data Processing Pipeline
1. **CSV Parser**: Handles multiple profit column formats (Profit, Raw, Managed)
2. **Strategy Extraction**: Parses from 'Name' column correctly
3. **Batch Processing**: 5K record chunks for memory efficiency
4. **Win/Loss Logic**: Profit > 0 = Win (1), Profit ≤ 0 = Loss (0)

### Feature Engineering (74 features)
- **Temporal** (9): Hour, minute, day of week, cyclical encodings
- **Price Features** (~40): Close, SMA, momentum, volatility, RSI for each symbol
- **VIX Features** (8): Level, SMA, changes, regime  
- **Strategy** (4): One-hot encoded
- **Trade Features** (10): Premium, risk/reward, predicted prices

### Model Architecture
- **Algorithm**: XGBoost with GPU support
- **Parameters**: 1000 estimators, 0.1 learning rate, 6 max depth
- **Class Balancing**: scale_pos_weight for imbalanced data
- **Validation**: Temporal split (60/20/20) for realistic backtesting

## 🎯 Next Steps: Real-Time Predictions

### Phase 2: Production System
1. **Real-Time Feature Engineering**
   - Connect to IBKR API for live market data
   - Calculate technical indicators in real-time
   - Match exact features from training
     (`is_market_open`, `<SYMBOL>_close`, `vix_vix_change`, etc.)

2. **Prediction Pipeline**
   ```python
   # Pseudo-code for real-time predictions
   for order in magic8_orders:
       features = generate_features(order, current_market_data)
       probability = model.predict_proba(features)
       if probability > threshold:
           execute_trade(order)
   ```

3. **Integration Components**
 - WebSocket connection to Magic8
  - IBKR API for market data
  - Redis for feature caching
  - REST API for predictions

### Enabling Magic8-Companion Data API
1. In the `Magic8-Companion` repository add the FastAPI endpoints:
   ```bash
   cd /path/to/Magic8-Companion
   python ../magic8-accuracy-predictor/setup_companion_api.py
   ```
2. Start the companion with the API enabled:
   ```bash
   export M8C_ENABLE_DATA_API=true
   python -m magic8_companion
   ```
3. Verify the API is running:
   ```bash
   curl http://localhost:8765/health
   ```

4. **Monitoring & Feedback**
   - Track prediction accuracy
   - Store predictions vs outcomes
   - Periodic model retraining

## 📚 Documentation

- `PROJECT_KNOWLEDGE_BASE.md` - Comprehensive project details
- `IMPLEMENTATION_PLAN.md` - Full project roadmap
- `PHASE1_SUMMARY.md` - Phase 1 implementation details
- `REALTIME_INTEGRATION_GUIDE.md` - Production system guide
- `CLEANUP_PLAN.md` - Codebase organization

## ⚡ Performance Optimizations

### 100x Feature Engineering Speedup
- **Problem**: O(n×m) time complexity with apply/lambda
- **Solution**: `pd.merge_asof()` for O(n log m) complexity
- **Result**: 3+ hours → 2-5 minutes

### Batch Processing
- **Problem**: Memory overflow with 1.5M records
- **Solution**: Process in 5K record chunks
- **Result**: Stable memory usage, 150x speedup

## 🐛 Common Issues & Solutions

### ImportError with required packages
```bash
pip install -r requirements.txt --upgrade
```

### Memory errors during processing
The optimized scripts handle this automatically with batch processing.

### Missing IBKR data
Run `./download_phase1_data.sh` to get all required market data.

---

**Repository**: https://github.com/birddograbbit/magic8-accuracy-predictor  
**Last Updated**: July 1, 2025  
**Phase 1 Status**: ✅ Complete - 88.21% accuracy achieved!  
**Next Goal**: Real-time prediction system
