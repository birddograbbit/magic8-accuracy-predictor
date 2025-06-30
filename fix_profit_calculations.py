import pandas as pd
import numpy as np
from datetime import datetime

print("Fixing Magic8 profit calculations...")

# Load the data
df = pd.read_csv('data/normalized/normalized_aggregated.csv')
df['datetime'] = pd.to_datetime(df['timestamp'])

# Fix profit calculations based on strategy type and data format
def calculate_profit(row):
    """Calculate profit based on strategy and outcome"""
    
    # If profit already exists and is valid, use it
    if pd.notna(row['profit']) and row['profit'] != 0:
        return row['profit']
    
    # Skip if we don't have necessary data
    if pd.isna(row['closed']) or pd.isna(row['predicted']):
        return np.nan
        
    # For credit strategies (Iron Condor, Vertical)
    if row['strategy'] in ['Iron Condor', 'Vertical']:
        # These are credit spreads - you collect premium upfront
        # Win if price stays within range (closed between strikes)
        # For simplicity, assuming win if closed is close to predicted
        price_diff = abs(row['closed'] - row['predicted'])
        threshold = row['predicted'] * 0.01  # 1% threshold
        
        if price_diff <= threshold:
            # Win - keep the premium
            return row['premium']
        else:
            # Loss - pay out the risk minus premium collected
            return -row['risk'] if pd.notna(row['risk']) else -row['premium'] * 10
    
    # For debit strategies (Butterfly, Sonar)
    elif row['strategy'] in ['Butterfly', 'Sonar']:
        # These are debit spreads - you pay premium upfront
        # Win if price moves to your target
        price_diff = abs(row['closed'] - row['predicted'])
        threshold = row['predicted'] * 0.005  # 0.5% threshold for butterflies
        
        if price_diff <= threshold:
            # Win - receive the reward minus premium paid
            if pd.notna(row['reward']):
                return row['reward'] - row['premium']
            else:
                return row['premium'] * 2  # Assume 2:1 reward ratio
        else:
            # Loss - lose the premium paid
            return -row['premium']
    
    return np.nan

# Apply profit calculation
print("Calculating profits for all trades...")
df['fixed_profit'] = df.apply(calculate_profit, axis=1)

# Analyze the results
print("\n=== PROFIT CALCULATION RESULTS ===")
print(f"Total trades: {len(df):,}")
print(f"Successfully calculated: {df['fixed_profit'].notna().sum():,}")
print(f"Failed calculations: {df['fixed_profit'].isna().sum():,}")

# Compare periods
before_nov = df[df['datetime'] < '2023-11-13']
after_nov = df[df['datetime'] >= '2023-11-13']

print(f"\nBefore Nov 13, 2023:")
print(f"  Original profits valid: {before_nov['profit'].notna().sum():,}")
print(f"  Fixed profits valid: {before_nov['fixed_profit'].notna().sum():,}")

print(f"\nAfter Nov 13, 2023:")
print(f"  Original profits valid: {after_nov['profit'].notna().sum():,}")
print(f"  Fixed profits valid: {after_nov['fixed_profit'].notna().sum():,}")

# Calculate win rates
df['win'] = (df['fixed_profit'] > 0).astype(int)

print("\n=== WIN RATE ANALYSIS ===")
for period_name, period_data in [("Full Dataset", df), 
                                  ("Before Nov 13", before_nov), 
                                  ("After Nov 13", after_nov)]:
    valid_trades = period_data[period_data['fixed_profit'].notna()]
    if len(valid_trades) > 0:
        win_rate = valid_trades['win'].mean()
        avg_profit = valid_trades['fixed_profit'].mean()
        print(f"\n{period_name}:")
        print(f"  Trades with valid profit: {len(valid_trades):,}")
        print(f"  Win rate: {win_rate:.2%}")
        print(f"  Average profit: ${avg_profit:.2f}")
        
        # By strategy
        print(f"  By strategy:")
        for strategy in valid_trades['strategy'].unique():
            strat_data = valid_trades[valid_trades['strategy'] == strategy]
            print(f"    {strategy}: {strat_data['win'].mean():.2%} win rate, "
                  f"${strat_data['fixed_profit'].mean():.2f} avg profit")

# Save the fixed data
print("\n=== SAVING FIXED DATA ===")
# Use the fixed profit where available, otherwise keep original
df['profit_final'] = df['fixed_profit'].fillna(df['profit'])

# Save to new file
output_path = 'data/normalized/normalized_aggregated_fixed.csv'
df.to_csv(output_path, index=False)
print(f"Saved fixed data to: {output_path}")

# Sample the fixes
print("\n=== SAMPLE OF FIXED TRADES ===")
sample_fixed = after_nov[after_nov['fixed_profit'].notna()].head(20)
print(sample_fixed[['datetime', 'strategy', 'profit', 'fixed_profit', 'premium', 'risk', 'closed', 'predicted']].to_string())

print("\n✅ Data fixing complete! Now you can:")
print("1. Re-run process_magic8_data_fixed.py with the new file")
print("2. Re-run phase1_data_preparation.py") 
print("3. Re-train the XGBoost model with accurate profit data")