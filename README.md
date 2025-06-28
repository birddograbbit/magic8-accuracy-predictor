# Magic8 Accuracy Predictor

## Project Overview
This project aims to predict the accuracy (win or loss) of Magic8's trading predictions using a hybrid Transformer + XGBoost + Decision Tree ensemble architecture. The system analyzes historical trading data to identify patterns based on time of day, day of month, symbol, VIX levels, and stock price levels.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/birddograbbit/magic8-accuracy-predictor.git
cd magic8-accuracy-predictor

# Install dependencies
pip install -r requirements.txt

# Run quick start script
python quick_start.py

# This will:
# 1. Test data loading
# 2. Install dependencies (optional)
# 3. Run data preparation pipeline (optional)
```

## 📋 Implementation Status

### Phase 1: Data Preparation ✅ Complete
- [x] Data normalization (already done)
- [x] Feature engineering script created
- [x] VIX data integration
- [x] Technical indicators
- [x] Temporal features
- [x] Market regime classification

### Phase 2: Model Development 🚧 In Progress
- [ ] Fork and adapt QuantStock framework
- [ ] Binary classification transformer
- [ ] XGBoost classifier
- [ ] Decision tree for market regime
- [ ] Ensemble predictor

### Phase 3: Production Deployment 📅 Planned
- [ ] FastAPI service
- [ ] Docker containerization
- [ ] Real-time prediction endpoint
- [ ] Performance monitoring

## 🏗️ Architecture

### Data Pipeline
```
Raw CSV Files → Normalization → Feature Engineering → Train/Val/Test Split
                                        ↓
                                   VIX Data (yfinance)
                                   Technical Indicators (ta)
                                   Temporal Features
```

### Model Architecture
```
Input Features → [Transformer] → Probability
              → [XGBoost]     → Probability  → [Ensemble] → Final Prediction
              → [Decision Tree] → Market Regime
```

### Key Components

1. **Data Preparation** (`src/data_preparation.py`)
   - Loads normalized trading data
   - Fetches VIX data from Yahoo Finance
   - Adds temporal and technical features
   - Creates train/validation/test splits

2. **Model Configurations** (`configs/model_config.yaml`)
   - Transformer: 3-layer encoder for sequence patterns
   - XGBoost: For feature interactions
   - Decision Tree: Market regime classification
   - Ensemble: Weighted voting mechanism

3. **Implementation Plan** (`IMPLEMENTATION_PLAN.md`)
   - Detailed architecture design
   - Timeline and milestones
   - Success criteria

## 📊 Data Structure

### Input Features
- **Temporal**: hour_sin/cos, day_of_week, day_of_month, is_market_open
- **Market Data**: VIX levels, price levels, technical indicators (RSI, MA, volatility)
- **Trading Data**: symbol, strategy_name, predicted prices, premiums
- **Regime**: Low/Medium/High volatility classification

### Output
- Binary classification: 1 (profitable trade) or 0 (loss)

## 🛠️ Development

### Setup Development Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dev dependencies
pip install -r requirements.txt

# Run tests
pytest tests/
```

### Project Structure
```
magic8-accuracy-predictor/
├── src/
│   ├── data/
│   │   └── data_preparation.py
│   ├── models/
│   │   ├── BinaryTransformer.py (TODO)
│   │   └── XGBoostClassifier.py (TODO)
│   └── ensemble/
│       └── EnsemblePredictor.py (TODO)
├── configs/
│   └── model_config.yaml
├── data/
│   ├── source/          # Original CSV files
│   ├── normalized/      # Processed data files
│   └── processed/       # Feature-engineered data
├── notebooks/
│   └── Transformer_Trading.ipynb  # Reference implementation
├── IMPLEMENTATION_PLAN.md
├── requirements.txt
└── quick_start.py
```

## 📈 Performance Metrics

### Classification Metrics
- Accuracy, Precision, Recall, F1-score
- AUC-ROC curve
- Confusion matrix

### Trading Metrics
- Win rate
- Profit factor
- Average win/loss ratio
- Maximum drawdown

## 🔧 Configuration

See `configs/model_config.yaml` for detailed model and training configurations.

Key parameters:
- Sequence length: 60 (5 hours of 5-minute data)
- Transformer layers: 3
- XGBoost trees: 1000
- Ensemble weights: Optimized on validation set

## 🚦 Next Steps

1. **Clone QuantStock Framework**
   ```bash
   git clone https://github.com/MXGao-A/QuantStock.git
   # Adapt for binary classification
   ```

2. **Implement Models**
   - Modify transformer for binary output
   - Add custom loss functions
   - Implement ensemble voting

3. **Training Pipeline**
   - Cross-validation
   - Hyperparameter tuning
   - Model selection

4. **Production Deployment**
   - API service
   - Docker container
   - Monitoring dashboard

## 📚 References

- **QuantStock**: Production-ready framework for stock prediction
  - https://github.com/MXGao-A/QuantStock
- **Original Transformer Code**: See `notebooks/Transformer_Trading.ipynb`
- **yfinance**: For VIX data - https://github.com/ranaroussi/yfinance
- **ta**: Technical indicators - https://github.com/bukosabino/ta

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 📧 Contact

For questions or contributions, please open an issue on GitHub.

---

**Note**: This is an active development project. The implementation is following a ship-fast, iterate approach with a focus on getting a working prototype quickly.
