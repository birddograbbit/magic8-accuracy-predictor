# Magic8 Accuracy Predictor

## Project Overview
This project predicts the accuracy (win/loss) of Magic8's 0DTE options trading systems using machine learning.

**Revamp Status**: Multi-model architecture in progress with symbol specific features.

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
python -m src.models.xgboost_baseline

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

## 📈 Enhanced Evaluation Metrics

Simple accuracy alone can be misleading when each strategy has a different base
win rate. The pipeline now logs per‑strategy confusion matrices, balanced
accuracy and profit‑weighted results.

Run the full pipeline to generate these metrics:

```bash
python -m src.models.xgboost_baseline

```

The summary section reports weighted balanced accuracy, average MCC and overall
profit improvement versus a naive baseline.

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

### Starting the Prediction API with IBKR Fallback
1. Ensure IBKR Gateway/TWS is running on port **7497**.
2. Start the prediction service:
   ```bash
   # Recommended - use the startup script
   python start_prediction_api.py
   
   # Alternative - run directly from src
   cd src && python prediction_api.py
   ```
3. Verify the API is live:
   ```bash
   curl http://localhost:8000/
   ```
   The service will fetch prices from Magic8-Companion when available and fall back to IBKR directly. Data is cached for 5 minutes.

### Running the Real-Time Feature API
1. Start the new API that generates Phase‑1 features automatically:
   ```bash
   ./run_realtime_api.sh
   ```
2. Send a sample prediction request:
   ```bash
  curl -X POST http://localhost:8000/predict \
        -H "Content-Type: application/json" \
        -d '{"strategy": "Butterfly", "symbol": "SPX", "premium": 1.25, "predicted_price": 5850}'
  ```
  The response includes the market data source and number of features used.

### Running Comprehensive API Tests

#### Test Suite Overview
The comprehensive test suite validates the ML prediction API with 130+ parameterized test cases:

```bash
# Run all tests
python tests/run_comprehensive_tests.py

# Run with coverage report
python -m pytest tests/test_api_comprehensive.py -v --cov=src
```

#### Test Coverage
- **Volatility Scenarios**: 4 regimes (VIX 12-35)
  - Low (VIX=12): ~17% win probability
  - Normal (VIX=17): ~35% win probability  
  - Elevated (VIX=25): ~73% win probability
  - High (VIX=35): ~95% win probability (capped)
- **Strategies**: All 4 types (Butterfly, Iron Condor, Vertical, Sonar)
- **Symbols**: Indices (SPX) and stocks (AAPL)
- **Time Periods**: Market open, midday, close, after-hours
- **Edge Cases**: Extreme premiums ($0.10 to $50.00)

#### Recent Fixes (July 2025)
- Fixed import issues in `real_time_features.py` (relative → absolute imports)
- Updated FastAPI to use modern lifespan handlers (eliminated deprecation warnings)
- Updated Pydantic to use `model_dump()` instead of deprecated `dict()`
- Reduced test warnings from 135 to 1 (only third-party eventkit warning remains)

### Running Comprehensive API Tests
Execute the scenario-driven test suite to verify prediction behaviour:

```bash
python tests/run_comprehensive_tests.py
```

This runs over 100 parameterized cases spanning volatility regimes,
market sessions, strategies and symbols to ensure the API remains robust.

### Simplified IBKR Connection
All components now share a single IBKR connection managed by `IBConnectionManager`.
This singleton ensures only one active `IB` instance is used across the project.
Providers call `IBConnectionManager.instance().get_ib()` to reuse the connection.

   **Note**: If you don't have market data subscriptions for certain symbols (e.g., NDX), the system will automatically use mock data for those symbols and continue operating normally.

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
- `docs/IBKR_INDEX_FIX.md` - IBKR index contract configuration
- `docs/MARKET_DATA_SUBSCRIPTIONS.md` - Handling market data subscription errors

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

### Market Data Subscription Errors
If you see "Error 354: Requested market data is not subscribed" for symbols like NDX:
- The system will automatically use mock data for those symbols
- No manual configuration needed
- See `docs/MARKET_DATA_SUBSCRIPTIONS.md` for details

---

**Repository**: https://github.com/birddograbbit/magic8-accuracy-predictor  
**Last Updated**: July 4, 2025  
**Phase 1 Status**: ✅ Complete - 88.21% accuracy achieved!  
**Test Suite**: ✅ 130 parameterized tests passing  
**Next Goal**: Real-time prediction system

