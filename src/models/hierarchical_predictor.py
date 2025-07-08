"""Prediction helper that cascades through multiple model levels."""

from __future__ import annotations

from pathlib import Path
import joblib
import xgboost as xgb
from typing import Dict
import logging
import numpy as np

logger = logging.getLogger(__name__)


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

        def _load(path: str):
            p = Path(path)
            if p.suffix == ".json":
                booster = xgb.Booster()
                booster.load_model(str(p))
                return booster
            try:
                booster = xgb.Booster()
                booster.load_model(str(p))
                return booster
            except Exception:
                return joblib.load(p)

        if symbol_strategy_paths:
            for key, p in symbol_strategy_paths.items():
                if p and Path(p).exists():
                    self.symbol_strategy_models[key] = _load(p)

        if symbol_paths:
            for key, p in symbol_paths.items():
                if p and Path(p).exists():
                    self.symbol_models[key] = _load(p)

        if strategy_paths:
            for key, p in strategy_paths.items():
                if p and Path(p).exists():
                    self.strategy_models[key] = _load(p)

        if default_path and Path(default_path).exists():
            self.default_model = _load(default_path)

    def predict_proba(self, symbol: str, strategy: str, features):
        """Return probability using available models with fallback."""
        key = f"{symbol}_{strategy}"

        def _align(model, feats: np.ndarray) -> np.ndarray:
            expected = None
            if hasattr(model, "n_features_in_"):
                expected = int(model.n_features_in_)
            elif hasattr(model, "get_booster"):
                booster = model.get_booster()
                num = booster.attr("num_feature")
                if num is not None:
                    expected = int(num)

            if expected is None:
                return feats

            current = feats.shape[1]
            if current > expected:
                logger.warning(
                    f"Feature mismatch for {key}: model expects {expected}, got {current}. Using first {expected} features."
                )
                return feats[:, :expected]
            if current < expected:
                raise ValueError(
                    f"Model for {key} expects {expected} features, got {current}"
                )
            return feats

        if key in self.symbol_strategy_models:
            aligned = _align(self.symbol_strategy_models[key], features)
            return self.symbol_strategy_models[key].predict_proba(aligned)

        if symbol in self.symbol_models:
            aligned = _align(self.symbol_models[symbol], features)
            return self.symbol_models[symbol].predict_proba(aligned)

        if strategy in self.strategy_models:
            aligned = _align(self.strategy_models[strategy], features)
            return self.strategy_models[strategy].predict_proba(aligned)

        if self.default_model:
            aligned = _align(self.default_model, features)
            return self.default_model.predict_proba(aligned)

        raise ValueError(f"No model available for {symbol} {strategy}")
