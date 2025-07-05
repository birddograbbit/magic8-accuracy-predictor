# Magic8 Accuracy Predictor

## Project Overview
This project predicts the accuracy (win/loss) of Magic8's 0DTE options trading systems using machine learning.

**Revamp Status**: Multi-model architecture with symbol-specific models COMPLETE! Individual XGBoost models trained for each trading symbol (SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA) plus grouped models for similar profit scales.

**Trading Symbols**: SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA  
**Strategies**: Butterfly, Iron Condor, Vertical, Sonar  
**Status**: ✅ Phase 1 Complete | ✅ Individual Models (90-94%) | ✅ Grouped Models (90%) | ✅ Threshold Optimization

## 🎉 All Models Successfully Trained (July 5, 2025)

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

### Step 5: Train Grouped Models
```bash
# Train grouped models for symbols with similar profit scales
python train_grouped_models.py data/symbol_specific models/grouped

# Creates:
# - models/grouped/SPX_SPY_combined_model.pkl (89.95% accuracy)
# - models/grouped/QQQ_AAPL_TSLA_combined_model.pkl (90.13% accuracy)
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
- **Dual Threshold Sets**: F1-optimized and 80%-recall options
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
│   │   ├── *_trades_model.pkl         # 8 individual models
│   │   ├── thresholds.json             # F1-optimized thresholds
│   │   └── thresholds_recall80.json   # 80% recall thresholds
│   └── grouped/                        # Grouped models
│       ├── SPX_SPY_combined_model.pkl
│       ├── QQQ_AAPL_TSLA_combined_model.pkl
│       └── thresholds_grouped.json
├── process_magic8_data_optimized_v2.py # Data processor
├── split_data_by_symbol.py             # Symbol splitter
├── train_symbol_models.py              # Individual trainer
├── train_grouped_models.py             # Grouped trainer
├── optimize_thresholds.py              # Threshold optimizer (fixed)
└── optimize_thresholds_grouped.py      # Grouped threshold optimizer
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

### Threshold Optimization (NEW)
- **F1 Score Calculation**: Fixed to use sklearn.metrics.f1_score
- **Dual Optimization**: F1-optimal and 80%-recall thresholds
- **Per-Symbol-Strategy**: Each combination has its own threshold
- **Debug Mode**: Shows prediction distributions and F1 calculations

### Multi-Model Prediction Pipeline
```python
# Pseudo-code for symbol-aware predictions with thresholds
model_strategy = SymbolModelStrategy(config)
predictor = MultiModelPredictor(model_strategy)
thresholds = load_thresholds()  # Load optimized thresholds

for order in magic8_orders:
    model = predictor.get_model(order.symbol)
    threshold = thresholds[order.symbol][order.strategy]
    probability = model.predict_proba(features)
    
    if probability > threshold:  # Use optimized threshold, not 0.5
        execute_trade(order)
```

## 🎯 Next Steps: Production Integration

### 1. Prediction API Improvements ✅
- All individual and grouped models loaded automatically
- Thresholds loaded from JSON and applied per symbol/strategy
- Routing supports grouped models with fallback to default
- Tested with real-time data

### 2. Performance Validation
- Compare individual vs grouped model performance
- Validate 76x profit scale handling
- Backtest with optimized thresholds
- Measure actual profit improvements

### 3. Integration with Trading Systems
- Update DiscordTrading ML client
- Connect to Magic8-Companion data API
- Implement paper trading tests
- Monitor latency and performance

### API Integration

#### Starting the Prediction API
```bash
# Start with multi-model support
python src/prediction_api.py

# Verify API
curl http://localhost:8000/

# Test prediction with threshold application
curl -X POST http://localhost:8000/predict \
     -H "Content-Type: application/json" \
     -d '{"strategy": "Butterfly", "symbol": "SPX", "premium": 24.82, "predicted_price": 5855}'
```

## 📚 Documentation

- `magic8-predictor-revamp-plan.md` - Complete revamp blueprint (~95% complete)
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
- **F1 Score Optimization**: Proper balance of precision and recall

## 🐛 Common Issues & Solutions

### All Thresholds Showing 0.50
Fixed! The F1 calculation was using bitwise AND. Now uses sklearn.metrics.f1_score for correct calculation.

### Missing Raw Data
Ensure you have the Magic8 CSV files organized by date folders with profit, trades, and delta sheets.

### Empty data/symbol_specific Directory
Run the complete pipeline: process data → split by symbol → train models → optimize thresholds

### Feature Mismatch
Use the minimal feature_info.json to let models auto-detect features from your data.

---

**Repository**: https://github.com/birddograbbit/magic8-accuracy-predictor  
**Last Updated**: July 5, 2025  
**Model Status**: ✅ All models trained (individual + grouped)  
**Threshold Status**: ✅ Optimized with proper F1 calculation  
**Revamp Progress**: ~95% Complete  
**Next Goal**: Production API integration and performance validation
