# Magic8 Accuracy Predictor

## Project Overview
This project predicts the accuracy (win/loss) of Magic8's 0DTE options trading systems using machine learning.

**Revamp Status**: Multi-model architecture with symbol-specific models COMPLETE! Individual XGBoost models trained for each trading symbol (SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA) plus grouped models for similar profit scales.

**Trading Symbols**: SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA  
**Strategies**: Butterfly, Iron Condor, Vertical, Sonar  
**Status**: ✅ Phase 1 Complete | ✅ Individual Models (90-94%) | ✅ Grouped Models (90%) | ✅ Threshold Optimization | ✅ API Integration

## 🎉 All Models Successfully Trained (January 2025 Update)

### Outstanding Results
- **Individual Model Accuracies**: 90-94% across all symbols
- **Grouped Model Accuracies**: SPX_SPY: 89.95%, QQQ_AAPL_TSLA: 90.13%
- **AUC Scores**: 0.96-0.98 (excellent discrimination)
- **Data Processed**: 1,076,742 trades from 620 folders
- **Threshold Optimization**: F1-optimized thresholds (0.35-0.75 range)
- **Mean F1 Score**: 0.910 across all symbol-strategy combinations

### Performance by Symbol
- **AAPL**: 94.08% accuracy (AUC: 0.987)
- **TSLA**: 94.04% accuracy (AUC: 0.987)
- **RUT**: 92.07% accuracy (AUC: 0.976)
- **SPY**: 91.48% accuracy (AUC: 0.972)
- **QQQ**: 91.02% accuracy (AUC: 0.972)
- **NDX**: 90.75% accuracy (AUC: 0.968)
- **XSP**: 90.59% accuracy (AUC: 0.968)
- **SPX**: 90.03% accuracy (AUC: 0.964)

### Grouped Models
- **SPX_SPY**: 89.95% accuracy (345,014 samples)
- **QQQ_AAPL_TSLA**: 90.13% accuracy (244,435 samples)

## 🚀 Complete Operational Flow

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

### Step 2: Process Raw Magic8 Data
```bash
# Run the complete data processor that merges all sheets
./run_data_processing_v2.sh

# This creates: data/processed_optimized_v2/magic8_trades_complete.csv
# Processing time: ~3.5 minutes for 1M+ trades
```

### Step 3: Split Data by Symbol
```bash
# Create symbol-specific CSV files
python split_data_by_symbol.py data/processed_optimized_v2/magic8_trades_complete.csv data/symbol_specific

# This creates:
# - data/symbol_specific/SPX_trades.csv
# - data/symbol_specific/SPY_trades.csv
# - ... (one file per symbol)
# - data/symbol_specific/symbol_statistics.json
```

### Step 4: Train Symbol-Specific Models
```bash
# Create minimal feature info file (models will auto-detect features)
echo '{"feature_names": []}' > data/symbol_specific/feature_info.json

# Train individual models for each symbol
python train_symbol_models.py data/symbol_specific models/individual data/symbol_specific/feature_info.json

# This creates:
# - models/individual/SPX_trades_model.pkl
# - models/individual/SPX_trades_features.pkl
# - ... (model and features for each symbol)
```

### Step 4a: Analyze Profit Scales by Strategy
```bash
python analyze_profit_scales.py \
    data/processed_optimized_v2/magic8_trades_complete.csv \
    data/profit_scale
```
Outputs `profit_scale_stats.json` and `profit_scale_groups.json` in `data/profit_scale/`.



### Step 5: Train Grouped Models
```bash
# Train grouped models for symbols with similar profit scales
python train_grouped_models.py data/symbol_specific models/grouped

# Creates:
# - models/grouped/SPX_SPY_combined_model.pkl (89.95% accuracy)
# - models/grouped/QQQ_AAPL_TSLA_combined_model.pkl (90.13% accuracy)
```
### Step 5a: Train Symbol-Strategy Models
```bash
python train_symbol_strategy_models.py data/processed_optimized_v2/magic8_trades_complete.csv models/symbol_strategy
```


### Step 6: Optimize Thresholds
```bash
# Calculate optimal decision thresholds per symbol-strategy
python optimize_thresholds.py data/symbol_specific models/individual --debug

# Creates: 
# - models/individual/thresholds.json (F1-optimized)
# - models/individual/thresholds_recall80.json (80% recall thresholds)

# For grouped models
python optimize_thresholds_grouped.py data/symbol_specific models/grouped

# Creates: models/grouped/thresholds_grouped.json
```

### Step 7: Configure API
Ensure `config/config.yaml` has all models configured:
```yaml
models:
  AAPL: models/individual/AAPL_trades_model.pkl
  TSLA: models/individual/TSLA_trades_model.pkl
  RUT: models/individual/RUT_trades_model.pkl
  SPY: models/individual/SPY_trades_model.pkl
  QQQ: models/individual/QQQ_trades_model.pkl
  NDX: models/individual/NDX_trades_model.pkl
  XSP: models/individual/XSP_trades_model.pkl
  SPX: models/individual/SPX_trades_model.pkl
  SPX_SPY: models/grouped/SPX_SPY_combined_model.pkl
  QQQ_AAPL_TSLA: models/grouped/QQQ_AAPL_TSLA_combined_model.pkl
  default: models/xgboost_phase1_model.pkl

model_routing:
  use_grouped:
    SPX: SPX_SPY
    SPY: SPX_SPY
    QQQ: QQQ_AAPL_TSLA
    AAPL: QQQ_AAPL_TSLA
    TSLA: QQQ_AAPL_TSLA
```

### Step 8: Start Prediction API
```bash
# Start the real-time prediction API with multi-model support
./run_realtime_api.sh

# Or manually:
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
python src/prediction_api_realtime.py

# API will be available at http://localhost:8000
```

## 📊 Key Results

### Symbol-Specific Profit Scales
- **Large Scale**: NDX ($2,452 avg), RUT ($503 avg)
- **Small Scale**: SPX ($9.67), SPY ($4.92), XSP ($4.39), QQQ ($3.93), AAPL ($12.79), TSLA ($12.86)

### Optimized Thresholds (Examples)
- **Butterfly strategies**: 0.45-0.55 (more conservative)
- **Iron Condor strategies**: 0.50-0.75 (more selective)
- **Mean threshold**: 0.600 (std: 0.097)
- **F1 scores**: 0.739-0.986 (mean: 0.910)

### Model Features (Auto-detected: 31 features)
Including temporal features (hour, minute, day_of_week), price data, risk/reward ratios, strike information, and strategy encodings.

### Data Statistics
- **Total trades**: 1,076,742 (with complete data)
- **Date Range**: Jan 2023 - Jun 2025 (2.5 years)
- **Strategies**: Butterfly (27.5%), Iron Condor (27.5%), Vertical (27.5%), Sonar (18.4%)

## 📈 Enhanced Multi-Model Architecture

The architecture handles symbol-specific characteristics with optimized thresholds:
- **Individual Models**: Each symbol has its own XGBoost model
- **Grouped Models**: SPX+SPY and QQQ+AAPL+TSLA for similar scales
- **Threshold Optimization**: Per-symbol-strategy thresholds using proper F1 calculation
- **Dynamic Routing**: API automatically selects appropriate model
- **Real-time Features**: Integration with market data providers

## 📁 Project Structure

```
magic8-accuracy-predictor/
├── src/
│   ├── models/
│   │   ├── xgboost_symbol_specific.py  # Symbol-specific training
│   │   └── multi_model.py              # Multi-model routing
│   ├── data_providers/                 # Market data interfaces
│   │   ├── standalone_provider.py      # Direct IBKR connection
│   │   └── companion_provider.py       # Magic8-Companion API
│   ├── feature_engineering/
│   │   └── real_time_features.py       # Feature generation
│   └── prediction_api_realtime.py      # Main API with thresholds
├── data/
│   ├── processed_optimized_v2/         # Complete merged data
│   └── symbol_specific/                # Per-symbol CSV files
├── models/
│   ├── individual/                     # Symbol-specific models
│   │   ├── *_trades_model.pkl         # 8 individual models
│   │   ├── thresholds.json             # F1-optimized thresholds
│   │   └── thresholds_recall80.json   # 80% recall thresholds
│   └── grouped/                        # Grouped models
│       ├── SPX_SPY_combined_model.pkl
│       ├── QQQ_AAPL_TSLA_combined_model.pkl
│       └── thresholds_grouped.json
├── config/
│   └── config.yaml                     # API configuration
├── process_magic8_data_optimized_v2.py # Data processor
├── split_data_by_symbol.py             # Symbol splitter
├── train_symbol_models.py              # Individual trainer
├── train_grouped_models.py             # Grouped trainer
├── optimize_thresholds.py              # Threshold optimizer
├── optimize_thresholds_grouped.py      # Grouped threshold optimizer
└── run_realtime_api.sh                 # API launcher script
```

## 🔧 Technical Details

### Complete Data Processing Pipeline
1. **Sheet Merger**: Combines profit, trades, and delta sheets by date/time/symbol
2. **Feature Extraction**: All strike details, bid/ask spreads, delta values
3. **Duplicate Detection**: Prevents duplicate trades in output
4. **Format Year Fix**: Correct year assignment from folder dates

### Symbol-Specific Models
- **Algorithm**: XGBoost with automatic feature detection
- **Parameters**: 200 rounds, early stopping, max_depth=4
- **Validation**: 80/20 train-test split with stratification
- **Features**: 31 auto-detected from raw data

### Threshold Optimization
- **F1 Score Calculation**: Uses sklearn.metrics.f1_score
- **Per-Symbol-Strategy**: Each combination has its own threshold
- **Dynamic Loading**: API loads thresholds from JSON files
- **Debug Mode**: Shows prediction distributions and F1 calculations

### Multi-Model Prediction Pipeline
```python
# Real-time prediction with dynamic thresholds
if predictor:
    proba = predictor.predict_proba(req.symbol, X)[0][1]
    
    # Get symbol-specific threshold
    threshold = 0.5  # default
    if req.symbol in predictor.models:
        sym_thresh = thresholds_individual.get(req.symbol, {})
        threshold = sym_thresh.get(req.strategy, 0.5)
    else:
        # Check grouped models
        for group_name, group_thresholds in thresholds_grouped.items():
            if req.symbol in group_name.split('_'):
                threshold = group_thresholds.get(req.symbol, {}).get(req.strategy, 0.5)
                break
    
    prediction = "WIN" if proba >= threshold else "LOSS"
```

## 🎯 API Integration

### Starting the Prediction API
```bash
# Using the shell script (recommended)
./run_realtime_api.sh

# Or manually
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
python src/prediction_api_realtime.py

# Verify API is running
curl http://localhost:8000/

# Test prediction with threshold application
curl -X POST http://localhost:8000/predict \
     -H "Content-Type: application/json" \
     -d '{"strategy": "Butterfly", "symbol": "SPX", "premium": 24.82, "predicted_price": 5855}'
```

### API Endpoints
- `GET /` - Health check and model status
- `GET /market/{symbol}` - Real-time market data
- `POST /predict` - Get prediction with dynamic threshold

### Data Source Configuration
Edit `config/config.yaml` to set your data source:
```yaml
data_source:
  primary: "companion"      # Use Magic8-Companion API
  # primary: "standalone"   # Or direct IBKR connection
  
  companion:
    base_url: "http://localhost:8765"
    
  standalone:
    ib_host: "127.0.0.1"
    ib_port: 7497
    client_id: 99
```

## 📚 Documentation

- `magic8-predictor-revamp-plan.md` - Complete revamp blueprint (98% complete)
- `REVAMP_SUMMARY.md` - Quick reference for revamp status
- `REVAMP_ACTION_ITEMS.md` - Remaining deployment tasks
- `docs/DATA_SCHEMA_COMPLETE.md` - Complete data schema after processing
- `docs/MULTI_MODEL_OVERVIEW.md` - Multi-model architecture details
- `PROJECT_KNOWLEDGE_BASE.md` - Comprehensive project details
- `IMPLEMENTATION_PLAN.md` - Full project roadmap

## ⚡ Performance Optimizations

### Recent Improvements (January 2025)
- **Dynamic Thresholds**: Per-symbol-strategy thresholds loaded from JSON
- **VIX Calculations**: Previous close and daily high/low tracking
- **Model Routing**: Automatic selection with grouped model support
- **Cache Management**: Daily data cached for performance

### Symbol-Specific Benefits
- **Profit Scale Handling**: 76x differences properly modeled
- **Feature Relevance**: Each symbol uses only relevant features
- **Threshold Optimization**: Per-symbol-strategy for maximum profit
- **Training Efficiency**: Parallel training possible

## 🐛 Common Issues & Solutions

### API Not Starting
- Check that models exist in `models/individual/` and `models/grouped/`
- Verify thresholds.json files are generated
- Ensure PYTHONPATH is set correctly

### Missing Raw Data
Ensure you have the Magic8 CSV files organized by date folders with profit, trades, and delta sheets.

### Empty data/symbol_specific Directory
Run the complete pipeline: process data → split by symbol → train models → optimize thresholds

### IBKR Connection Issues
- Ensure Gateway/TWS is running on port 7497
- Check API permissions are enabled
- Verify no other clients are using the same client ID

## 🚨 Production Deployment

### Pre-deployment Checklist
- [x] All models trained (individual + grouped)
- [x] Thresholds optimized and saved
- [x] API tested with all endpoints
- [x] Configuration updated
- [ ] IBKR Gateway configured for production
- [ ] Monitoring setup
- [ ] Backup procedures documented

### Deployment Steps
1. Set environment to production in config.yaml
2. Start IBKR Gateway (if using standalone)
3. Run API: `./run_realtime_api.sh`
4. Monitor logs in `logs/` directory
5. Validate predictions match expected thresholds

---

**Repository**: https://github.com/birddograbbit/magic8-accuracy-predictor  
**Last Updated**: January 2025  
**Model Status**: ✅ All models trained and integrated  
**API Status**: ✅ Real-time API with dynamic thresholds  
**Revamp Progress**: 98% Complete - Ready for Production  
**Next Goal**: Deploy to production and monitor performance