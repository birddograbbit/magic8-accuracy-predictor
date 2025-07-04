"""Magic8 specific feature engineering utilities."""
from typing import List
import pandas as pd

class SymbolNormalizer:
    """Normalize numeric features per symbol."""

    def __init__(self, symbol_stats: pd.DataFrame):
        self.stats = symbol_stats.set_index('symbol')

    def transform(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        df = df.copy()
        for symbol, group in df.groupby('symbol'):
            if symbol in self.stats.index:
                mean = self.stats.loc[symbol, 'mean']
                std = self.stats.loc[symbol, 'std']
                df.loc[group.index, columns] = (group[columns] - mean) / (std + 1e-9)
        return df

class Magic8FeatureEngineer:
    """Generate advanced features from strike and delta information."""

    def __init__(self):
        pass

    def add_strike_features(self, df: pd.DataFrame) -> pd.DataFrame:
        # Placeholder for strike structure features
        strike_cols = ['strike1', 'strike2', 'strike3', 'strike4']
        if all(col in df.columns for col in strike_cols):
            df['strike_distance_pct'] = (df['strike4'] - df['strike1']) / df['strike1'].abs()
        return df

    def add_delta_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'call_delta' in df.columns and 'put_delta' in df.columns:
            df['delta_diff'] = df['call_delta'] - df['put_delta']
        return df

    def engineer(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.add_strike_features(df)
        df = self.add_delta_features(df)
        return df
