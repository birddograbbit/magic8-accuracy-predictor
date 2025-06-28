"""
Data Preparation Script for Magic8 Accuracy Predictor

This script enhances the normalized trading data with additional features:
- VIX data from market
- Temporal features
- Technical indicators
- Market regime classification
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import ta
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import json
import os

class DataPreparation:
    def __init__(self, data_path='data/normalized/normalized_aggregated.csv'):
        self.data_path = data_path
        self.vix_data = None
        self.df = None
        
    def load_data(self):
        """Load the normalized aggregated data"""
        print("Loading normalized data...")
        self.df = pd.read_csv(self.data_path)
        self.df['interval_datetime'] = pd.to_datetime(self.df['interval_datetime'])
        self.df = self.df.sort_values('interval_datetime')
        print(f"Loaded {len(self.df)} records")
        return self
        
    def fetch_vix_data(self):
        """Fetch VIX data for the date range in our dataset"""
        print("Fetching VIX data...")
        start_date = self.df['interval_datetime'].min() - timedelta(days=1)
        end_date = self.df['interval_datetime'].max() + timedelta(days=1)
        
        # Fetch VIX data
        vix = yf.download('^VIX', start=start_date, end=end_date, interval='1h')
        
        # Resample to 5-minute intervals and forward fill
        vix_5min = vix.resample('5T').ffill()
        
        # Store for later use
        self.vix_data = vix_5min
        print(f"Fetched VIX data from {start_date} to {end_date}")
        return self
        
    def add_temporal_features(self):
        """Add time-based features with cyclical encoding"""
        print("Adding temporal features...")
        
        # Extract time components
        self.df['hour'] = self.df['interval_datetime'].dt.hour
        self.df['minute'] = self.df['interval_datetime'].dt.minute
        self.df['day_of_week'] = self.df['interval_datetime'].dt.dayofweek
        self.df['day_of_month'] = self.df['interval_datetime'].dt.day
        self.df['month'] = self.df['interval_datetime'].dt.month
        
        # Cyclical encoding for hour
        self.df['hour_sin'] = np.sin(2 * np.pi * self.df['hour'] / 24)
        self.df['hour_cos'] = np.cos(2 * np.pi * self.df['hour'] / 24)
        
        # Cyclical encoding for minute
        self.df['minute_sin'] = np.sin(2 * np.pi * self.df['minute'] / 60)
        self.df['minute_cos'] = np.cos(2 * np.pi * self.df['minute'] / 60)
        
        # Day of week encoding (cyclical)
        self.df['dow_sin'] = np.sin(2 * np.pi * self.df['day_of_week'] / 7)
        self.df['dow_cos'] = np.cos(2 * np.pi * self.df['day_of_week'] / 7)
        
        # Market hours indicator
        self.df['is_market_open'] = (
            (self.df['hour'] >= 9) & (self.df['hour'] < 16) &
            (self.df['day_of_week'] < 5)  # Monday = 0, Friday = 4
        ).astype(int)
        
        # First/last 30 minutes of trading
        self.df['is_market_open_30min'] = (
            ((self.df['hour'] == 9) & (self.df['minute'] >= 30)) |
            ((self.df['hour'] == 15) & (self.df['minute'] >= 30))
        ).astype(int)
        
        return self
        
    def add_technical_indicators(self):
        """Add technical indicators for each symbol"""
        print("Adding technical indicators...")
        
        # Get unique symbols
        symbols = ['SPX', 'SPY', 'XSP', 'NDX', 'QQQ', 'RUT']
        
        for symbol in symbols:
            # Price columns for this symbol
            price_col = f'pred_price'
            
            if price_col in self.df.columns:
                # Only calculate where we have price data
                mask = self.df[price_col].notna()
                
                # RSI
                if mask.sum() > 14:  # Need at least 14 periods for RSI
                    rsi_values = ta.momentum.RSIIndicator(
                        close=self.df.loc[mask, price_col], 
                        window=14
                    ).rsi()
                    self.df.loc[mask, f'{symbol}_rsi'] = rsi_values
                
                # Moving averages
                if mask.sum() > 5:
                    self.df.loc[mask, f'{symbol}_ma5'] = self.df.loc[mask, price_col].rolling(5).mean()
                if mask.sum() > 20:
                    self.df.loc[mask, f'{symbol}_ma20'] = self.df.loc[mask, price_col].rolling(20).mean()
                
                # Price momentum (rate of change)
                if mask.sum() > 5:
                    self.df.loc[mask, f'{symbol}_momentum'] = self.df.loc[mask, price_col].pct_change(5)
                
                # Volatility (rolling std)
                if mask.sum() > 20:
                    self.df.loc[mask, f'{symbol}_volatility'] = self.df.loc[mask, price_col].rolling(20).std()
        
        return self
        
    def merge_vix_data(self):
        """Merge VIX data with main dataframe"""
        print("Merging VIX data...")
        
        if self.vix_data is not None:
            # Align VIX data with our intervals
            vix_close = self.vix_data[['Close']].rename(columns={'Close': 'vix_close'})
            
            # Merge on datetime index
            self.df = self.df.set_index('interval_datetime')
            self.df = self.df.join(vix_close, how='left')
            
            # Forward fill VIX values
            self.df['vix_close'] = self.df['vix_close'].fillna(method='ffill')
            
            # Add VIX-based features
            self.df['vix_ma5'] = self.df['vix_close'].rolling(5).mean()
            self.df['vix_change'] = self.df['vix_close'].pct_change()
            
            # Market regime based on VIX
            self.df['market_regime'] = pd.cut(
                self.df['vix_close'],
                bins=[0, 15, 25, 100],
                labels=['low_vol', 'medium_vol', 'high_vol']
            )
            
            # One-hot encode market regime
            regime_dummies = pd.get_dummies(self.df['market_regime'], prefix='regime')
            self.df = pd.concat([self.df, regime_dummies], axis=1)
            
            # Reset index
            self.df = self.df.reset_index()
        
        return self
        
    def create_target_variable(self):
        """Create binary target variable from profit data"""
        print("Creating target variable...")
        
        # Primary target from trades data
        if 'trad_profited' in self.df.columns:
            self.df['target'] = self.df['trad_profited'].map({True: 1, False: 0})
        
        # Fill missing targets with profit data if available
        if 'prof_profit' in self.df.columns:
            profit_target = (self.df['prof_profit'] > 0).astype(int)
            self.df['target'] = self.df['target'].fillna(profit_target)
        
        print(f"Target distribution: {self.df['target'].value_counts().to_dict()}")
        return self
        
    def create_sequences(self, sequence_length=60, prediction_horizon=1):
        """Create sequences for time series modeling"""
        print(f"Creating sequences with length {sequence_length}...")
        
        # Select feature columns (exclude metadata and target)
        exclude_cols = ['interval_datetime', 'date', 'time_est', 'target', 
                       'file_types', 'record_count', 'market_regime']
        feature_cols = [col for col in self.df.columns if col not in exclude_cols]
        
        # Fill missing values
        self.df[feature_cols] = self.df[feature_cols].fillna(method='ffill').fillna(0)
        
        # Store feature names
        self.feature_names = feature_cols
        
        return self
        
    def split_data(self, test_size=0.2, val_size=0.2):
        """Split data temporally into train/val/test sets"""
        print("Splitting data into train/val/test sets...")
        
        # Remove rows without target
        valid_data = self.df[self.df['target'].notna()].copy()
        
        # Calculate split points
        n_samples = len(valid_data)
        train_end = int(n_samples * (1 - test_size - val_size))
        val_end = int(n_samples * (1 - test_size))
        
        # Split temporally
        train_data = valid_data.iloc[:train_end]
        val_data = valid_data.iloc[train_end:val_end]
        test_data = valid_data.iloc[val_end:]
        
        print(f"Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}")
        print(f"Train dates: {train_data['interval_datetime'].min()} to {train_data['interval_datetime'].max()}")
        print(f"Val dates: {val_data['interval_datetime'].min()} to {val_data['interval_datetime'].max()}")
        print(f"Test dates: {test_data['interval_datetime'].min()} to {test_data['interval_datetime'].max()}")
        
        # Save splits
        train_data.to_csv('data/processed/train_data.csv', index=False)
        val_data.to_csv('data/processed/val_data.csv', index=False)
        test_data.to_csv('data/processed/test_data.csv', index=False)
        
        # Save feature names and statistics
        stats = {
            'n_features': len(self.feature_names),
            'feature_names': self.feature_names,
            'train_samples': len(train_data),
            'val_samples': len(val_data),
            'test_samples': len(test_data),
            'class_distribution': {
                'train': train_data['target'].value_counts().to_dict(),
                'val': val_data['target'].value_counts().to_dict(),
                'test': test_data['target'].value_counts().to_dict()
            }
        }
        
        with open('data/processed/data_stats.json', 'w') as f:
            json.dump(stats, f, indent=2)
        
        return train_data, val_data, test_data
    
    def run_pipeline(self):
        """Run the complete data preparation pipeline"""
        # Create output directory
        os.makedirs('data/processed', exist_ok=True)
        
        # Run pipeline
        self.load_data()
        self.fetch_vix_data()
        self.add_temporal_features()
        self.add_technical_indicators()
        self.merge_vix_data()
        self.create_target_variable()
        self.create_sequences()
        train_data, val_data, test_data = self.split_data()
        
        print("\nData preparation complete!")
        return train_data, val_data, test_data


if __name__ == "__main__":
    # Run data preparation
    prep = DataPreparation()
    train_data, val_data, test_data = prep.run_pipeline()
