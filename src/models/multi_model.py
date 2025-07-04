"""Utilities for training and using multiple models by symbol group."""
from pathlib import Path
import joblib
from typing import Dict, List

class SymbolModelStrategy:
    """Define mapping from symbols to model paths."""

    def __init__(self, mapping: Dict[str, str]):
        self.mapping = mapping

    def get_model_path(self, symbol: str) -> str:
        return self.mapping.get(symbol)

class MultiModelPredictor:
    """Load and route predictions to symbol specific models."""

    def __init__(self, strategy: SymbolModelStrategy):
        self.strategy = strategy
        self.models: Dict[str, object] = {}

    def load_models(self):
        for sym, path in self.strategy.mapping.items():
            if path and Path(path).exists():
                self.models[sym] = joblib.load(path)

    def predict_proba(self, symbol: str, features):
        model = self.models.get(symbol)
        if model is None:
            raise ValueError(f"No model for symbol {symbol}")
        return model.predict_proba(features)
