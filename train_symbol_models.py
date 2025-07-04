#!/usr/bin/env python3
"""CLI tool to train symbol-specific XGBoost models."""
from pathlib import Path
import argparse

from src.models.xgboost_symbol_specific import train_all_models


def main():
    parser = argparse.ArgumentParser(description="Train symbol specific models")
    parser.add_argument("data_dir", help="Directory with *_trades.csv files")
    parser.add_argument("output_dir", help="Directory to store models")
    parser.add_argument("feature_info", help="JSON with feature names")
    args = parser.parse_args()

    train_all_models(args.data_dir, args.output_dir, Path(args.feature_info))


if __name__ == "__main__":
    main()
