#!/usr/bin/env python3
"""Run profit scale analysis for symbol-strategy combinations."""

import json
import os
import argparse
import pandas as pd
from src.profit_scale_analyzer import ProfitScaleAnalyzer


def main(input_file: str, output_dir: str):
    df = pd.read_csv(input_file, low_memory=False)
    os.makedirs(output_dir, exist_ok=True)
    analyzer = ProfitScaleAnalyzer()
    analysis = analyzer.analyze_by_strategy(df)
    groupings = analyzer.recommend_groupings(analysis)

    with open(os.path.join(output_dir, "profit_scale_stats.json"), "w") as f:
        json.dump(analysis, f, indent=2)

    with open(os.path.join(output_dir, "profit_scale_groups.json"), "w") as f:
        json.dump(groupings, f, indent=2)

    return analysis, groupings


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Analyze profit scales by strategy")
    p.add_argument("input_file", help="CSV with complete trade data")
    p.add_argument("output_dir", help="Directory for output JSON")
    args = p.parse_args()

    analysis, groups = main(args.input_file, args.output_dir)
    print(json.dumps(groups, indent=2))
