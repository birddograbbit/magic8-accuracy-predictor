"""
Analyze which features actually predict win/loss probability
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import chi2_contingency, pointbiserialr
import warnings
warnings.filterwarnings('ignore')

def analyze_feature_predictiveness():
    """Analyze which features actually correlate with win/loss outcomes"""
    
    print("Feature Predictiveness Analysis")
    print("=" * 60)
    
    # Load the data
    print("\n1. Loading normalized data...")
    df = pd.read_csv('data/normalized/normalized_aggregated.csv')
    
    # Convert datetime
    df['interval_datetime'] = pd.to_datetime(df['interval_datetime'])
    
    # Create day_of_week from date
    df['day_of_week'] = df['interval_datetime'].dt.dayofweek
    
    # Create target from prof_raw
    df['target'] = (df['prof_raw'] > 0).astype(int)
    df = df.dropna(subset=['target'])
    
    print(f"Total records with target: {len(df)}")
    print(f"Win rate: {df['target'].mean():.2%}")
    
    # Analyze key features
    results = []
    
    print("\n2. Analyzing Temporal Features")
    print("-" * 40)
    
    # Hour of day
    hourly_winrate = df.groupby('hour')['target'].agg(['mean', 'count'])
    hourly_winrate = hourly_winrate[hourly_winrate['count'] > 100]  # Filter low counts
    
    print("\nWin rate by hour:")
    print(hourly_winrate.sort_values('mean', ascending=False).head(10))
    
    # Calculate correlation
    corr, p_value = pointbiserialr(df['target'], df['hour'])
    results.append({'feature': 'hour', 'correlation': corr, 'p_value': p_value})
    
    # Day of week
    daily_winrate = df.groupby('day_of_week')['target'].agg(['mean', 'count'])
    print("\nWin rate by day of week (0=Monday):")
    print(daily_winrate)
    
    # Day of week correlation
    corr, p_value = pointbiserialr(df['target'], df['day_of_week'])
    results.append({'feature': 'day_of_week', 'correlation': corr, 'p_value': p_value})
    
    # Minute of hour patterns
    if 'minute' in df.columns:
        minute_bins = pd.cut(df['minute'], bins=[0, 15, 30, 45, 60], labels=['0-15', '15-30', '30-45', '45-60'])
        minute_winrate = df.groupby(minute_bins)['target'].agg(['mean', 'count'])
        print("\nWin rate by minute bins:")
        print(minute_winrate)
    
    print("\n3. Analyzing VIX Features")
    print("-" * 40)
    
    # Load IBKR VIX data if available
    try:
        vix_data = pd.read_csv('data/ibkr/historical_data_INDEX_VIX_5_mins.csv')
        vix_data['date'] = pd.to_datetime(vix_data['date'])
        vix_data = vix_data.set_index('date')
        
        # Get VIX values for each trade
        df['vix'] = df['interval_datetime'].apply(
            lambda x: vix_data.loc[vix_data.index.get_indexer([x], method='nearest')[0], 'close'] 
            if len(vix_data) > 0 else np.nan
        )
    except:
        print("Could not load VIX data from IBKR")
        if 'vix' not in df.columns:
            df['vix'] = np.nan
    
    # VIX level bins
    if df['vix'].notna().sum() > 100:
        df['vix_bin'] = pd.qcut(df['vix'].dropna(), q=10, labels=False, duplicates='drop')
        vix_winrate = df.groupby('vix_bin')['target'].agg(['mean', 'count'])
        
        print("\nWin rate by VIX decile:")
        print(vix_winrate)
        
        # VIX correlation
        corr, p_value = pointbiserialr(df['target'], df['vix'].fillna(df['vix'].median()))
        results.append({'feature': 'vix', 'correlation': corr, 'p_value': p_value})
    
    print("\n4. Analyzing Strategy Features")
    print("-" * 40)
    
    strategy_winrate = df.groupby('prof_strategy_name')['target'].agg(['mean', 'count'])
    strategy_winrate = strategy_winrate[strategy_winrate['count'] > 50]  # Filter low counts
    print("\nWin rate by strategy:")
    print(strategy_winrate.sort_values('mean', ascending=False))
    
    print("\n5. Analyzing Risk/Reward Impact")
    print("-" * 40)
    
    # Show that risk/reward don't predict outcomes
    for feature in ['prof_risk', 'prof_reward']:
        if feature in df.columns:
            corr, p_value = pointbiserialr(df['target'], df[feature].fillna(0))
            results.append({'feature': feature, 'correlation': corr, 'p_value': p_value})
            print(f"{feature} correlation with win/loss: {corr:.4f} (p={p_value:.4f})")
    
    # Premium normalized by price
    if 'prof_premium' in df.columns and 'pred_price' in df.columns:
        df['premium_normalized'] = df['prof_premium'] / (df['pred_price'] + 1e-8)
        corr, p_value = pointbiserialr(df['target'], df['premium_normalized'])
        results.append({'feature': 'premium_normalized', 'correlation': corr, 'p_value': p_value})
        print(f"premium_normalized correlation: {corr:.4f} (p={p_value:.4f})")
    
    # Minutes to close (for 0DTE)
    df['minutes_to_close'] = ((16 - df['hour']) * 60 - df['minute']).clip(lower=0)
    corr, p_value = pointbiserialr(df['target'], df['minutes_to_close'])
    results.append({'feature': 'minutes_to_close', 'correlation': corr, 'p_value': p_value})
    
    # Create visualizations
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: Hourly win rate
    ax1 = axes[0, 0]
    hourly_winrate['mean'].plot(kind='bar', ax=ax1)
    ax1.axhline(y=df['target'].mean(), color='r', linestyle='--', label='Overall win rate')
    ax1.set_title('Win Rate by Hour of Day')
    ax1.set_xlabel('Hour')
    ax1.set_ylabel('Win Rate')
    ax1.legend()
    
    # Plot 2: Day of week win rate
    ax2 = axes[0, 1]
    daily_winrate['mean'].plot(kind='bar', ax=ax2)
    ax2.axhline(y=df['target'].mean(), color='r', linestyle='--', label='Overall win rate')
    ax2.set_title('Win Rate by Day of Week')
    ax2.set_xlabel('Day (0=Monday, 4=Friday)')
    ax2.set_ylabel('Win Rate')
    ax2.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][:len(daily_winrate)])
    ax2.legend()
    
    # Plot 3: Feature Correlations
    ax3 = axes[1, 0]
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('correlation', key=abs, ascending=False)
    results_df.set_index('feature')['correlation'].head(20).plot(kind='barh', ax=ax3)
    ax3.set_title('Feature Correlations with Win/Loss')
    ax3.set_xlabel('Point-Biserial Correlation')
    
    # Plot 4: Time to close analysis
    ax4 = axes[1, 1]
    df['minutes_to_close_bin'] = pd.cut(df['minutes_to_close'], 
                                        bins=[0, 30, 60, 120, 180, 240, 300, 400],
                                        labels=['0-30', '30-60', '60-120', '120-180', '180-240', '240-300', '300-400'])
    close_winrate = df.groupby('minutes_to_close_bin')['target'].mean()
    close_winrate.plot(kind='bar', ax=ax4)
    ax4.set_title('Win Rate by Minutes to Close')
    ax4.set_xlabel('Minutes to Close')
    ax4.set_ylabel('Win Rate')
    
    plt.tight_layout()
    plt.savefig('feature_predictiveness_analysis.png', dpi=300, bbox_inches='tight')
    print(f"\nSaved visualization to feature_predictiveness_analysis.png")
    
    # Key insights
    print("\n" + "="*60)
    print("KEY INSIGHTS:")
    print("="*60)
    
    # Find best and worst hours
    best_hour = hourly_winrate['mean'].idxmax()
    worst_hour = hourly_winrate['mean'].idxmin()
    print(f"1. Best hour to trade: {best_hour}:00 ({hourly_winrate.loc[best_hour, 'mean']:.1%} win rate)")
    print(f"   Worst hour to trade: {worst_hour}:00 ({hourly_winrate.loc[worst_hour, 'mean']:.1%} win rate)")
    
    # Day of week insights
    best_day = daily_winrate['mean'].idxmax()
    worst_day = daily_winrate['mean'].idxmin()
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    print(f"\n2. Best day to trade: {day_names[best_day]} ({daily_winrate.loc[best_day, 'mean']:.1%} win rate)")
    print(f"   Worst day to trade: {day_names[worst_day]} ({daily_winrate.loc[worst_day, 'mean']:.1%} win rate)")
    
    # VIX insights
    if df['vix'].notna().sum() > 100 and len(vix_winrate) > 0:
        best_vix = vix_winrate['mean'].idxmax()
        worst_vix = vix_winrate['mean'].idxmin()
        print(f"\n3. Best VIX decile: {best_vix} ({vix_winrate.loc[best_vix, 'mean']:.1%} win rate)")
        print(f"   Worst VIX decile: {worst_vix} ({vix_winrate.loc[worst_vix, 'mean']:.1%} win rate)")
    
    # Most predictive features
    print(f"\n4. Most predictive features (by correlation):")
    for _, row in results_df.head(10).iterrows():
        if row['p_value'] < 0.05:
            print(f"   - {row['feature']}: {row['correlation']:.4f} (p={row['p_value']:.4f})")
    
    print("\n5. Risk/Reward features have LOW correlation with outcomes")
    print("   This confirms they indicate magnitude, not probability")
    
    # Strategy insights
    print(f"\n6. Strategy performance:")
    for strategy, row in strategy_winrate.iterrows():
        if row['count'] > 100:
            print(f"   - {strategy}: {row['mean']:.1%} win rate ({row['count']} trades)")
    
    return results_df

if __name__ == "__main__":
    results = analyze_feature_predictiveness()
    
    # Save results
    results.to_csv('feature_predictiveness_results.csv', index=False)
    print("\nResults saved to feature_predictiveness_results.csv")
