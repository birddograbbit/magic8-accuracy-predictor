import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np

# Load the original data to analyze temporal patterns
print("Loading normalized data...")
df = pd.read_csv('data/normalized/normalized_aggregated.csv')

# Convert timestamp to datetime
df['datetime'] = pd.to_datetime(df['timestamp'])
df['date'] = df['datetime'].dt.date
df['year_month'] = df['datetime'].dt.to_period('M')

# Create win indicator (profit > 0)
df['win'] = (df['profit'] > 0).astype(int)

print(f"\nTotal records: {len(df):,}")
print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
print(f"Overall win rate: {df['win'].mean():.2%}")

# 1. Win rate by month
monthly_stats = df.groupby('year_month').agg({
    'win': ['count', 'sum', 'mean']
}).round(4)
monthly_stats.columns = ['total_trades', 'wins', 'win_rate']
monthly_stats = monthly_stats.reset_index()

print("\n=== Monthly Win Rates ===")
print(monthly_stats.to_string())

# 2. Visualize win rate over time
fig, axes = plt.subplots(3, 1, figsize=(12, 10))

# Plot 1: Win rate by month
axes[0].plot(monthly_stats.index, monthly_stats['win_rate'], marker='o')
axes[0].set_title('Win Rate by Month')
axes[0].set_ylabel('Win Rate')
axes[0].axhline(y=0.1468, color='r', linestyle='--', label='Overall avg')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Plot 2: Number of trades by month
axes[1].bar(monthly_stats.index, monthly_stats['total_trades'], alpha=0.7)
axes[1].set_title('Number of Trades by Month')
axes[1].set_ylabel('Trade Count')
axes[1].grid(True, alpha=0.3)

# Plot 3: Cumulative wins
df_sorted = df.sort_values('datetime')
df_sorted['cumulative_wins'] = df_sorted['win'].cumsum()
df_sorted['cumulative_trades'] = range(1, len(df_sorted) + 1)
df_sorted['cumulative_win_rate'] = df_sorted['cumulative_wins'] / df_sorted['cumulative_trades']

# Sample for plotting (every 10000th point)
sample_indices = range(0, len(df_sorted), 10000)
axes[2].plot(df_sorted.iloc[sample_indices]['datetime'], 
             df_sorted.iloc[sample_indices]['cumulative_win_rate'])
axes[2].set_title('Cumulative Win Rate Over Time')
axes[2].set_ylabel('Cumulative Win Rate')
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('reports/temporal_win_analysis.png', dpi=150)
print("\nSaved temporal analysis plot to reports/temporal_win_analysis.png")

# 3. Analyze where the 60/20/20 split would fall
total_trades = len(df_sorted)
train_end_idx = int(0.6 * total_trades)
val_end_idx = int(0.8 * total_trades)

train_end_date = df_sorted.iloc[train_end_idx]['datetime']
val_end_date = df_sorted.iloc[val_end_idx]['datetime']

print(f"\n=== Temporal Split Analysis ===")
print(f"60% split (train end): {train_end_date}")
print(f"80% split (val end): {val_end_date}")

# Check wins in each period
train_wins = df_sorted.iloc[:train_end_idx]['win'].sum()
val_wins = df_sorted.iloc[train_end_idx:val_end_idx]['win'].sum()
test_wins = df_sorted.iloc[val_end_idx:]['win'].sum()

print(f"\nWins by split:")
print(f"Train period (first 60%): {train_wins:,} wins")
print(f"Val period (60-80%): {val_wins:,} wins")
print(f"Test period (last 20%): {test_wins:,} wins")

# 4. Find when wins stopped
last_win_date = df_sorted[df_sorted['win'] == 1]['datetime'].max()
print(f"\n🚨 Last winning trade: {last_win_date}")
print(f"Days before data end: {(df_sorted['datetime'].max() - last_win_date).days}")

# 5. Strategy analysis
print("\n=== Win Rate by Strategy ===")
strategy_stats = df.groupby('strategy').agg({
    'win': ['count', 'sum', 'mean']
}).round(4)
strategy_stats.columns = ['total_trades', 'wins', 'win_rate']
print(strategy_stats)

# 6. Recent period analysis
recent_cutoff = pd.Timestamp('2024-01-01')
recent_df = df[df['datetime'] >= recent_cutoff]
print(f"\n=== Recent Period Analysis (since {recent_cutoff.date()}) ===")
print(f"Total trades: {len(recent_df):,}")
print(f"Wins: {recent_df['win'].sum():,}")
print(f"Win rate: {recent_df['win'].mean():.2%}")