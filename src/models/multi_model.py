"""Utilities for training and using multiple models by symbol group."""
from pathlib import Path
import joblib
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

    def __init__(self, strategy: SymbolModelStrategy):
        self.strategy = strategy
        self.models: Dict[str, object] = {}

    def load_models(self):
        for sym, path in self.strategy.mapping.items():
            if sym == 'default':
                continue
            if path and Path(path).exists():
                self.models[sym] = joblib.load(path)
        if self.strategy.default and Path(self.strategy.default).exists():
            self.default_model = joblib.load(self.strategy.default)
        else:
            self.default_model = None

    def predict_proba(self, symbol: str, features):
        model = self.models.get(symbol)
        if model is None:
            if self.default_model is None:
                raise ValueError(f"No model for symbol {symbol}")
            model = self.default_model
        return model.predict_proba(features)
