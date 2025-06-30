import pandas as pd
import numpy as np
from datetime import datetime

print("Loading data for diagnostic analysis...")
df = pd.read_csv('data/normalized/normalized_aggregated.csv')
df['datetime'] = pd.to_datetime(df['timestamp'])

# Define periods
golden_period = df[df['datetime'] < '2023-11-11']
failure_period = df[df['datetime'] >= '2023-11-11']

print(f"\n=== PERIOD COMPARISON ===")
print(f"Golden Period: {golden_period['datetime'].min()} to {golden_period['datetime'].max()}")
print(f"  Trades: {len(golden_period):,}")
print(f"  Win rate: {(golden_period['profit'] > 0).mean():.2%}")

print(f"\nFailure Period: {failure_period['datetime'].min()} to {failure_period['datetime'].max()}")
print(f"  Trades: {len(failure_period):,}")
print(f"  Win rate: {(failure_period['profit'] > 0).mean():.2%}")

# Check if trades are being closed
print(f"\n=== TRADE CLOSURE STATUS ===")
print("Golden Period:")
print(golden_period['closed'].value_counts())
print("\nFailure Period:")
print(failure_period['closed'].value_counts())

# Check profit distributions
print(f"\n=== PROFIT ANALYSIS ===")
print(f"Golden Period profits: ${golden_period['profit'].min():.2f} to ${golden_period['profit'].max():.2f}")
print(f"  Mean: ${golden_period['profit'].mean():.2f}")
print(f"  Median: ${golden_period['profit'].median():.2f}")
print(f"  Std: ${golden_period['profit'].std():.2f}")

print(f"\nFailure Period profits: ${failure_period['profit'].min():.2f} to ${failure_period['profit'].max():.2f}")
print(f"  Mean: ${failure_period['profit'].mean():.2f}")
print(f"  Median: ${failure_period['profit'].median():.2f}")
print(f"  Std: ${failure_period['profit'].std():.2f}")

# Check for any positive profits in failure period
positive_profits = failure_period[failure_period['profit'] > 0]
print(f"\n=== POSITIVE PROFITS IN FAILURE PERIOD ===")
print(f"Count: {len(positive_profits)}")
if len(positive_profits) > 0:
    print("Sample trades with positive profit:")
    print(positive_profits[['datetime', 'strategy', 'profit', 'premium', 'risk']].head(10))

# Strategy performance comparison
print(f"\n=== STRATEGY PERFORMANCE ===")
for strategy in df['strategy'].unique():
    golden_strat = golden_period[golden_period['strategy'] == strategy]
    failure_strat = failure_period[failure_period['strategy'] == strategy]
    
    print(f"\n{strategy}:")
    print(f"  Golden: {len(golden_strat):,} trades, {(golden_strat['profit'] > 0).mean():.2%} win rate")
    print(f"  Failure: {len(failure_strat):,} trades, {(failure_strat['profit'] > 0).mean():.2%} win rate")

# Check premium and risk values
print(f"\n=== PREMIUM/RISK ANALYSIS ===")
print("Golden Period:")
print(f"  Premium: ${golden_period['premium'].mean():.2f} (avg)")
print(f"  Risk: ${golden_period['risk'].mean():.2f} (avg)")
print(f"  Risk/Reward Ratio: {golden_period['ratio'].mean():.2f}")

print("\nFailure Period:")
print(f"  Premium: ${failure_period['premium'].mean():.2f} (avg)")
print(f"  Risk: ${failure_period['risk'].mean():.2f} (avg)")
print(f"  Risk/Reward Ratio: {failure_period['ratio'].mean():.2f}")

# Look for the transition period
print(f"\n=== NOVEMBER 2023 TRANSITION ===")
nov_2023 = df[(df['datetime'] >= '2023-11-01') & (df['datetime'] < '2023-12-01')]
nov_2023['win'] = (nov_2023['profit'] > 0).astype(int)

# Group by day to see the transition
daily_stats = nov_2023.groupby(nov_2023['datetime'].dt.date).agg({
    'profit': ['count', 'mean', 'min', 'max'],
    'win': 'sum'
})
daily_stats.columns = ['trades', 'avg_profit', 'min_profit', 'max_profit', 'wins']
print(daily_stats.tail(15))  # Show last 15 days of November

# Sample trades from the last winning day
last_win_date = df[df['profit'] > 0]['datetime'].dt.date.max()
last_win_trades = df[(df['datetime'].dt.date == last_win_date) & (df['profit'] > 0)]
print(f"\n=== LAST WINNING DAY ({last_win_date}) ===")
print(f"Total wins: {len(last_win_trades)}")
print("\nSample winning trades:")
print(last_win_trades[['datetime', 'strategy', 'symbol', 'profit', 'premium', 'closed']].head(10))