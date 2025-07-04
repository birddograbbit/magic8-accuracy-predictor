#!/usr/bin/env python3
"""Generate per-symbol profit scale report."""
import pandas as pd
import json
import os
from typing import Dict


def generate_symbol_report(input_file: str, output_dir: str) -> Dict:
    df = pd.read_csv(input_file)
    os.makedirs(output_dir, exist_ok=True)
    report = {}

    for symbol in df['symbol'].unique():
        symbol_df = df[df['symbol'] == symbol]
        wins = symbol_df[symbol_df['profit'] > 0]
        losses = symbol_df[symbol_df['profit'] <= 0]
        avg_win = wins['profit'].mean() if len(wins) > 0 else 0
        avg_loss = losses['profit'].mean() if len(losses) > 0 else 0
        report[symbol] = {
            'total_trades': len(symbol_df),
            'avg_profit': symbol_df['profit'].mean(),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
        }

    # Calculate relative scale difference using average win amounts
    wins = [v['avg_win'] for v in report.values() if v['avg_win']]
    if wins:
        max_win = max(wins)
        min_win = min(wins)
        report['scale_ratio'] = round(max_win / min_win, 2) if min_win else None
    else:
        report['scale_ratio'] = None

    out_file = os.path.join(output_dir, 'symbol_profit_report.json')
    with open(out_file, 'w') as f:
        json.dump(report, f, indent=2)
    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Compute symbol profit statistics')
    parser.add_argument('input_file', help='Aggregated CSV file')
    parser.add_argument('output_dir', help='Directory for output JSON')
    args = parser.parse_args()
    result = generate_symbol_report(args.input_file, args.output_dir)
    print(json.dumps(result, indent=2))
