#!/usr/bin/env python3
"""Split aggregated data into symbol-specific files and compute stats."""
import os
import json
import pandas as pd
from typing import Dict


def split_data_by_symbol(input_file: str, output_dir: str) -> Dict:
    """Split aggregated data into per-symbol CSVs and return statistics."""
    # Read with low_memory=False to avoid DtypeWarning
    df = pd.read_csv(input_file, low_memory=False)
    
    # Convert numeric columns that might have mixed types
    numeric_columns = ['price', 'premium', 'predicted', 'closed', 'expired', 
                      'risk', 'reward', 'ratio', 'profit',
                      'expected_move', 'low', 'high', 'target1', 'target2',
                      'predicted_trades', 'closing',
                      'strike1', 'strike2', 'strike3', 'strike4',
                      'bid1', 'ask1', 'bid2', 'ask2', 'bid3', 'ask3', 'bid4', 'ask4',
                      'mid1', 'mid2', 'mid3', 'mid4',
                      'call_delta', 'put_delta', 'predicted_delta',
                      'short_term', 'long_term', 'closing_delta']
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    symbols = df['symbol'].unique()
    os.makedirs(output_dir, exist_ok=True)

    symbol_stats = {}
    for symbol in symbols:
        symbol_df = df[df['symbol'] == symbol]
        output_file = os.path.join(output_dir, f"{symbol}_trades.csv")
        symbol_df.to_csv(output_file, index=False)

        symbol_stats[symbol] = {
            'total_trades': len(symbol_df),
            'strategies': symbol_df['strategy'].value_counts().to_dict(),
            'avg_profit': float(symbol_df['profit'].mean()) if 'profit' in symbol_df.columns else 0,
            'profit_by_strategy': {}
        }

        for strategy in ['Butterfly', 'Iron Condor', 'Sonar', 'Vertical']:
            strat_df = symbol_df[symbol_df['strategy'] == strategy]
            if len(strat_df) == 0:
                continue
            symbol_stats[symbol]['profit_by_strategy'][strategy] = {
                'count': len(strat_df),
                'avg_profit': float(strat_df['profit'].mean()),
                'win_rate': float((strat_df['profit'] > 0).mean()),
                'avg_win': float(strat_df[strat_df['profit'] > 0]['profit'].mean()) if any(strat_df['profit'] > 0) else 0,
                'avg_loss': float(strat_df[strat_df['profit'] <= 0]['profit'].mean()) if any(strat_df['profit'] <= 0) else 0
            }

    with open(os.path.join(output_dir, 'symbol_statistics.json'), 'w') as f:
        json.dump(symbol_stats, f, indent=2)

    return symbol_stats


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Split aggregated trades by symbol")
    parser.add_argument("input_file", help="Path to aggregated CSV")
    parser.add_argument("output_dir", help="Directory to write symbol files")
    args = parser.parse_args()

    stats = split_data_by_symbol(args.input_file, args.output_dir)
    print(json.dumps(stats, indent=2))
