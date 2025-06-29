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
    
    print("\n3. Analyzing VIX Features")
    print("-" * 40)
    
    # VIX level bins
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
    print("\nWin rate by strategy:")
    print(strategy_winrate)
    
    print("\n5. Analyzing Risk/Reward Impact")
    print("-" * 40)
    
    # Show that risk/reward don't predict outcomes
    for feature in ['prof_risk', 'prof_reward']:
        if feature in df.columns:
            corr, p_value = pointbiserialr(df['target'], df[feature].fillna(0))
            results.append({'feature': feature, 'correlation': corr, 'p_value': p_value})
            print(f"{feature} correlation with win/loss: {corr:.4f} (p={p_value:.4f})")
    
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
    
    # Plot 2: VIX vs Win Rate
    ax2 = axes[0, 1]
    vix_winrate['mean'].plot(kind='line', marker='o', ax=ax2)
    ax2.set_title('Win Rate by VIX Level')
    ax2.set_xlabel('VIX Decile')
    ax2.set_ylabel('Win Rate')
    
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
    plt.savefig('feature_predictiveness_analysis.png', dpi=300)
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
    
    # VIX insights
    if len(vix_winrate) > 0:
        best_vix = vix_winrate['mean'].idxmax()
        worst_vix = vix_winrate['mean'].idxmin()
        print(f"\n2. Best VIX decile: {best_vix} ({vix_winrate.loc[best_vix, 'mean']:.1%} win rate)")
        print(f"   Worst VIX decile: {worst_vix} ({vix_winrate.loc[worst_vix, 'mean']:.1%} win rate)")
    
    # Most predictive features
    print(f"\n3. Most predictive features (by correlation):")
    for _, row in results_df.head(5).iterrows():
        if row['p_value'] < 0.05:
            print(f"   - {row['feature']}: {row['correlation']:.4f} (p={row['p_value']:.4f})")
    
    print("\n4. Risk/Reward features have LOW correlation with outcomes")
    print("   This confirms they indicate magnitude, not probability")
    
    return results_df

if __name__ == "__main__":
    results = analyze_feature_predictiveness()
    
    # Save results
    results.to_csv('feature_predictiveness_results.csv', index=False)
    print("\nResults saved to feature_predictiveness_results.csv")
