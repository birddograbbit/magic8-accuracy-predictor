"""Utilities for training and using multiple models by symbol group."""
from pathlib import Path
import joblib
import xgboost as xgb
from typing import Dict, List

class SymbolModelStrategy:
    """Define mapping from symbols to model paths."""

    def __init__(self, mapping: Dict[str, str]):
        self.mapping = mapping
        self.default = mapping.get('default')

    def get_model_path(self, symbol: str) -> str:
        return self.mapping.get(symbol)

class MultiModelPredictor:
    """Load and route predictions to symbol specific models."""

    def __init__(self, strategy: SymbolModelStrategy, model_routing: Dict | None = None):
        self.strategy = strategy
        self.models: Dict[str, object] = {}
        self.model_routing = model_routing or {}
        
    def load_models(self):
        def _load(p: str):
            fp = Path(p)
            if fp.suffix == ".json":
                booster = xgb.Booster()
                booster.load_model(str(fp))
                return booster
            try:
                booster = xgb.Booster()
                booster.load_model(str(fp))
                return booster
            except Exception:
                return joblib.load(fp)

        for sym, path in self.strategy.mapping.items():
            if sym == 'default':
                continue
            if path and Path(path).exists():
                self.models[sym] = _load(path)
        if self.strategy.default and Path(self.strategy.default).exists():
            self.default_model = _load(self.strategy.default)
        else:
            self.default_model = None

    def predict_proba(self, symbol: str, features):
        """Route to appropriate model with grouped and default fallback."""
        # direct individual model
        model = self.models.get(symbol)
        if model:
            return model.predict_proba(features)

        # grouped routing
        group_map = self.model_routing.get('use_grouped', {})
        if symbol in group_map:
            group_name = group_map[symbol]
            group_model = self.models.get(group_name)
            if group_model:
                return group_model.predict_proba(features)

        # default fallback
        if self.default_model is None:
            raise ValueError(f"No model available for symbol {symbol}")
        return self.default_model.predict_proba(features)
