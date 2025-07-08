"""Train XGBoost models for each symbol-strategy combination."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier

logger = logging.getLogger(__name__)


class SymbolStrategyModelTrainer:
    """Train dedicated models for each symbol-strategy pair."""

    def __init__(self, min_samples: int = 100):
        self.min_samples = min_samples
        self.models: Dict[str, Dict] = {}

    def train_all_models(self, df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, Dict]:
        """Train models and return metadata."""
        symbols = df['symbol'].unique()
        strategies = df['strategy'].unique()

        for symbol in symbols:
            for strategy in strategies:
                mask = (df['symbol'] == symbol) & (df['strategy'] == strategy)
                strat_df = df[mask]
                if len(strat_df) < self.min_samples:
                    logger.warning(
                        "Insufficient data for %s_%s: %d samples",
                        symbol,
                        strategy,
                        len(strat_df),
                    )
                    continue

                model_key = f"{symbol}_{strategy}"
                logger.info("Training model for %s: %d samples", model_key, len(strat_df))

                X = strat_df[feature_cols]
                if 'target' not in strat_df.columns:
                    raise ValueError("Missing 'target' column in training data")
                y = strat_df['target']
                if y.isna().all():
                    raise ValueError(
                        f"Target column for {model_key} contains only NaN values"
                    )

                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42, stratify=y
                )

                model = XGBClassifier(
                    n_estimators=200,
                    max_depth=4,
                    learning_rate=0.1,
                    random_state=42,
                )
                model.fit(X_train, y_train)

                y_pred = model.predict(X_test)
                accuracy = accuracy_score(y_test, y_pred)

                self.models[model_key] = {
                    'model': model,
                    'accuracy': accuracy,
                    'samples': len(strat_df),
                    'features': feature_cols,
                }

                logger.info("  Accuracy: %.4f", accuracy)

        return self.models

    def save_models(self, out_dir: Path):
        """Save trained models to directory."""
        out_dir.mkdir(parents=True, exist_ok=True)
        for key, info in self.models.items():
            model_path = out_dir / f"{key}_model.json"
            feature_path = out_dir / f"{key}_features.pkl"
            info['model'].get_booster().save_model(str(model_path))
            joblib.dump(info['features'], feature_path)
            info['model_path'] = str(model_path)
            info['feature_path'] = str(feature_path)


def load_data(csv_path: Path) -> pd.DataFrame:
    """Load CSV helper."""
    return pd.read_csv(csv_path, low_memory=False)

