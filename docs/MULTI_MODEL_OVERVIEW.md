# Multi-Model Architecture Overview

The revamp introduces a set of separate models for groups of symbols with vastly different profit scales. Configuration is provided via `config/config.yaml` under a `models` section:

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

`prediction_api_realtime.py` automatically loads these models if the configuration is present and routes prediction requests based on the incoming symbol.

The real-time feature generator now includes Magic8 delta predictions (`short_term` and `long_term`). These values are passed through the API request and converted into derived features such as `short_long_spread` and `price_vs_short` to align with the training data.

Use `symbol_analysis_report.py` to compute per-symbol profit statistics to help determine grouping strategies.
