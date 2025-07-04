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

    def create_prediction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate features from Magic8 prediction indicators."""
        # Price target distances
        if {'target1', 'price'}.issubset(df.columns):
            df['distance_to_target1'] = (df['target1'] - df['price']) / df['price']
        if {'target2', 'price'}.issubset(df.columns):
            df['distance_to_target2'] = (df['target2'] - df['price']) / df['price']
        if {'target1', 'target2', 'price'}.issubset(df.columns):
            df['targets_spread'] = (df['target1'] - df['target2']).abs() / df['price']

        # Prediction alignment
        if {'predicted_trades', 'price'}.issubset(df.columns):
            df['predicted_vs_price'] = (df['predicted_trades'] - df['price']) / df['price']
        if {'predicted_trades', 'closing'}.issubset(df.columns):
            df['predicted_vs_closing'] = (
                df['predicted_trades'] - df['closing']
            ) / df['predicted_trades'].replace(0, 1e-9)

        # Delta relationships
        if {'call_delta', 'put_delta'}.issubset(df.columns):
            df['call_put_delta_spread'] = df['call_delta'] - df['put_delta']
            if 'price' in df.columns:
                df['delta_skew'] = df['call_put_delta_spread'] / df['price']

        # Short/long term bias
        if {'short_term', 'price'}.issubset(df.columns):
            df['short_term_bias'] = (df['short_term'] - df['price']) / df['price']
        if {'long_term', 'price'}.issubset(df.columns):
            df['long_term_bias'] = (df['long_term'] - df['price']) / df['price']
        if {'short_term', 'long_term'}.issubset(df.columns):
            df['term_structure'] = df['short_term'] - df['long_term']

        # Expected move utilisation
        if {'high', 'low', 'expected_move'}.issubset(df.columns):
            df['strike_width_ratio'] = (df['high'] - df['low']) / df['expected_move'].replace(0, 1e-9)

        return df

    def add_strike_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features describing the strike layout."""
        strike_cols = ['strike1', 'strike2', 'strike3', 'strike4']
        if all(col in df.columns for col in strike_cols):
            df['strike_distance_pct'] = (df['strike4'] - df['strike1']) / (df['strike1'].abs() + 1e-9)
            df['avg_strike'] = df[strike_cols].mean(axis=1)
            df['strike_width'] = df['strike4'] - df['strike1']
        return df

    def add_delta_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'call_delta' in df.columns and 'put_delta' in df.columns:
            df['delta_diff'] = df['call_delta'] - df['put_delta']
        if 'predicted_delta' in df.columns:
            df['delta_error'] = df['predicted_delta'] - df[['call_delta', 'put_delta']].mean(axis=1)
        if 'short_term' in df.columns and 'long_term' in df.columns:
            df['term_structure'] = df['short_term'] - df['long_term']
        return df

    def add_microstructure_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add simple market microstructure features from bid/ask prices."""
        if 'bid1' in df.columns and 'ask1' in df.columns:
            df['spread1'] = df['ask1'] - df['bid1']
        if 'bid2' in df.columns and 'ask2' in df.columns:
            df['spread2'] = df['ask2'] - df['bid2']
        return df

    def engineer(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.create_prediction_features(df)
        df = self.add_strike_features(df)
        df = self.add_delta_features(df)
        df = self.add_microstructure_features(df)
        return df
