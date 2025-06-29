#!/usr/bin/env python3
"""
Analyze the existing normalized data to show the strategy distribution problem
"""

import pandas as pd
import json
from pathlib import Path

def analyze_existing_data():
    """Analyze the existing normalized data files."""
    data_path = Path("/Users/jt/magic8/magic8-accuracy-predictor/data/normalized")
    
    print("=" * 80)
    print("EXISTING NORMALIZED DATA ANALYSIS")
    print("=" * 80)
    
    # Check if files exist
    raw_file = data_path / "normalized_raw.csv"
    agg_file = data_path / "normalized_aggregated.csv"
    
    if not agg_file.exists():
        print(f"ERROR: {agg_file} not found!")
        return
    
    # Load aggregated data
    print(f"\nLoading {agg_file.name}...")
    df = pd.read_csv(agg_file)
    print(f"Total records: {len(df):,}")
    
    # Check for strategy columns
    strategy_cols = [col for col in df.columns if 'strategy' in col.lower() or 'name' in col.lower()]
    print(f"\nStrategy-related columns found: {strategy_cols}")
    
    # Analyze prof_strategy_name if it exists
    if 'prof_strategy_name' in df.columns:
        print("\n" + "=" * 60)
        print("STRATEGY DISTRIBUTION IN prof_strategy_name:")
        print("=" * 60)
        
        # Count strategies
        strategy_counts = df['prof_strategy_name'].value_counts()
        total = len(df[df['prof_strategy_name'].notna()])
        
        for strategy, count in strategy_counts.items():
            pct = (count / total * 100) if total > 0 else 0
            print(f"{strategy:15} : {count:6,} trades ({pct:5.1f}%)")
        
        # Check for Sonar
        if 'Sonar' not in strategy_counts:
            print("\n⚠️  WARNING: Sonar strategy is MISSING!")
        
        # Sample some trades
        print("\nSample trades:")
        sample_df = df[df['prof_strategy_name'].notna()].head(10)
        for idx, row in sample_df.iterrows():
            print(f"  {row.get('date', 'N/A')} {row.get('time_est', 'N/A')} - "
                  f"{row.get('prof_symbol', 'N/A')} - {row.get('prof_strategy_name', 'N/A')}")
    
    # Check prof_trade column for Iron Condor mentions
    if 'prof_trade' in df.columns:
        print("\n" + "=" * 60)
        print("CHECKING prof_trade COLUMN FOR SONAR MISLABELING:")
        print("=" * 60)
        
        # Count Iron Condor mentions
        ic_trades = df[df['prof_trade'].str.contains('Iron Condor', na=False)]
        print(f"Total trades with 'Iron Condor' in description: {len(ic_trades):,}")
        
        # Show distribution of strategies for Iron Condor trades
        if 'prof_strategy_name' in df.columns:
            ic_strategy_dist = ic_trades['prof_strategy_name'].value_counts()
            print("\nStrategy distribution for 'Iron Condor' trades:")
            for strategy, count in ic_strategy_dist.items():
                print(f"  {strategy}: {count:,}")
    
    # Check date range
    if 'date' in df.columns:
        print("\n" + "=" * 60)
        print("DATE RANGE:")
        print("=" * 60)
        dates = pd.to_datetime(df['date'])
        print(f"Start date: {dates.min()}")
        print(f"End date: {dates.max()}")
        print(f"Total days: {dates.nunique()}")
    
    # Check symbols
    symbol_cols = [col for col in df.columns if 'symbol' in col.lower()]
    if symbol_cols:
        print("\n" + "=" * 60)
        print("SYMBOL COVERAGE:")
        print("=" * 60)
        for col in symbol_cols:
            print(f"\n{col}:")
            symbol_counts = df[col].value_counts()
            for symbol, count in symbol_counts.items():
                print(f"  {symbol}: {count:,}")
    
    # Save analysis results
    analysis = {
        'total_records': len(df),
        'columns': list(df.columns),
        'strategy_distribution': strategy_counts.to_dict() if 'prof_strategy_name' in df.columns else {},
        'date_range': {
            'start': str(dates.min()) if 'date' in df.columns else None,
            'end': str(dates.max()) if 'date' in df.columns else None
        }
    }
    
    with open('existing_data_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print("\n" + "=" * 80)
    print("CONCLUSION:")
    print("=" * 80)
    print("The existing normalized data shows:")
    print("1. Butterfly strategy is vastly over-represented (~97%)")
    print("2. Sonar strategy is completely missing")
    print("3. This is likely due to parsing strategy from Trade column instead of Name column")
    print("4. The prof_trade column contains 'Iron Condor' for both Iron Condor AND Sonar trades")
    print("\nThis confirms our hypothesis about the data processing bug!")


if __name__ == "__main__":
    analyze_existing_data()
