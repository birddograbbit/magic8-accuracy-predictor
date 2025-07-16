# Magic8 Accuracy Predictor

## Project Overview
This project predicts the accuracy (win/loss) of Magic8's 0DTE options trading systems using machine learning.

**Revamp Status**: Multi-model architecture with symbol-specific models COMPLETE! Individual XGBoost models trained for each trading symbol (SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA) plus grouped models for similar profit scales. Hierarchical prediction and risk/reward calculations implemented.

**Trading Symbols**: SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA  
**Strategies**: Butterfly, Iron Condor, Vertical, Sonar  
**Status**: ✅ Phase 1-7 Complete | ✅ Individual Models (90-94%) | ✅ Grouped Models (90%) | ✅ Symbol-Strategy Models | ✅ Risk/Reward Calculator | ✅ Batch Predictions | ✅ Enhanced Caching

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

### Part A: Initial Setup and Model Training

#### Step 1: Setup Environment
```bash
git clone https://github.com/birddograbbit/magic8-accuracy-predictor.git
cd magic8-accuracy-predictor

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Recommended versions
# - Python 3.10
# - scikit-learn 1.5
# - XGBoost 2.x (models saved via Booster.save_model for compatibility)
```

#### Step 2: Process Raw Magic8 Data
```bash
# Run the complete data processor that merges all sheets
./run_data_processing_v2.sh

# This creates: data/processed_optimized_v2/magic8_trades_complete.csv
# Processing time: ~3.5 minutes for 1M+ trades
# Note: Delta features (short_term/long_term) are included if delta sheets are present
```

#### Step 3: Split Data by Symbol
```bash
# Create symbol-specific CSV files
python split_data_by_symbol.py data/processed_optimized_v2/magic8_trades_complete.csv data/symbol_specific

# This creates:
# - data/symbol_specific/SPX_trades.csv
# - data/symbol_specific/SPY_trades.csv
# - ... (one file per symbol)
# - data/symbol_specific/symbol_statistics.json
```

#### Step 4: Train Symbol-Specific Models
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

`prepare_symbol_data()` automatically adds a `target` column derived
from the `profit` column (1 for wins, 0 for losses). The training
scripts rely on this column for supervised learning.

#### Step 4a: Analyze Profit Scales by Strategy
```bash
# Analyze profit ranges for correct symbol grouping
python analyze_profit_scales.py \
    data/processed_optimized_v2/magic8_trades_complete.csv \
    data/profit_scale

# Outputs:
# - data/profit_scale/profit_scale_stats.json
# - data/profit_scale/profit_scale_groups.json
# Correctly classifies SPX as large-scale based on actual profit ranges
```

#### Step 5: Train Grouped Models
```bash
# Train grouped models for symbols with similar profit scales
python train_grouped_models.py data/symbol_specific models/grouped

# Creates:
# - models/grouped/SPX_SPY_combined_model.pkl (89.95% accuracy)
# - models/grouped/QQQ_AAPL_TSLA_combined_model.pkl (90.13% accuracy)
```

#### Step 5a: Train Symbol-Strategy Models
```bash
# Train hierarchical models for each symbol-strategy combination
python train_symbol_strategy_models.py data/processed_optimized_v2/magic8_trades_complete.csv models/symbol_strategy

# Creates models like:
# - models/symbol_strategy/SPX_Butterfly_model.pkl
# - models/symbol_strategy/SPX_IronCondor_model.pkl
# - ... (one for each symbol-strategy pair with sufficient data)
```

#### Step 6: Optimize Thresholds
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

#### Step 7: Configure API with Full Model Hierarchy
Ensure `config/config.yaml` has all models configured:
```yaml
models:
  # Individual models
  AAPL: models/individual/AAPL_trades_model.pkl
  TSLA: models/individual/TSLA_trades_model.pkl
  RUT: models/individual/RUT_trades_model.pkl
  SPY: models/individual/SPY_trades_model.pkl
  QQQ: models/individual/QQQ_trades_model.pkl
  NDX: models/individual/NDX_trades_model.pkl
  XSP: models/individual/XSP_trades_model.pkl
  SPX: models/individual/SPX_trades_model.pkl

  # Grouped models
  SPX_SPY: models/grouped/SPX_SPY_combined_model.pkl
  QQQ_AAPL_TSLA: models/grouped/QQQ_AAPL_TSLA_combined_model.pkl

  # Fallback
  default: models/xgboost_phase1_model.pkl

# Symbol-strategy models directory
symbol_strategy_models:
  dir: models/symbol_strategy

# Caching configuration (NEW)
performance:
  cache:
    enabled: true
    market_data_ttl: 300    # 5 minutes - for continuous monitoring
    feature_ttl: 60         # 1 minute - features change slowly
    prediction_ttl: 300     # 5 minutes - align with monitoring interval
    max_size: 1000
    
  batch_predictions:
    max_batch_size: 100     # Support large batches for continuous monitoring
```

### Part B: Production Operation

#### Step 8: Start Enhanced Prediction API
```bash
# Start the real-time prediction API with hierarchical models and risk/reward
./run_realtime_api.sh

# Or manually:
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
python src/prediction_api_realtime.py

# API will be available at http://localhost:8000
```

#### API Endpoints:
- `GET /` - Health check and loaded model status
- `GET /market/{symbol}` - Real-time market data
- `POST /predict` - Single prediction with hierarchical model selection
- `POST /predict/batch` - **NEW: Batch predictions for continuous monitoring**
- `POST /calculate_risk_reward` - Calculate max profit/loss for trades

#### Step 9: Production Usage Patterns

##### For Individual Predictions (Traditional)
```bash
# Test single prediction
curl -X POST http://localhost:8000/predict \
     -H "Content-Type: application/json" \
     -d '{
       "strategy": "Butterfly", 
       "symbol": "SPX", 
       "premium": 24.82,
       "predicted_price": 5855,
       "strikes": [5905, 5855, 5805]
     }'
```

##### For Batch Predictions (Continuous Monitoring)
```bash
# Test batch prediction - ideal for DiscordTrading continuous monitoring
curl -X POST http://localhost:8000/predict/batch \
     -H "Content-Type: application/json" \
     -d '{
       "requests": [
         {"symbol": "SPX", "strategy": "Butterfly", "premium": 24.82, "predicted_price": 5855},
         {"symbol": "SPX", "strategy": "Iron Condor", "premium": 0.65, "predicted_price": 5855},
         {"symbol": "SPY", "strategy": "Butterfly", "premium": 2.48, "predicted_price": 585.5},
         {"symbol": "SPY", "strategy": "Iron Condor", "premium": 0.43, "predicted_price": 585.5}
       ],
       "share_market_data": true
     }'

# Response includes cache metrics for monitoring performance
```

#### Step 10: Monitor Performance

##### Cache Effectiveness
- Monitor `batch_metrics` in responses
- Feature cache hit rate should be >70% after warmup
- Prediction cache serves repeated requests instantly

##### Log Monitoring
```bash
# View API logs (directory created automatically)
tail -f logs/prediction_api.log

# Monitor cache performance
grep "cache" logs/prediction_api.log | tail -20

# Watch prediction results
tail -f logs/predictions.jsonl | jq
```

## 📊 Key Performance Optimizations

### Continuous Monitoring Support (NEW)
- **Batch Endpoint**: Process 32+ predictions in one API call
- **Smart Caching**: 3-tier cache (market data, features, predictions)
- **Shared Resources**: Market data fetched once per batch
- **Configurable TTLs**: Align cache expiry with monitoring intervals

### Cache Configuration
```yaml
performance:
  cache:
    market_data_ttl: 300   # 5 minutes - matches continuous monitoring
    feature_ttl: 60        # 1 minute - features change slowly  
    prediction_ttl: 300    # 5 minutes - valid for full monitoring cycle
```

### Performance Gains
- **Before**: 32 API calls × 200ms = 6.4 seconds
- **After**: 1 batch call = <500ms (93% reduction)
- **Cache Hit Rate**: >70% after warmup
- **Market Data Calls**: 1 per cycle (was 32)

## 📊 Key Results

### Symbol-Specific Profit Scales (Corrected)
- **Large Scale**: SPX ($2800 to -$1000 range), NDX ($2,452 avg), RUT ($503 avg)
- **Medium Scale**: SPY ($100-1000 range)
- **Small Scale**: XSP ($4.39), QQQ ($3.93), AAPL ($12.79), TSLA ($12.86)

### Optimized Thresholds (Examples)
- **Butterfly strategies**: 0.45-0.55 (more conservative)
- **Iron Condor strategies**: 0.50-0.75 (more selective)
- **Mean threshold**: 0.600 (std: 0.097)
- **F1 scores**: 0.739-0.986 (mean: 0.910)

### Model Features (31+ auto-detected)
Including temporal features, price data, VIX indicators, risk/reward ratios, strike information, and strategy encodings.
**Note**: Delta features (short_term/long_term) are now fully integrated into the real-time API.

### Data Statistics
- **Total trades**: 1,076,742 (with complete data)
- **Date Range**: Jan 2023 - Jun 2025 (2.5 years)
- **Strategies**: Butterfly (27.5%), Iron Condor (27.5%), Vertical (27.5%), Sonar (18.4%)

## 📈 Enhanced Multi-Model Architecture

The architecture handles symbol-specific characteristics with hierarchical prediction:
- **Symbol-Strategy Models**: Highest priority (e.g., SPX_Butterfly)
- **Individual Models**: Second priority for each symbol
- **Grouped Models**: Third priority for similar profit scales
- **Default Model**: Fallback for new symbols/strategies
- **Hierarchical Predictor**: Automatic model selection with 4-level fallback
- **Risk/Reward Calculator**: Real-time max profit/loss calculations
- **Batch Processor**: Efficient handling of multiple predictions
- **Cache Manager**: 3-tier caching for optimal performance

## 📁 Project Structure

```
magic8-accuracy-predictor/
├── src/
│   ├── models/
│   │   ├── xgboost_symbol_specific.py  # Symbol-specific training
│   │   ├── symbol_strategy_trainer.py  # Symbol-strategy models
│   │   ├── hierarchical_predictor.py   # 4-level fallback logic
│   │   └── multi_model.py              # Multi-model routing
│   ├── data_providers/                 # Market data interfaces
│   │   ├── standalone_provider.py      # Direct IBKR connection
│   │   └── companion_provider.py       # Magic8-Companion API
│   ├── feature_engineering/
│   │   ├── real_time_features.py       # Feature generation
│   │   └── delta_features.py           # Delta-aware features
│   ├── cache_manager.py                # NEW: Feature/prediction caching
│   ├── risk_reward_calculator.py       # Option spread calculations
│   ├── enhanced_discord_parser.py      # Parse Magic8 messages
│   ├── profit_scale_analyzer.py        # Profit scale analysis
│   └── prediction_api_realtime.py      # Main API with batch support
├── data/
│   ├── processed_optimized_v2/         # Complete merged data
│   ├── symbol_specific/                # Per-symbol CSV files
│   └── profit_scale/                   # Profit analysis results
├── models/
│   ├── individual/                     # Symbol-specific models
│   │   ├── *_trades_model.pkl         # 8 individual models
│   │   ├── thresholds.json             # F1-optimized thresholds
│   │   └── thresholds_recall80.json   # 80% recall thresholds
│   ├── grouped/                        # Grouped models
│   │   ├── SPX_SPY_combined_model.pkl
│   │   ├── QQQ_AAPL_TSLA_combined_model.pkl
│   │   └── thresholds_grouped.json
│   └── symbol_strategy/                # Symbol-strategy models
│       └── *_*_model.pkl              # e.g., SPX_Butterfly_model.pkl
├── config/
│   └── config.yaml                     # API configuration
├── process_magic8_data_optimized_v2.py # Data processor
├── split_data_by_symbol.py             # Symbol splitter
├── train_symbol_models.py              # Individual trainer
├── train_grouped_models.py             # Grouped trainer
├── train_symbol_strategy_models.py     # Symbol-strategy trainer
├── analyze_profit_scales.py            # Profit scale analyzer
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

### Hierarchical Model Architecture
1. **Symbol-Strategy Models**: Most specific (e.g., SPX_Butterfly)
2. **Symbol Models**: Per-symbol fallback (e.g., SPX)
3. **Strategy Models**: Per-strategy fallback (e.g., Butterfly)
4. **Default Model**: Universal fallback

### Risk/Reward Calculations
- **Butterfly**: Max profit at center strike, limited risk
- **Iron Condor**: Credit spread with defined risk
- **Vertical**: Directional spread with capped profit/loss
- **Breakeven Points**: Calculated for all strategies

### Multi-Model Prediction Pipeline
```python
# Hierarchical prediction with dynamic thresholds
if predictor:
    # Try symbol-strategy first, then fallback
    proba = predictor.predict_proba(req.symbol, req.strategy, X)[0][1]
    
    # Get appropriate threshold
    threshold = 0.5  # default
    
    # Check symbol-strategy models
    key = f"{req.symbol}_{req.strategy}"
    if key in predictor.symbol_strategy_models:
        threshold = thresholds_strategy.get(key, 0.5)
    # Check individual models
    elif req.symbol in predictor.symbol_models:
        sym_thresh = thresholds_individual.get(req.symbol, {})
        threshold = sym_thresh.get(req.strategy, 0.5)
    # Check grouped models
    else:
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
     -d '{
       "strategy": "Butterfly", 
       "symbol": "SPX", 
       "premium": 24.82,
       "predicted_price": 5855,
       "short_term": 5850,
       "long_term": 5860,
       "strikes": [5905, 5855, 5805],
       "action": "BUY"
     }'

# Test risk/reward calculation
curl -X POST http://localhost:8000/calculate_risk_reward \
     -H "Content-Type: application/json" \
     -d '{
       "symbol": "SPX",
       "strategy": "Butterfly",
       "strikes": [5905, 5855, 5805],
       "premium": 24.82,
       "action": "BUY",
       "quantity": 1
     }'
```

### API Endpoints
- `GET /` - Health check and model status (shows loaded models)
- `GET /market/{symbol}` - Real-time market data
- `POST /predict` - Get prediction with hierarchical model selection
- `POST /predict/batch` - Predict multiple trades in one call (optimized for continuous monitoring)
- `POST /calculate_risk_reward` - Calculate max profit/loss and breakevens

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

### Caching Configuration
Adjust cache TTLs in `config/config.yaml` under `performance.cache`:
```yaml
performance:
  cache:
    market_data_ttl: 300   # 5 minutes
    feature_ttl: 60        # 1 minute
    prediction_ttl: 300    # 5 minutes
```

## 📚 Documentation

- `magic8-predictor-revamp-plan2.md` - Complete revamp blueprint (Phases 5-7 complete)
- `magic8-predictor-revamp-plan3.md` - Continuous monitoring optimization plan
- `REVAMP_SUMMARY.md` - Quick reference for revamp status
- `REVAMP_ACTION_ITEMS.md` - Remaining deployment tasks
- `docs/DATA_SCHEMA_COMPLETE.md` - Complete data schema after processing
- `docs/MULTI_MODEL_OVERVIEW.md` - Multi-model architecture details
- `docs/PROFIT_SCALE_ANALYSIS.md` - Profit scale grouping documentation
- `PROJECT_KNOWLEDGE_BASE.md` - Comprehensive project details
- `PROJECT_STATUS_CONTINUOUS_MONITORING.md` - Integration with DiscordTrading
- `DISCORDTRADING_BATCH_INTEGRATION.md` - Batch endpoint integration guide
- `IMPLEMENTATION_PLAN.md` - Full project roadmap

## ⚡ Performance Optimizations

### Recent Improvements (January 2025)
- **Batch Prediction Endpoint**: Process multiple predictions in one call
- **3-Tier Caching**: Market data, features, and predictions cached
- **Hierarchical Predictor**: 4-level model fallback system
- **Risk/Reward Calculator**: Real-time option spread analysis
- **Profit Scale Correction**: SPX properly classified as large-scale
- **Symbol-Strategy Models**: Most granular predictions possible

### Symbol-Specific Benefits
- **Profit Scale Handling**: 76x differences properly modeled
- **Feature Relevance**: Each symbol uses only relevant features
- **Threshold Optimization**: Per-symbol-strategy for maximum profit
- **Training Efficiency**: Parallel training possible
- **Model Hierarchy**: Best model automatically selected

## 🐛 Common Issues & Solutions

### API Not Starting
- Check that models exist in all directories: `models/individual/`, `models/grouped/`, `models/symbol_strategy/`
- Verify all threshold JSON files are generated
- Ensure PYTHONPATH is set correctly

### Cache Not Working
- Verify cache is enabled in `config.yaml`
- Check cache TTL settings are appropriate
- Monitor cache metrics in batch response

### Empty data/symbol_specific Directory
Run the complete pipeline: process data → split by symbol → train models → optimize thresholds

### IBKR Connection Issues
- Ensure Gateway/TWS is running on port 7497
- Check API permissions are enabled
- Verify no other clients are using the same client ID

### Risk/Reward Not Calculated
- Ensure strikes array is provided in request
- Check strategy name matches exactly
- Verify action is "BUY" or "SELL"

## 🚨 Production Deployment

### Pre-deployment Checklist
- [x] All models trained (individual + grouped + symbol-strategy)
- [x] Thresholds optimized and saved
- [x] API tested with all endpoints
- [x] Batch endpoint implemented and tested
- [x] Caching layer configured
- [x] Configuration updated
- [x] Risk/reward calculator tested
- [x] Delta features integrated in API
- [ ] IBKR Gateway configured for production
- [ ] Monitoring setup
- [ ] Backup procedures documented
- [ ] Load testing with continuous monitoring workload

### Deployment Steps
1. Set environment to production in config.yaml
2. Configure cache TTLs for your monitoring interval
3. Start IBKR Gateway (if using standalone)
4. Run API: `./run_realtime_api.sh`
5. Test batch endpoint with expected load
6. Monitor logs in `logs/` directory
7. Validate predictions match expected thresholds
8. Test hierarchical model selection
9. Verify risk/reward calculations
10. Monitor cache hit rates

---

**Repository**: https://github.com/birddograbbit/magic8-accuracy-predictor  
**Last Updated**: January 2025  
**Model Status**: ✅ All models trained and integrated (3-tier hierarchy)  
**API Status**: ✅ Real-time API with hierarchical prediction, risk/reward, and batch support  
**Revamp Progress**: 99% Complete - Phases 0-7 Done + Continuous Monitoring Support  
**Next Goal**: Deploy to production with DiscordTrading integration
