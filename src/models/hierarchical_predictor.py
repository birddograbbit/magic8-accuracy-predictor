"""Prediction helper that cascades through multiple model levels."""

from __future__ import annotations

from pathlib import Path
import joblib
from typing import Dict


class HierarchicalPredictor:
    """Predict using symbol-strategy models with fallbacks."""

    def __init__(
        self,
        symbol_strategy_paths: Dict[str, str] | None = None,
        symbol_paths: Dict[str, str] | None = None,
        strategy_paths: Dict[str, str] | None = None,
        default_path: str | None = None,
    ) -> None:
        self.symbol_strategy_models: Dict[str, object] = {}
        self.symbol_models: Dict[str, object] = {}
        self.strategy_models: Dict[str, object] = {}
        self.default_model = None

        if symbol_strategy_paths:
            for key, p in symbol_strategy_paths.items():
                if p and Path(p).exists():
                    self.symbol_strategy_models[key] = joblib.load(p)

        if symbol_paths:
            for key, p in symbol_paths.items():
                if p and Path(p).exists():
                    self.symbol_models[key] = joblib.load(p)

        if strategy_paths:
            for key, p in strategy_paths.items():
                if p and Path(p).exists():
                    self.strategy_models[key] = joblib.load(p)

        if default_path and Path(default_path).exists():
            self.default_model = joblib.load(default_path)

    def predict_proba(self, symbol: str, strategy: str, features):
        """Return probability using available models with fallback."""
        key = f"{symbol}_{strategy}"
        if key in self.symbol_strategy_models:
            return self.symbol_strategy_models[key].predict_proba(features)

        if symbol in self.symbol_models:
            return self.symbol_models[symbol].predict_proba(features)

        if strategy in self.strategy_models:
            return self.strategy_models[strategy].predict_proba(features)

        if self.default_model:
            return self.default_model.predict_proba(features)

        raise ValueError(f"No model available for {symbol} {strategy}")
