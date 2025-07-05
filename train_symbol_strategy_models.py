#!/usr/bin/env python3
"""CLI tool to train symbol-strategy models."""

import argparse
from pathlib import Path
import pandas as pd

from src.models.symbol_strategy_trainer import SymbolStrategyModelTrainer
from src.models.xgboost_symbol_specific import prepare_symbol_data


def main(data_csv: str, output_dir: str, min_samples: int = 100):
    df = pd.read_csv(data_csv, low_memory=False)
    df, feature_cols = prepare_symbol_data(df)
    trainer = SymbolStrategyModelTrainer(min_samples=min_samples)
    trainer.train_all_models(df, feature_cols)
    trainer.save_models(Path(output_dir))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Train symbol-strategy models")
    p.add_argument("data_csv", help="Aggregated CSV file")
    p.add_argument("output_dir", help="Directory to save models")
    p.add_argument("--min_samples", type=int, default=100, help="Minimum samples required")
    args = p.parse_args()

    main(args.data_csv, args.output_dir, args.min_samples)
