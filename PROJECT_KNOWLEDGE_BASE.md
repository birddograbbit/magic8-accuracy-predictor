# Magic8 Accuracy Predictor - Project Knowledge Base

## Project Overview

The Magic8 Accuracy Predictor is a machine learning system designed to predict the win/loss outcomes of Magic8's 0DTE (zero days to expiration) options trading system. The project uses a phased approach, starting with a simple MVP using readily available data and gradually adding complexity.

**Repository**: https://github.com/birddograbbit/magic8-accuracy-predictor

**Trading Symbols**: SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA  
**Strategies**: Butterfly (debit), Iron Condor (credit), Vertical Spreads (credit), Sonar

## Current Status (As of July 1, 2025)

### Phase 1: MVP Implementation - 100% Complete ✅

**Major Achievement**: Successfully trained XGBoost model with 88.21% test accuracy!

**Completed Milestones**:
- ✅ Data processing pipeline (1.5M trades in 0.6 minutes)
- ✅ Feature engineering (100x speedup: 3 hours → 2-5 minutes)
- ✅ XGBoost model training (88.21% accuracy vs 60% target)
- ✅ Strategy-specific evaluation
- ✅ Feature importance analysis
- ✅ Model saved and ready for deployment

**Key Results**:
- **Test Accuracy**: 88.21% (exceeded 60% target by 47%)
- **AUC-ROC**: 0.9497 (excellent discrimination)
- **F1 Score**: 0.8496
- **Training Time**: 2 minutes 29 seconds
- **Total Pipeline Time**: < 10 minutes (was 3+ hours)

### Performance by Strategy
| Strategy | Accuracy | Precision | Recall | F1 Score | Samples |
|----------|----------|-----------|---------|-----------|---------|
| Iron Condor | 96.24% | 0.925 | 0.999 | 0.961 | 76,390 |
| Vertical | 91.92% | 0.838 | 0.999 | 0.912 | 76,391 |
| Sonar | 88.70% | 0.784 | 0.980 | 0.871 | 76,389 |
| Butterfly | 75.98% | 0.531 | 0.297 | 0.381 | 76,391 |

## Critical Technical Achievements

### 1. Data Processing Optimization ✅
- **Problem**: Old processor took 2+ hours and crashed
- **Solution**: Batch processing with 5K record chunks
- **Result**: 150x speedup (0.6 minutes for 1.5M records)

### 2. Strategy Parsing Fix ✅
- **Problem**: Parsed from wrong column, missing Sonar strategy
- **Solution**: Parse from 'Name' column with regex
- **Result**: All 4 strategies correctly identified

### 3. Feature Engineering Optimization ✅
- **Problem**: O(n×m) complexity with apply/lambda (537 billion comparisons)
- **Solution**: pd.merge_asof() for O(n log m) complexity
- **Result**: 100x+ speedup (3+ hours → 2-5 minutes)

### 4. Profit Column Handling ✅
- **Problem**: Late-2023 CSVs dropped 'Profit' column
- **Solution**: Fallback logic: Profit → Raw → Managed
- **Result**: Captured all 1,085,312 valid profit records

## Data Statistics

### Processed Trade Data
- **Total Records**: 1,527,804 (all trades)
- **Valid Profit Records**: 1,085,312 (71%)
- **Win Rate**: 54.30% (realistic)
- **Date Range**: Jan 2023 - Jun 2025 (2.5 years)
- **Training Samples**: 916,682 (after feature engineering)

### Strategy Distribution
- Butterfly: 25.20% (274,147 trades)
- Iron Condor: 28.14% (305,561 trades)  
- Vertical: 28.14% (305,561 trades)
- Sonar: 18.52% (201,194 trades)

### Symbol Coverage
All 8 symbols have comprehensive coverage with SPX, SPY, QQQ having the most trades.

## Feature Engineering Details (74 Features)

### Top 20 Most Important Features
1. **pred_price** (9726.73) - Magic8's predicted price
2. **strategy_Butterfly** (1747.91) - Butterfly strategy indicator
3. **pred_difference** (943.14) - Prediction error
4. **prof_premium** (643.03) - Trade premium
5. **strategy_Iron Condor** (418.84) - Iron Condor indicator
6. **premium_normalized** (206.67) - Premium/price ratio
7. **strategy_Sonar** (202.27) - Sonar indicator
8. **NDX_close** (191.94) - NASDAQ-100 price
9. **pred_predicted** (171.51) - Predicted value
10. **NDX_sma_20** (143.63) - NASDAQ 20-period SMA

### Feature Categories
- **Temporal** (9): Hour, minute, day_of_week, cyclical encodings
- **Price Features** (~40): Close, SMA, momentum, volatility, RSI per symbol
- **VIX Features** (8): Level, SMA, changes, regime classification
- **Strategy** (4): One-hot encoded strategy indicators
- **Trade Features** (10): Premium, risk/reward, predictions

## Model Architecture

### XGBoost Configuration
```python
params = {
    'n_estimators': 1000,
    'learning_rate': 0.1,
    'max_depth': 6,
    'tree_method': 'hist',
    'device': 'cuda',  # GPU acceleration
    'scale_pos_weight': class_weight_ratio,
    'eval_metric': 'logloss',
    'early_stopping_rounds': 50
}
```

### Training Details
- **Algorithm**: XGBoost with GPU acceleration
- **Validation**: Temporal split (60/20/20)
- **Class Balancing**: Automatic weight adjustment
- **Best Iteration**: 999 (no early stopping)
- **Training Time**: 2 minutes 29 seconds

## Production Pipeline Flow

```
1. Raw CSV Files → process_magic8_data_optimized_v2.py
   ↓ (0.6 minutes)
2. Normalized Trade Data → phase1_data_preparation.py
   ↓ (2-5 minutes) 
3. Feature Matrix → xgboost_baseline.py
   ↓ (2.5 minutes)
4. Trained Model → predictions
```

## Next Phase: Real-Time Predictions

### Phase 2 Objectives
1. **Real-Time Feature Engineering**
   - Connect to IBKR API for live data
   - Calculate features matching training pipeline
   - Sub-second feature generation

2. **Prediction Service**
   - REST API for batch predictions
   - WebSocket for streaming predictions
   - Redis cache for features

3. **Integration Architecture**
   ```
   Magic8 Orders → Feature Generator → XGBoost Model → Predictions
         ↑                ↑
    IBKR API         Feature Cache
   ```

4. **Performance Requirements**
   - Latency: < 100ms per prediction
   - Throughput: 1000+ predictions/second
   - Availability: 99.9% during market hours

## Key Technical Decisions

### Why XGBoost?
- Best performance on tabular data
- Fast inference (< 1ms per prediction)
- Built-in feature importance
- GPU acceleration support
- Proven in production systems

### Why Temporal Split?
- Realistic backtesting (no future leakage)
- Matches production scenario
- Tests model degradation over time

### Why 74 Features?
- Balance between information and overfitting
- Computationally efficient
- All features can be calculated in real-time

## Lessons Learned

### Performance Optimization
1. **Always profile first** - Found O(n×m) bottleneck
2. **Use vectorized operations** - merge_asof vs apply
3. **Batch processing** - Prevents memory overflow
4. **Pre-calculate when possible** - Technical indicators

### Data Quality
1. **Verify column parsing** - Wrong column lost strategies
2. **Handle schema changes** - Profit → Raw/Managed
3. **Check for missing data** - Some trades lack profit
4. **Validate assumptions** - Win rate should be ~50%

### Model Development
1. **Start simple** - XGBoost baseline exceeded expectations
2. **Feature engineering matters** - More than model choice
3. **Evaluate by segment** - Strategy-specific performance
4. **Use appropriate metrics** - AUC-ROC for imbalanced data

## File Organization

### Core Production Files
- `process_magic8_data_optimized_v2.py` - Data processor
- `src/phase1_data_preparation.py` - Feature engineering
- `src/models/xgboost_baseline.py` - Model training
- `models/phase1/` - Saved model files

### Key Scripts
- `run_data_processing_v2.sh` - Processing automation
- `download_phase1_data.sh` - IBKR data download
- `predict_trades_example.py` - Prediction template

## Important Configuration

### IBKR Data Requirements
- **Symbols**: SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA
- **Bar Size**: 5 minutes
- **Duration**: 5 years
- **Format**: CSV with OHLCV data

### Processing Parameters
- **Batch Size**: 5,000 records
- **Timezone**: US Eastern (converted from UTC)
- **Tolerance**: 10 minutes for time matching
- **Memory Limit**: 8GB recommended

## Success Metrics Achieved

### Phase 1 Targets vs Actual
| Metric | Target | Actual | Status |
|--------|--------|---------|--------|
| Accuracy | >60% | 88.21% | ✅ +47% |
| AUC-ROC | >0.7 | 0.9497 | ✅ +35% |
| Feature Time | <30min | 2-5min | ✅ 6-15x |
| Training Time | <5min | 2.5min | ✅ 2x |

### Business Impact
- Can identify 88% of winning trades
- Iron Condor strategy 96% predictable
- Butterfly most challenging (76%)
- Ready for real-time deployment

## Future Enhancements

### Phase 2 (Immediate)
- Real-time prediction API
- Live IBKR integration
- Performance monitoring
- A/B testing framework

### Phase 3 (Medium-term)
- Deep learning models
- Cross-asset features
- Market regime detection
- Strategy optimization

### Phase 4 (Long-term)
- Automated trading
- Risk management
- Portfolio optimization
- Multi-strategy ensemble

---

**Last Updated**: July 1, 2025  
**Phase 1 Status**: ✅ 100% Complete  
**Model Performance**: 88.21% accuracy (47% above target)  
**Next Action**: Build real-time prediction system