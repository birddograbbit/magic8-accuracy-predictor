import pandas as pd

class DeltaFeatureGenerator:
    """Generate delta-aware features from ShortTerm/LongTerm predictions."""

    def generate_delta_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate features from delta sheet data."""
        df = df.copy()

        # Basic delta features
        df['has_delta_data'] = (~df['short_term'].isna()).astype(int)

        # Short/Long term bias
        df['short_long_spread'] = df['short_term'] - df['long_term']
        df['short_long_ratio'] = df['short_term'] / df['long_term'].replace(0, 1)

        # Price vs predictions
        df['price_vs_short'] = (df['price'] - df['short_term']) / df['price'] * 100
        df['price_vs_long'] = (df['price'] - df['long_term']) / df['price'] * 100

        # Prediction alignment
        df['predicted_vs_short'] = df['predicted'] - df['short_term']
        df['predicted_vs_long'] = df['predicted'] - df['long_term']

        # Delta convergence
        df['delta_convergence'] = (df['short_term'] - df['long_term']).abs()

        # Directional agreement
        df['predictions_aligned'] = (
            (df['short_term'] > df['price']) == (df['long_term'] > df['price'])
        ).astype(int)

        return df
