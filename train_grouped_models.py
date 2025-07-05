#!/usr/bin/env python3
"""Train grouped models for symbol clusters."""
from pathlib import Path
import argparse
from src.models.xgboost_symbol_specific import train_grouped_models


def main():
    parser = argparse.ArgumentParser(description="Train grouped models")
    parser.add_argument("data_dir", help="Directory with *_trades.csv files")
    parser.add_argument("output_dir", help="Directory to store grouped models")
    parser.add_argument("feature_info", help="JSON with feature info", nargs="?")
    args = parser.parse_args()

    # Define default groups
    groups = {
        "SPX_SPY": ["SPX", "SPY"],
        "QQQ_AAPL_TSLA": ["QQQ", "AAPL", "TSLA"],
    }

    train_grouped_models(groups, args.data_dir, args.output_dir, Path(args.feature_info) if args.feature_info else None)


if __name__ == "__main__":
    main()
