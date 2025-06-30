import pandas as pd
import numpy as np

# Check the raw data to understand the profit issue
print("Analyzing profit calculation issue...")
df = pd.read_csv('data/normalized/normalized_aggregated.csv')
df['datetime'] = pd.to_datetime(df['timestamp'])

# Sample data from both periods
print("\n=== GOLDEN PERIOD SAMPLE (Working) ===")
golden_sample = df[df['datetime'] < '2023-11-11'].head(10)
print(golden_sample[['datetime', 'strategy', 'profit', 'closed', 'expired', 'premium', 'risk', 'reward']].to_string())

print("\n=== FAILURE PERIOD SAMPLE (Broken) ===")
failure_sample = df[df['datetime'] >= '2023-11-13'].head(10)
print(failure_sample[['datetime', 'strategy', 'profit', 'closed', 'expired', 'premium', 'risk', 'reward']].to_string())

# Check data types
print("\n=== DATA TYPES ===")
print(df[['profit', 'closed', 'expired', 'premium', 'risk', 'reward']].dtypes)

# Check for different source file formats
print("\n=== SOURCE FILE ANALYSIS ===")
source_counts = df.groupby('source_file')['datetime'].agg(['min', 'max', 'count'])
print(source_counts)

# Check if 'expired' field contains the actual profit after Nov 2023
print("\n=== CHECKING 'EXPIRED' FIELD ===")
recent = df[df['datetime'] >= '2023-11-13']
expired_stats = recent['expired'].describe()
print(f"Expired field stats (recent):\n{expired_stats}")

# Sample non-zero expired values
non_zero_expired = recent[recent['expired'] != 0].head(20)
print("\nSample trades with non-zero 'expired' values:")
print(non_zero_expired[['datetime', 'strategy', 'profit', 'expired', 'premium', 'closed']].to_string())

# Check if we can calculate profit from other fields
print("\n=== ATTEMPTING PROFIT RECONSTRUCTION ===")
# For credit strategies (Iron Condor, Vertical), profit might be:
# If closed < predicted: profit = premium
# If closed > predicted: profit = -risk

sample_trades = recent.head(100)
sample_trades['reconstructed_profit'] = np.where(
    sample_trades['strategy'].isin(['Iron Condor', 'Vertical']),
    np.where(sample_trades['closed'] < sample_trades['predicted'], 
             sample_trades['premium'], 
             -sample_trades['risk']),
    np.nan  # Need different logic for other strategies
)

print("\nSample profit reconstruction:")
print(sample_trades[['strategy', 'profit', 'reconstructed_profit', 'premium', 'risk', 'closed', 'predicted']].head(20))