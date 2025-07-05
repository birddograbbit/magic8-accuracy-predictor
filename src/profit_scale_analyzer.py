"""Analyze profit scales per symbol-strategy combination."""

from typing import Dict
import pandas as pd


class ProfitScaleAnalyzer:
    """Analyze profit ranges and recommend model groupings."""

    def analyze_by_strategy(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Return stats for each symbol-strategy combination."""
        results: Dict[str, Dict] = {}
        symbols = df['symbol'].unique()
        strategies = df['strategy'].unique()

        for symbol in symbols:
            for strategy in strategies:
                mask = (df['symbol'] == symbol) & (df['strategy'] == strategy)
                strategy_df = df[mask]
                if len(strategy_df) == 0:
                    continue
                key = f"{symbol}_{strategy}"
                results[key] = {
                    'count': len(strategy_df),
                    'avg_profit': strategy_df['profit'].mean(),
                    'min_profit': strategy_df['profit'].min(),
                    'max_profit': strategy_df['profit'].max(),
                    'std_profit': strategy_df['profit'].std(),
                    'profit_range': strategy_df['profit'].max() - strategy_df['profit'].min(),
                }
        return results

    def recommend_groupings(self, analysis: Dict[str, Dict]) -> Dict[str, list]:
        """Categorize symbol-strategy keys by profit range magnitude."""
        groupings = {
            'large_scale': [],  # > $1000 range
            'medium_scale': [],  # $100-1000 range
            'small_scale': [],  # < $100 range
        }

        for key, stats in analysis.items():
            if stats['profit_range'] > 1000:
                groupings['large_scale'].append(key)
            elif stats['profit_range'] > 100:
                groupings['medium_scale'].append(key)
            else:
                groupings['small_scale'].append(key)

        return groupings
