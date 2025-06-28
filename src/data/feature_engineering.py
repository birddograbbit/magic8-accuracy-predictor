import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import ta


class FeatureEngineer:
    """Feature engineering for Magic8 accuracy prediction."""
    
    def __init__(self, lookback_periods: List[int] = [10, 20, 50]):
        self.lookback_periods = lookback_periods
        
    def create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create cyclical temporal features."""
        # Extract time components
        df['hour'] = df.index.hour
        df['minute'] = df.index.minute
        df['day'] = df.index.day
        df['month'] = df.index.month
        df['day_of_week'] = df.index.dayofweek
        
        # Cyclical encoding
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['minute_sin'] = np.sin(2 * np.pi * df['minute'] / 60)
        df['minute_cos'] = np.cos(2 * np.pi * df['minute'] / 60)
        df['day_sin'] = np.sin(2 * np.pi * df['day'] / 31)
        df['day_cos'] = np.cos(2 * np.pi * df['day'] / 31)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        return df
    
    def create_magic8_performance_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features based on Magic8's historical performance."""
        # Binary win/loss column
        df['win'] = (df['profit'] > 0).astype(int)
        
        for period in self.lookback_periods:
            # Win rate over different periods
            df[f'win_rate_{period}'] = df['win'].rolling(period, min_periods=1).mean()
            
            # Profit statistics
            df[f'profit_sum_{period}'] = df['profit'].rolling(period, min_periods=1).sum()
            df[f'profit_std_{period}'] = df['profit'].rolling(period, min_periods=1).std()
            
            # Consecutive wins/losses
            df[f'win_streak_{period}'] = self._calculate_streak(df['win'], period)
            
        # Time since last loss
        df['time_since_loss'] = self._time_since_event(df['win'] == 0)
        
        return df
    
    def create_market_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create market condition features."""
        # VIX features
        if 'vix' in df.columns:
            df['vix_percentile'] = df['vix'].rank(pct=True)
            df['vix_ma_ratio'] = df['vix'] / df['vix'].rolling(20).mean()
            df['vix_change'] = df['vix'].pct_change()
        
        # Price features
        if 'price' in df.columns:
            df['price_momentum_5'] = df['price'].pct_change(5)
            df['price_momentum_20'] = df['price'].pct_change(20)
            df['price_volatility'] = df['price'].pct_change().rolling(20).std()
            
            # Relative position
            df['price_position'] = (df['price'] - df['price'].rolling(20).min()) / \
                                  (df['price'].rolling(20).max() - df['price'].rolling(20).min())
        
        return df
    
    def _calculate_streak(self, series: pd.Series, max_period: int) -> pd.Series:
        """Calculate consecutive occurrences."""
        streak = series.groupby((series != series.shift()).cumsum()).cumcount() + 1
        return streak.clip(upper=max_period)
    
    def _time_since_event(self, event_series: pd.Series) -> pd.Series:
        """Calculate time since last occurrence of event."""
        last_event = event_series.where(event_series).last_valid_index()
        if last_event is None:
            return pd.Series(0, index=event_series.index)
        
        time_since = pd.Series(index=event_series.index, dtype=float)
        for i, idx in enumerate(event_series.index):
            last_event_idx = event_series[:idx][event_series[:idx]].index.max()
            if pd.notna(last_event_idx):
                time_since.iloc[i] = i - event_series.index.get_loc(last_event_idx)
            else:
                time_since.iloc[i] = i
                
        return time_since
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all feature engineering."""
        df = df.copy()
        
        # Create all feature groups
        df = self.create_temporal_features(df)
        df = self.create_magic8_performance_features(df)
        df = self.create_market_features(df)
        
        # Drop intermediate columns
        columns_to_drop = ['hour', 'minute', 'day', 'month', 'day_of_week']
        df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])
        
        return df
