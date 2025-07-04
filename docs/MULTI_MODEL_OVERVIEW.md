# Multi-Model Architecture Overview

The revamp introduces a set of separate models for groups of symbols with vastly different profit scales. Configuration is provided via `config/config.yaml` under a `models` section:

```yaml
models:
  SPX: models/spx_model.pkl
  NDX: models/ndx_model.pkl
  XSP: models/small_model.pkl
```

`prediction_api_realtime.py` automatically loads these models if the configuration is present and routes prediction requests based on the incoming symbol.

Use `symbol_analysis_report.py` to compute per-symbol profit statistics to help determine grouping strategies.
