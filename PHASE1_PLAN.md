# Phase 1 MVP Implementation Plan - Magic8 Accuracy Predictor

## Overview
This document outlines a practical Phase 1 implementation focused on readily available data. We'll build a working MVP using your existing trade data and historical price data from IBKR.

## Available Data Sources

### 1. Your Existing Data (Already Have)
- 3 years of normalized Magic8 trading results
- Fields include:
  - Trade outcomes (profit/loss)
  - Strategy names (Butterfly, Iron Condor, Vertical)
  - Predicted prices and actual prices
  - Premium, risk, reward values
  - Delta values from actual trades
  - Trade probabilities

### 2. IBKR Historical Data (Can Download)
Using your script, we can get:
- **Symbols**: SPX, SPY, RUT, QQQ, NDX, XSP, AAPL, TSLA
- **Also**: VIX (as INDEX:VIX)
- **Timeframes**: 1 min, 5 mins, 15 mins, 1 hour bars
- **Fields**: date, open, high, low, close, volume
- **Duration**: Up to several years of historical data

### 3. Free Internet Sources (Backup)
- Yahoo Finance for VIX data (if IBKR fails)
- Basic economic calendar (optional for Phase 1)

## Phase 1 Feature Set (Practical & Achievable)

### Temporal Features (9 features)
- Hour, minute, day of week
- Cyclical encoding (hour_sin, hour_cos)
- Market session indicators (is_open, first_30min, last_30min)
- Minutes to close (for 0DTE theta decay)

### Price-Based Features (30-40 features)
For each symbol (SPX, SPY, etc.):
- Current price (from 5-min bars)
- Simple moving average (20-period)
- Price momentum (5-period return)
- Volatility (20-period std dev)
- RSI (14-period)
- Price position (where in 20-period range)

### VIX Features (6-8 features)
- VIX level
- VIX 20-period SMA
- VIX change (1-period and 5-period)
- VIX regime classification (low/normal/elevated/high)

### Trade-Specific Features (8-10 features)
- Strategy one-hot encoding (Butterfly, Iron Condor, Vertical)
- Premium normalized by underlying price
- Risk-reward ratio
- Original predicted vs actual price difference
- Trade probability (from your data)

**Total Phase 1 Features: ~60-70 features**

## Phase 1 Model Architecture (Simple & Effective)

### 1. Start Simple
- **XGBoost Classifier**: Primary model for feature interactions
- **Logistic Regression**: Baseline for comparison
- **Simple Ensemble**: Average of both models

### 2. Quick Iterations
- Train on 60% of data (temporal split)
- Validate on 20%
- Test on final 20%
- No complex architectures yet

### 3. Focus on Feature Engineering
- Most gains will come from good features
- Price momentum and volatility regimes
- Time decay for 0DTE

## Implementation Steps (2 Weeks)

### Week 1: Data Pipeline
**Day 1-2: IBKR Data Download**
```bash
# Download all symbols with 5-min bars
python ibkr_downloader.py --symbols INDEX:SPX INDEX:VIX STOCK:SPY INDEX:RUT \
  INDEX:NDX STOCK:QQQ INDEX:XSP STOCK:AAPL STOCK:TSLA \
  --bar_sizes "5 mins" --duration "3 Y"
```

**Day 3-4: Data Integration**
- Run `phase1_data_preparation.py`
- Merge IBKR price data with your trade data
- Calculate technical indicators
- Create train/val/test splits

**Day 5: Feature Analysis**
- Check feature distributions
- Identify missing data
- Correlation analysis
- Feature importance with random forest

### Week 2: Model Development
**Day 6-7: Baseline Models**
- Implement XGBoost classifier
- Train logistic regression baseline
- Compare performance metrics

**Day 8-9: Model Tuning**
- Hyperparameter optimization
- Feature selection
- Class weight balancing

**Day 10: Evaluation & Documentation**
- Comprehensive evaluation metrics
- Performance by strategy type
- Performance by market regime
- Document findings

## Directory Structure for Phase 1
```
magic8-accuracy-predictor/
├── data/
│   ├── normalized/           # Your existing data
│   ├── ibkr/                # Downloaded IBKR data
│   └── phase1_processed/    # Processed features
├── src/
│   ├── phase1_data_preparation.py  # MVP data pipeline
│   ├── models/
│   │   ├── xgboost_baseline.py
│   │   └── logistic_baseline.py
│   └── evaluation/
│       └── phase1_metrics.py
├── notebooks/
│   ├── phase1_eda.ipynb     # Exploratory analysis
│   └── phase1_results.ipynb # Results visualization
└── configs/
    └── phase1_config.yaml    # Simple configuration
```

## Success Criteria for Phase 1

### Minimum Viable Metrics
- **Accuracy**: > 60% (baseline is ~50% random)
- **Consistent**: Works across all 3 strategies
- **Stable**: Performance doesn't degrade over time
- **Fast**: < 1 second prediction time

### Deliverables
1. Working data pipeline with IBKR integration
2. Trained XGBoost model
3. Evaluation report with metrics
4. List of insights for Phase 2

## What We're NOT Doing in Phase 1

### Complex Features
- ❌ Cross-asset correlations (bonds, currencies)
- ❌ Market microstructure (bid-ask, order flow)
- ❌ Options Greeks (no historical option data)
- ❌ Complex market indicators

### Complex Models
- ❌ Transformer architectures
- ❌ Deep learning models
- ❌ Complex ensembles
- ❌ Real-time systems

### Production Features
- ❌ API endpoints
- ❌ Docker containers
- ❌ Real-time data feeds
- ❌ Monitoring dashboards

## Phase 2 Preview (Future)

Once Phase 1 is working:
1. Add more data sources (if value proven)
2. Implement Transformer for sequence modeling
3. Strategy-specific models
4. Real-time prediction system
5. Production deployment

## Next Immediate Steps

1. **Download IBKR Data**:
```bash
# Create data directory
mkdir -p data/ibkr

# Run your IBKR downloader for all symbols
python ibkr_downloader.py --symbols INDEX:SPX INDEX:VIX STOCK:SPY \
  --bar_sizes "5 mins" --duration "3 Y" --port 7497
```

2. **Run Phase 1 Pipeline**:
```bash
# After downloading IBKR data
python src/phase1_data_preparation.py
```

3. **Quick Validation**:
```python
# Check the output
import pandas as pd
train = pd.read_csv('data/phase1_processed/train_data.csv')
print(f"Training samples: {len(train)}")
print(f"Features: {train.shape[1]}")
print(f"Class distribution: {train['target'].value_counts()}")
```

## Key Advantages of This Approach

1. **Uses Available Data**: No hunting for exotic data sources
2. **Quick to Implement**: 2 weeks to working model
3. **Iterative**: Learn what works before adding complexity
4. **Practical**: Focused on what will actually improve predictions
5. **Measurable**: Clear metrics to track progress

## Risk Mitigation

1. **Data Quality**: IBKR data is reliable and clean
2. **Overfitting**: Simple models with proper validation
3. **Complexity**: Start simple, add only what improves results
4. **Time**: 2-week timeline is realistic

This Phase 1 plan gives you a working system quickly, using data you can actually get, with clear next steps for improvement.
