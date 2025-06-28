# Magic8 Accuracy Predictor

A Transformer-based binary classification system to predict the accuracy (win/loss) of Magic8 trading system predictions.

## Overview

This project adapts a time-series Transformer architecture to predict whether Magic8's next option combo order will be profitable or not, based on:
- Historical Magic8 performance patterns
- Temporal features (time of day, day of month)
- Market conditions (VIX, stock price levels)
- Symbol-specific patterns

## Architecture

### Hybrid Approach
Based on research showing 15-35% performance improvement, we implement a hybrid architecture:
- **Transformer (70%)**: Captures temporal patterns in Magic8's historical performance
- **Decision Trees (30%)**: Handles market regime detection and rule-based features

### Key Features
- Binary classification (win/loss prediction)
- Symbol embeddings for multi-asset support
- Cyclical temporal encoding
- Real-time inference (<50ms)
- Class imbalance handling

## Project Structure

```
magic8-accuracy-predictor/
├── src/
│   ├── data/              # Data loading and preprocessing
│   ├── models/            # Transformer and hybrid models
│   ├── training/          # Training and optimization
│   └── inference/         # Real-time prediction
├── notebooks/             # Exploratory analysis
├── config/                # Configuration files
└── tests/                 # Unit tests
```

## Quick Start

### Installation
```bash
git clone https://github.com/birddograbbit/magic8-accuracy-predictor.git
cd magic8-accuracy-predictor
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Data Preparation
1. Place Magic8 historical data in `data/raw/magic8_trades.csv`
2. Ensure market data (VIX, stock prices) is available

### Training
```bash
python src/training/train.py --config config/default.yaml
```

### Inference
```bash
python src/inference/predict.py --symbol SPY --model checkpoints/best_model.pth
```

## Implementation Timeline

- **Week 1**: Data pipeline and feature engineering
- **Week 2**: Model architecture adaptation
- **Week 3**: Training and optimization
- **Week 4**: Integration and deployment

## Performance Targets

- Accuracy > 65%
- False Negative Rate < 30%
- Inference time < 50ms
- Consistent performance across market regimes

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
