#!/usr/bin/env python3
"""
Check the strategy distribution in the optimized processed data
"""

import pandas as pd
import json
from pathlib import Path

def check_optimized_data():
    """Check the newly processed optimized data."""
    print("Checking Optimized Data Processing Results")
    print("=" * 80)
    
    # Check if optimized data exists
    optimized_path = Path('data/processed_optimized/magic8_trades_complete.csv')
    if not optimized_path.exists():
        print(f"ERROR: Optimized data not found at {optimized_path}")
        print("Please run: ./run_data_processing_optimized.sh")
        return
    
    # Load the data
    print(f"\nLoading {optimized_path}...")
    df = pd.read_csv(optimized_path)
    print(f"Total records: {len(df):,}")
    
    # Check columns
    print(f"\nColumns in dataset: {list(df.columns)}")
    
    # Strategy distribution
    print("\nStrategy Distribution:")
    print("-" * 40)
    strategy_counts = df['strategy'].value_counts()
    strategy_pcts = (df['strategy'].value_counts() / len(df) * 100).round(2)
    
    for strategy in strategy_counts.index:
        count = strategy_counts[strategy]
        pct = strategy_pcts[strategy]
        print(f"{strategy:15}: {count:,} trades ({pct}%)")
    
    # Check for any null strategies
    null_strategies = df['strategy'].isna().sum()
    if null_strategies > 0:
        print(f"\n⚠️  WARNING: {null_strategies:,} trades with null strategy")
    
    # Symbol distribution
    print("\nSymbol Distribution:")
    print("-" * 40)
    symbol_counts = df['symbol'].value_counts()
    for symbol in symbol_counts.index:
        count = symbol_counts[symbol]
        pct = (count / len(df) * 100).round(2)
        print(f"{symbol:6}: {count:,} trades ({pct}%)")
    
    # Date range
    print("\nDate Range:")
    print("-" * 40)
    df['datetime'] = pd.to_datetime(df['timestamp'])
    print(f"Start: {df['datetime'].min()}")
    print(f"End:   {df['datetime'].max()}")
    print(f"Days:  {(df['datetime'].max() - df['datetime'].min()).days}")
    
    # Sample of data
    print("\nSample of trades:")
    print("-" * 40)
    sample_cols = ['date', 'time', 'symbol', 'strategy', 'premium', 'profit']
    available_cols = [col for col in sample_cols if col in df.columns]
    print(df[available_cols].head(10).to_string(index=False))
    
    # Load and display JSON reports
    print("\n" + "=" * 80)
    print("ANALYSIS REPORTS")
    print("=" * 80)
    
    # Strategy analysis
    strategy_file = Path('data/processed_optimized/strategy_analysis.json')
    if strategy_file.exists():
        with open(strategy_file, 'r') as f:
            strategy_data = json.load(f)
        print("\nStrategy Analysis Summary:")
        print(f"Total trades: {strategy_data['total_trades']:,}")
        for strategy, pct in strategy_data['by_strategy_pct'].items():
            count = strategy_data['by_strategy'][strategy]
            print(f"  {strategy}: {count:,} ({pct}%)")
    
    # Data quality report
    quality_file = Path('data/processed_optimized/data_quality_report.json')
    if quality_file.exists():
        with open(quality_file, 'r') as f:
            quality_data = json.load(f)
        print("\nData Quality Summary:")
        for issue, count in quality_data['summary'].items():
            if count > 0:
                print(f"  {issue}: {count}")
    
    # Processing stats
    stats_file = Path('data/processed_optimized/processing_stats.json')
    if stats_file.exists():
        with open(stats_file, 'r') as f:
            stats_data = json.load(f)
        print("\nProcessing Performance:")
        print(f"  Total time: {stats_data['total_processing_time_minutes']:.1f} minutes")
        print(f"  Folders processed: {stats_data['folders_processed']}")
        print(f"  Average per folder: {stats_data['average_time_per_folder_seconds']:.1f} seconds")
        print(f"  Timestamp success rate: {stats_data['success_rate']}%")

if __name__ == "__main__":
    check_optimized_data()
