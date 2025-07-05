# Magic8 Accuracy Predictor

## Project Overview
This project predicts the accuracy (win/loss) of Magic8's 0DTE options trading systems using machine learning.

**Revamp Status**: Multi-model architecture with symbol-specific models COMPLETE! Individual XGBoost models trained for each trading symbol (SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA) to capture unique market dynamics and handle 76x profit scale differences.

**Trading Symbols**: SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA  
**Strategies**: Butterfly, Iron Condor, Vertical, Sonar  
**Status**: ✅ Phase 1 Complete | ✅ Symbol-Specific Models Trained (90-94% accuracy)

## 🎉 Symbol-Specific Models Successfully Trained (July 5, 2025)

### Outstanding Results
- **Individual Model Accuracies**: 90-94% across all symbols
- **AUC Scores**: 0.96-0.98 (excellent discrimination)
- **Data Processed**: 1,076,742 trades from 620 folders
- **Complete Data Schema**: Profit, trades, and delta sheets merged
- **76x Profit Scale**: Properly handled (NDX $2,452 vs XSP $4.39)

### Performance by Symbol
- **AAPL**: 94.08% accuracy (AUC: 0.987)
- **TSLA**: 94.04% accuracy (AUC: 0.987)
- **RUT**: 92.07% accuracy (AUC: 0.976)
- **SPY**: 91.48% accuracy (AUC: 0.972)
- **QQQ**: 91.02% accuracy (AUC: 0.972)
- **NDX**: 90.75% accuracy (AUC: 0.968)
- **XSP**: 90.59% accuracy (AUC: 0.968)
- **SPX**: 90.03% accuracy (AUC: 0.964)

## 🚀 Complete Operational Flow (NEW)

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

### Step 5: Train Grouped Models (Optional)
```bash
# Train grouped models for symbols with similar profit scales
python train_grouped_models.py data/symbol_specific models/grouped

# Default groups:
# - SPX_SPY: Medium scale symbols
# - QQQ_AAPL_TSLA: Small scale symbols
```

### Step 6: Optimize Thresholds
```bash
# Calculate optimal decision thresholds per symbol-strategy
python optimize_thresholds.py data/symbol_specific models/individual

# Creates: models/individual/thresholds.json
# with thresholds like SPX-Butterfly: 0.45, SPX-IronCondor: 0.55, etc.
```

## 📊 Key Results

### Symbol-Specific Profit Scales
- **Large Scale**: NDX ($2,452 avg), RUT ($503 avg)
- **Small Scale**: SPX ($9.67), SPY ($4.92), XSP ($4.39), QQQ ($3.93), AAPL ($12.79), TSLA ($12.86)

### Model Features (Auto-detected: 31 features)
Including temporal features (hour, minute, day_of_week), price data, risk/reward ratios, strike information, and strategy encodings.

### Data Statistics
- **Total trades**: 1,076,742 (with complete data)
- **Date Range**: Jan 2023 - Jun 2025 (2.5 years)
- **Strategies**: Butterfly (27.5%), Iron Condor (27.5%), Vertical (27.5%), Sonar (18.4%)

## 📈 Enhanced Multi-Model Architecture

The new architecture handles symbol-specific characteristics:
- **Individual Models**: Each symbol has its own XGBoost model
- **Grouped Models**: Symbols with similar profit scales can share models
- **Threshold Optimization**: Per-symbol-strategy thresholds for optimal decisions
- **Scale Normalization**: Proper handling of 76x profit differences

## 📁 Project Structure

```
magic8-accuracy-predictor/
├── src/
│   ├── models/
│   │   ├── xgboost_symbol_specific.py  # Symbol-specific training
│   │   └── multi_model_predictor.py    # Multi-model routing
│   └── prediction_api.py               # API with model selection
├── data/
│   ├── processed_optimized_v2/         # Complete merged data
│   └── symbol_specific/                # Per-symbol CSV files
├── models/
│   ├── individual/                     # Symbol-specific models
│   └── grouped/                        # Grouped models
├── process_magic8_data_optimized_v2.py # Data processor
├── split_data_by_symbol.py             # Symbol splitter
├── train_symbol_models.py              # Individual trainer
├── train_grouped_models.py             # Grouped trainer
└── optimize_thresholds.py              # Threshold optimizer
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

### Multi-Model Prediction Pipeline
```python
# Pseudo-code for symbol-aware predictions
model_strategy = SymbolModelStrategy(config)
predictor = MultiModelPredictor(model_strategy)

for order in magic8_orders:
    model = predictor.get_model(order.symbol)
    threshold = thresholds[order.symbol][order.strategy]
    probability = model.predict_proba(features)
    
    if probability > threshold:
        execute_trade(order)
```

## 🎯 Next Steps: Integration & Production

### 1. Complete Integration Testing
- Test multi-model prediction pipeline
- Validate API routing to correct models
- Measure profit improvements with optimized thresholds

### 2. Performance Comparison
- Individual vs grouped models
- Measure actual profit improvements
- Validate 76x scale handling

### 3. Production Deployment
- Real-time feature generation
- Load balancing across models
- Performance monitoring dashboard

### API Integration

#### Starting the Prediction API
```bash
# Start with multi-model support
python src/prediction_api.py

# Verify API
curl http://localhost:8000/

# Test prediction
curl -X POST http://localhost:8000/predict \
     -H "Content-Type: application/json" \
     -d '{"strategy": "Butterfly", "symbol": "SPX", "premium": 24.82, "predicted_price": 5855}'
```

## 📚 Documentation

- `magic8-predictor-revamp-plan.md` - Complete revamp blueprint
- `REVAMP_SUMMARY.md` - Quick reference for revamp status
- `docs/DATA_SCHEMA_COMPLETE.md` - Complete data schema after processing
- `PROJECT_KNOWLEDGE_BASE.md` - Comprehensive project details
- `IMPLEMENTATION_PLAN.md` - Full project roadmap

## ⚡ Performance Optimizations

### Symbol-Specific Benefits
- **Profit Scale Handling**: 76x differences properly modeled
- **Feature Relevance**: Each symbol uses only relevant features
- **Threshold Optimization**: Per-symbol-strategy for maximum profit
- **Training Efficiency**: Parallel training possible

## 🐛 Common Issues & Solutions

### Missing Raw Data
Ensure you have the Magic8 CSV files organized by date folders with profit, trades, and delta sheets.

### Empty data/symbol_specific Directory
Run the complete pipeline: process data → split by symbol → train models

### Feature Mismatch
Use the minimal feature_info.json to let models auto-detect features from your data.

---

**Repository**: https://github.com/birddograbbit/magic8-accuracy-predictor  
**Last Updated**: July 5, 2025  
**Symbol Models Status**: ✅ Complete - 90-94% accuracy achieved!  
**Revamp Progress**: ~90% Complete  
**Next Goal**: Grouped models, threshold application, production deployment
