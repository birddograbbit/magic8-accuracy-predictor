# Magic8 Accuracy Predictor

## Project Overview
This project predicts the accuracy (win/loss) of Magic8's 0DTE options trading system. We use a phased approach, starting with a simple MVP using readily available data and gradually adding complexity.

**Trading Symbols**: SPX, SPY, RUT, QQQ, XSP, NDX, AAPL, TSLA  
**Strategies**: Butterfly (debit), Iron Condor (credit), Vertical Spreads (credit)

## 🚀 Phase 1 Quick Start (MVP - Ship Fast!)

### Step 1: Clone and Setup
```bash
git clone https://github.com/birddograbbit/magic8-accuracy-predictor.git
cd magic8-accuracy-predictor

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Download IBKR Data
First, ensure your IBKR TWS/Gateway is running, then:

```bash
# Copy your IBKR download script to this directory
cp /path/to/your/ibkr_downloader.py .

# Make the download script executable
chmod +x download_phase1_data.sh

# Download all required symbols (uses port 7497 by default)
./download_phase1_data.sh

# Or specify a different port
./download_phase1_data.sh 7496
```

### Step 3: Run Phase 1 Pipeline
```bash
# Process data and create features
python src/phase1_data_preparation.py

# Train XGBoost baseline model
python src/models/xgboost_baseline.py
```

## 📊 Phase 1 Features (MVP)

Using only readily available data:

### From Your Trade Data
- Trade outcomes (profit/loss)
- Strategy types
- Premium, risk, reward values
- Trade probabilities

### From IBKR Historical Data
- 5-minute price bars for all symbols
- VIX levels
- Calculated technical indicators:
  - RSI, Moving Averages
  - Price momentum
  - Volatility measures

### Engineered Features
- Time-based features (hour, minute, time to close)
- Market regime (based on VIX levels)
- Strategy encoding
- Price position indicators

**Total: ~60-70 features**

## 🎯 Phase 1 Goals

- **Accuracy**: > 60% (baseline is 50%)
- **Timeline**: 2 weeks to working model
- **Complexity**: Simple XGBoost + feature engineering
- **Focus**: Get a working system quickly, iterate from there

## 📁 Project Structure

```
magic8-accuracy-predictor/
├── data/
│   ├── normalized/           # Your existing trade data
│   ├── ibkr/                # Downloaded IBKR price data
│   └── phase1_processed/    # Processed features
├── src/
│   ├── phase1_data_preparation.py  # Simple data pipeline
│   ├── data_preparation.py         # (Future: comprehensive features)
│   └── models/
│       └── xgboost_baseline.py     # Phase 1 model
├── download_phase1_data.sh   # IBKR data download helper
├── PHASE1_PLAN.md           # Detailed Phase 1 plan
└── requirements.txt
```

## 📈 Implementation Phases

### ✅ Phase 1: MVP (Current)
- Use existing trade data + IBKR price data
- Simple features (price, time, VIX)
- XGBoost baseline model
- 2-week implementation

### 📅 Phase 2: Enhanced Features
- Add cross-asset correlations
- Market microstructure features
- Advanced technical indicators
- Transformer models

### 📅 Phase 3: Production System
- Real-time predictions
- API deployment
- Performance monitoring
- Strategy-specific models

## 🔧 Data Requirements

### What You Need
1. Your normalized trade data (already have)
2. IBKR account with market data subscription
3. Python 3.8+

### What We Use (Phase 1)
- Historical price data from IBKR
- VIX data (INDEX:VIX)
- No exotic data sources
- No historical options data needed

## 📊 Expected Results

### Phase 1 Targets
- Overall accuracy: > 60%
- Per-strategy accuracy: > 58%
- Feature calculation: < 1 second
- Model training: < 5 minutes

### Key Metrics
- Accuracy, Precision, Recall
- F1 Score, AUC-ROC
- Performance by strategy
- Performance by market regime

## 🚦 Next Steps After Phase 1

1. **Analyze Results**
   - Which features are most important?
   - Which strategies are easiest to predict?
   - When does the model fail?

2. **Iterate Quickly**
   - Add features that show promise
   - Remove features that don't help
   - Try different model architectures

3. **Plan Phase 2**
   - Based on Phase 1 learnings
   - Add complexity only where it helps
   - Keep focus on practical improvements

## 💡 Key Principles

1. **Start Simple**: Phase 1 uses only readily available data
2. **Ship Fast**: Get a working model in 2 weeks
3. **Iterate**: Learn what works before adding complexity
4. **Be Practical**: Use data you can actually get
5. **Measure Everything**: Track what improves predictions

## 🐛 Troubleshooting

### IBKR Data Download Issues
- Ensure TWS/Gateway is running
- Check your market data subscriptions
- Try reducing the duration (e.g., "1 Y" instead of "3 Y")
- Check logs in `logs/` directory

### Feature Calculation Issues
- Check for missing IBKR data files
- Ensure all symbols have been downloaded
- Look for NaN values in processed data

## 📚 References

- **Your IBKR Script**: For downloading historical data
- **XGBoost**: Fast and effective for tabular data
- **yfinance**: Backup for VIX data if needed

## 🤝 Contributing

Focus on Phase 1 improvements:
1. Better feature engineering
2. Model hyperparameter tuning
3. Error analysis and debugging
4. Documentation improvements

## 📧 Contact

For questions or contributions, please open an issue on GitHub.

---

**Remember**: The goal of Phase 1 is to get a working system quickly with available data. We'll add complexity in future phases only where it demonstrably improves predictions.
