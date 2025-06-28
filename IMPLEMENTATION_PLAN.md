# Magic8 Accuracy Predictor - Implementation Plan

## Executive Summary
This document outlines the implementation plan for building a Transformer-based system to predict the accuracy (win/loss) of Magic8's trading predictions. The system will use historical trading data combined with market indicators to provide binary classification predictions.

## Architecture Overview

### 1. Data Pipeline
- **Input Features**: Time features, Symbol, VIX, Stock price levels, Technical indicators
- **Output**: Binary classification (1=profit, 0=loss)
- **Data Source**: 3 years of normalized trading data (2022-2025)

### 2. Model Architecture
We will adapt the **QuantStock** framework (https://github.com/MXGao-A/QuantStock) which provides:
- Production-ready implementation
- Multiple model architectures (Transformer, LSTM, XGBoost)
- Comprehensive backtesting framework
- Modular design for easy customization

### 3. Ensemble Approach
- **Decision Tree**: Market regime classification based on VIX levels
- **Transformer**: Sequential pattern recognition
- **XGBoost**: Feature importance and non-linear relationships
- **Voting Mechanism**: Weighted ensemble based on validation performance

## Implementation Phases

### Phase 1: Data Enhancement (3-4 days)

#### 1.1 Feature Engineering
```python
# New features to add:
- VIX data (fetch from yfinance)
- Temporal features:
  - hour_sin = sin(2π * hour/24)
  - hour_cos = cos(2π * hour/24)
  - day_of_week (one-hot encoded)
  - day_of_month
  - is_market_open_hour
- Technical indicators:
  - RSI (14-period)
  - Moving averages (5, 20 periods)
  - Volatility (rolling std)
  - Price momentum
- Market regime:
  - VIX < 15: Low volatility
  - VIX 15-25: Medium volatility
  - VIX > 25: High volatility
```

#### 1.2 Data Preparation Script
Create `src/data_preparation.py`:
- Load normalized_aggregated.csv
- Fetch and merge VIX data
- Calculate technical indicators
- Create sliding windows for sequences
- Handle class imbalance
- Split data temporally (60/20/20)

### Phase 2: Model Development (1 week)

#### 2.1 Fork and Adapt QuantStock
1. Fork repository to `magic8-accuracy-predictor`
2. Create custom modules:
   - `src/models/BinaryTransformer.py`
   - `src/data/Magic8DataLoader.py`
   - `src/ensemble/EnsemblePredictor.py`

#### 2.2 Model Modifications
```python
# Key changes for binary classification:
1. Output layer: nn.Linear(hidden_dim, 1) + nn.Sigmoid()
2. Loss function: nn.BCEWithLogitsLoss()
3. Metrics: Accuracy, Precision, Recall, F1, AUC-ROC
4. Class weighting for imbalanced data
```

#### 2.3 Training Pipeline
- Implement k-fold cross-validation
- Early stopping based on validation loss
- Learning rate scheduling
- Hyperparameter tuning with Optuna

### Phase 3: Production Deployment (3-4 days)

#### 3.1 API Service
```python
# FastAPI structure:
/predict - Real-time prediction endpoint
/batch_predict - Batch predictions
/model/reload - Reload model weights
/health - Health check
```

#### 3.2 Infrastructure
- Docker containerization
- Redis for caching
- PostgreSQL for storing predictions
- MLflow for experiment tracking

## File Structure
```
magic8-accuracy-predictor/
├── src/
│   ├── data/
│   │   ├── data_preparation.py
│   │   ├── feature_engineering.py
│   │   └── Magic8DataLoader.py
│   ├── models/
│   │   ├── BinaryTransformer.py
│   │   ├── DecisionTreeRegime.py
│   │   └── XGBoostClassifier.py
│   ├── ensemble/
│   │   └── EnsemblePredictor.py
│   ├── api/
│   │   ├── main.py
│   │   └── predictor_service.py
│   └── utils/
│       ├── metrics.py
│       └── visualization.py
├── configs/
│   ├── model_config.yaml
│   └── training_config.yaml
├── notebooks/
│   ├── data_exploration.ipynb
│   └── model_evaluation.ipynb
├── tests/
├── docker/
│   └── Dockerfile
└── requirements.txt
```

## Key Metrics to Track
1. **Classification Metrics**:
   - Accuracy, Precision, Recall, F1-score
   - AUC-ROC curve
   - Confusion matrix

2. **Trading Metrics**:
   - Profit factor (gross profit / gross loss)
   - Win rate
   - Average win/loss ratio
   - Maximum drawdown

3. **Model Performance**:
   - Training/validation loss curves
   - Feature importance
   - Prediction confidence distribution

## Risk Management
1. **Overfitting Prevention**:
   - Dropout layers
   - L2 regularization
   - Data augmentation
   - Cross-validation

2. **Production Safeguards**:
   - Confidence threshold for predictions
   - Fallback to ensemble average
   - Real-time performance monitoring
   - A/B testing for model updates

## Timeline
- **Week 1**: Data preparation and feature engineering
- **Week 2**: Model development and training
- **Week 3**: Production deployment and testing
- **Week 4**: Performance monitoring and optimization

## Success Criteria
1. Model accuracy > 65% on test set
2. Consistent performance across different market regimes
3. Real-time prediction latency < 100ms
4. System uptime > 99.9%

## Next Steps
1. Set up development environment
2. Install QuantStock framework
3. Create feature engineering pipeline
4. Begin model development

## References
- QuantStock: https://github.com/MXGao-A/QuantStock
- Original Transformer Trading Code: Provided in attached notebook
- yfinance: For VIX data fetching
- ta library: For technical indicators
