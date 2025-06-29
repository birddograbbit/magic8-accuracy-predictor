"""
Data Preparation Script for Magic8 Accuracy Predictor

This script enhances the normalized trading data with additional features:
- VIX and VVIX data from market
- Temporal features with 0DTE-specific indicators
- Technical indicators for all symbols including AAPL and TSLA
- Market regime classification
- Cross-asset correlations
- Option-specific features
- Strategy encoding
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import ta
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import json
import os
import warnings
warnings.filterwarnings('ignore')

class DataPreparation:
    def __init__(self, data_path='data/normalized/normalized_aggregated.csv'):
        self.data_path = data_path
        self.vix_data = None
        self.vvix_data = None
        self.cross_asset_data = {}
        self.df = None
        
        # All symbols traded by Magic8
        self.symbols = ['SPX', 'SPY', 'XSP', 'NDX', 'QQQ', 'RUT', 'AAPL', 'TSLA']
        
        # Trading strategies
        self.strategies = ['Butterfly', 'Iron Condor', 'Vertical Spread']
        
    def load_data(self):
        """Load the normalized aggregated data"""
        print("Loading normalized data...")
        self.df = pd.read_csv(self.data_path)
        self.df['interval_datetime'] = pd.to_datetime(self.df['interval_datetime'])
        self.df = self.df.sort_values('interval_datetime')
        print(f"Loaded {len(self.df)} records")
        return self
        
    def fetch_market_data(self):
        """Fetch VIX, VVIX, and cross-asset data"""
        print("Fetching market data...")
        start_date = self.df['interval_datetime'].min() - timedelta(days=30)  # Extra days for indicators
        end_date = self.df['interval_datetime'].max() + timedelta(days=1)
        
        # Fetch VIX data
        vix = yf.download('^VIX', start=start_date, end=end_date, interval='5m')
        self.vix_data = vix.resample('5T').ffill()
        
        # Fetch VVIX data (volatility of VIX)
        try:
            vvix = yf.download('^VVIX', start=start_date, end=end_date, interval='1h')
            self.vvix_data = vvix.resample('5T').ffill()
        except:
            print("VVIX data not available, creating synthetic VVIX from VIX volatility")
            self.vvix_data = None
        
        # Fetch cross-asset data
        cross_assets = {
            'DXY': 'DX-Y.NYB',  # Dollar Index
            'TY': 'ZN=F',       # 10-Year Treasury futures
            'TU': 'ZT=F',       # 2-Year Treasury futures
            'XLF': 'XLF',       # Financial sector ETF
            'XLK': 'XLK',       # Technology sector ETF
            'ES': 'ES=F',       # S&P 500 futures
            'NQ': 'NQ=F'        # NASDAQ futures
        }
        
        for name, ticker in cross_assets.items():
            try:
                data = yf.download(ticker, start=start_date, end=end_date, interval='5m')
                self.cross_asset_data[name] = data.resample('5T').ffill()
                print(f"Fetched {name} data")
            except:
                print(f"Could not fetch {name} data")
                
        print(f"Fetched VIX data from {start_date} to {end_date}")
        return self
        
    def add_temporal_features(self):
        """Add time-based features with cyclical encoding and 0DTE-specific features"""
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
        
        # First/last 30 minutes of trading (high volatility periods)
        self.df['is_market_open_30min'] = (
            ((self.df['hour'] == 9) & (self.df['minute'] >= 30)) |
            ((self.df['hour'] == 15) & (self.df['minute'] >= 30))
        ).astype(int)
        
        # Power hour indicator (last hour of trading)
        self.df['is_power_hour'] = (
            (self.df['hour'] == 15) & (self.df['is_market_open'] == 1)
        ).astype(int)
        
        # Lunch hour indicator (typically lower volatility)
        self.df['is_lunch_hour'] = (
            (self.df['hour'] >= 12) & (self.df['hour'] < 13) & 
            (self.df['is_market_open'] == 1)
        ).astype(int)
        
        # Minutes to market close (critical for 0DTE theta decay)
        self.df['minutes_to_close'] = 0
        market_open_mask = self.df['is_market_open'] == 1
        self.df.loc[market_open_mask, 'minutes_to_close'] = (
            (16 - self.df.loc[market_open_mask, 'hour']) * 60 - 
            self.df.loc[market_open_mask, 'minute']
        )
        
        # Time decay factor (exponential decay for 0DTE)
        self.df['time_decay_factor'] = np.exp(-self.df['minutes_to_close'] / 390)  # 390 minutes in trading day
        
        # Options expiration effects
        self.df['is_monthly_opex'] = (
            (self.df['day_of_week'] == 4) &  # Friday
            (self.df['day_of_month'] >= 15) & (self.df['day_of_month'] <= 21)
        ).astype(int)
        
        # Quarter end effects
        self.df['is_quarter_end'] = (
            self.df['month'].isin([3, 6, 9, 12]) & 
            (self.df['day_of_month'] >= 25)
        ).astype(int)
        
        return self
        
    def add_technical_indicators(self):
        """Add technical indicators for each symbol"""
        print("Adding technical indicators...")
        
        for symbol in self.symbols:
            # Check if we have price data for this symbol
            symbol_mask = self.df['pred_symbol'] == symbol
            
            if symbol_mask.sum() > 0:
                # Get price data for this symbol
                symbol_data = self.df[symbol_mask].copy()
                price_col = 'pred_price'
                
                if price_col in symbol_data.columns and symbol_data[price_col].notna().sum() > 0:
                    # RSI
                    if len(symbol_data) > 14:
                        rsi = ta.momentum.RSIIndicator(
                            close=symbol_data[price_col], 
                            window=14
                        ).rsi()
                        self.df.loc[symbol_mask, f'{symbol}_rsi'] = rsi
                    
                    # Moving averages
                    for period in [5, 10, 20, 50]:
                        if len(symbol_data) > period:
                            ma = symbol_data[price_col].rolling(period).mean()
                            self.df.loc[symbol_mask, f'{symbol}_ma{period}'] = ma
                    
                    # Price momentum (rate of change)
                    for period in [5, 10]:
                        if len(symbol_data) > period:
                            momentum = symbol_data[price_col].pct_change(period)
                            self.df.loc[symbol_mask, f'{symbol}_momentum{period}'] = momentum
                    
                    # Volatility (rolling std)
                    for period in [10, 20]:
                        if len(symbol_data) > period:
                            volatility = symbol_data[price_col].rolling(period).std()
                            self.df.loc[symbol_mask, f'{symbol}_volatility{period}'] = volatility
                    
                    # ATR (Average True Range)
                    if 'pred_long_term' in symbol_data.columns and 'pred_short_term' in symbol_data.columns:
                        high = symbol_data[['pred_price', 'pred_long_term']].max(axis=1)
                        low = symbol_data[['pred_price', 'pred_short_term']].min(axis=1)
                        atr = ta.volatility.AverageTrueRange(
                            high=high, low=low, close=symbol_data[price_col], window=14
                        ).average_true_range()
                        self.df.loc[symbol_mask, f'{symbol}_atr'] = atr
                    
                    # Bollinger Bands
                    if len(symbol_data) > 20:
                        bb = ta.volatility.BollingerBands(
                            close=symbol_data[price_col], window=20, window_dev=2
                        )
                        self.df.loc[symbol_mask, f'{symbol}_bb_high'] = bb.bollinger_hband()
                        self.df.loc[symbol_mask, f'{symbol}_bb_low'] = bb.bollinger_lband()
                        self.df.loc[symbol_mask, f'{symbol}_bb_width'] = (
                            bb.bollinger_hband() - bb.bollinger_lband()
                        )
                    
                    # Price position relative to daily range
                    daily_high = symbol_data.groupby(symbol_data['interval_datetime'].dt.date)[price_col].transform('max')
                    daily_low = symbol_data.groupby(symbol_data['interval_datetime'].dt.date)[price_col].transform('min')
                    self.df.loc[symbol_mask, f'{symbol}_daily_position'] = (
                        (symbol_data[price_col] - daily_low) / (daily_high - daily_low + 1e-8)
                    )
                    
                    # Distance from key moving averages (normalized)
                    if f'{symbol}_ma20' in self.df.columns:
                        self.df.loc[symbol_mask, f'{symbol}_dist_ma20'] = (
                            (symbol_data[price_col] - self.df.loc[symbol_mask, f'{symbol}_ma20']) / 
                            self.df.loc[symbol_mask, f'{symbol}_volatility20']
                        )
        
        return self
        
    def merge_market_data(self):
        """Merge VIX, VVIX, and cross-asset data with main dataframe"""
        print("Merging market data...")
        
        # Set datetime as index for merging
        self.df = self.df.set_index('interval_datetime')
        
        # Merge VIX data
        if self.vix_data is not None:
            vix_close = self.vix_data[['Close']].rename(columns={'Close': 'vix_close'})
            self.df = self.df.join(vix_close, how='left')
            self.df['vix_close'] = self.df['vix_close'].fillna(method='ffill')
            
            # Add VIX-based features
            self.df['vix_ma5'] = self.df['vix_close'].rolling(5).mean()
            self.df['vix_ma20'] = self.df['vix_close'].rolling(20).mean()
            self.df['vix_change'] = self.df['vix_close'].pct_change()
            self.df['vix_change_5'] = self.df['vix_close'].pct_change(5)
            
            # VIX term structure (if we had VIX9D data, we'd calculate VIX9D/VIX ratio)
            # For now, use VIX momentum as proxy
            self.df['vix_momentum'] = self.df['vix_close'] / self.df['vix_ma20'] - 1
            
            # IV Rank (percentile of VIX over past 252 periods ~ 1 month)
            self.df['vix_rank'] = self.df['vix_close'].rolling(252).rank(pct=True)
        
        # Merge VVIX data or create synthetic VVIX
        if self.vvix_data is not None:
            vvix_close = self.vvix_data[['Close']].rename(columns={'Close': 'vvix_close'})
            self.df = self.df.join(vvix_close, how='left')
            self.df['vvix_close'] = self.df['vvix_close'].fillna(method='ffill')
        else:
            # Synthetic VVIX from VIX volatility
            self.df['vvix_close'] = self.df['vix_close'].rolling(20).std() * 100
        
        # VVIX/VIX ratio (volatility of volatility indicator)
        self.df['vvix_vix_ratio'] = self.df['vvix_close'] / (self.df['vix_close'] + 1e-8)
        
        # Merge cross-asset data
        for name, data in self.cross_asset_data.items():
            if data is not None and not data.empty:
                asset_close = data[['Close']].rename(columns={'Close': f'{name}_close'})
                self.df = self.df.join(asset_close, how='left')
                self.df[f'{name}_close'] = self.df[f'{name}_close'].fillna(method='ffill')
                
                # Add momentum features
                self.df[f'{name}_change'] = self.df[f'{name}_close'].pct_change()
                self.df[f'{name}_momentum5'] = self.df[f'{name}_close'].pct_change(5)
        
        # Calculate cross-asset correlations and spreads
        if 'ES_close' in self.df.columns and 'SPX_close' in self.df.columns:
            # Futures vs Cash spread
            self.df['es_spx_spread'] = self.df['ES_close'] - self.df['SPX_close']
        
        if 'TY_close' in self.df.columns and 'TU_close' in self.df.columns:
            # Yield curve proxy (10Y-2Y spread)
            self.df['yield_curve'] = self.df['TY_close'] - self.df['TU_close']
        
        # Market regime based on VIX levels
        self.df['market_regime'] = pd.cut(
            self.df['vix_close'],
            bins=[0, 12, 15, 20, 25, 100],
            labels=['ultra_low_vol', 'low_vol', 'normal_vol', 'elevated_vol', 'high_vol']
        )
        
        # One-hot encode market regime
        regime_dummies = pd.get_dummies(self.df['market_regime'], prefix='regime')
        self.df = pd.concat([self.df, regime_dummies], axis=1)
        
        # Reset index
        self.df = self.df.reset_index()
        
        return self
        
    def add_option_specific_features(self):
        """Add features specific to 0DTE options trading"""
        print("Adding option-specific features...")
        
        # Strategy encoding (one-hot encode the three strategies)
        if 'prof_strategy_name' in self.df.columns:
            # Clean strategy names
            self.df['strategy_clean'] = self.df['prof_strategy_name'].fillna('Unknown')
            
            # Map to our three main strategies
            strategy_mapping = {
                'Butterfly': 'Butterfly',
                'Iron Condor': 'Iron_Condor',
                'Vertical Spread': 'Vertical_Spread',
                'Broken Butterfly': 'Butterfly',  # Map variations
                'Put Spread': 'Vertical_Spread',
                'Call Spread': 'Vertical_Spread'
            }
            
            for old, new in strategy_mapping.items():
                self.df.loc[self.df['strategy_clean'].str.contains(old, na=False), 'strategy_type'] = new
            
            # One-hot encode strategies
            strategy_dummies = pd.get_dummies(self.df['strategy_type'], prefix='strategy')
            self.df = pd.concat([self.df, strategy_dummies], axis=1)
        
        # Moneyness features (if we have strike and price data)
        if 'pred_predicted' in self.df.columns and 'pred_price' in self.df.columns:
            self.df['moneyness'] = self.df['pred_predicted'] / self.df['pred_price']
            self.df['moneyness_log'] = np.log(self.df['moneyness'] + 1e-8)
        
        # Premium normalized by price
        if 'prof_premium' in self.df.columns and 'pred_price' in self.df.columns:
            self.df['premium_normalized'] = self.df['prof_premium'] / self.df['pred_price']
        
        # Risk-reward features
        if 'prof_risk' in self.df.columns and 'prof_reward' in self.df.columns:
            self.df['risk_reward_ratio'] = self.df['prof_reward'] / (self.df['prof_risk'] + 1e-8)
        
        # Delta features (Greeks)
        if 'delt_call_delta' in self.df.columns:
            self.df['delta_abs'] = self.df['delt_call_delta'].abs()
            self.df['delta_squared'] = self.df['delt_call_delta'] ** 2  # Gamma proxy
        
        # Expected move features
        if 'trad_expected_move' in self.df.columns:
            self.df['expected_move_normalized'] = (
                self.df['trad_expected_move'] / self.df['pred_price']
            )
        
        # Probability features
        if 'trad_probability' in self.df.columns:
            self.df['probability_log_odds'] = np.log(
                self.df['trad_probability'] / (1 - self.df['trad_probability'] + 1e-8)
            )
        
        return self
        
    def add_price_action_features(self):
        """Add price action and microstructure features"""
        print("Adding price action features...")
        
        for symbol in self.symbols:
            symbol_mask = self.df['pred_symbol'] == symbol
            
            if symbol_mask.sum() > 0 and 'pred_price' in self.df.columns:
                # Price acceleration (2nd derivative)
                price_change = self.df.loc[symbol_mask, 'pred_price'].diff()
                self.df.loc[symbol_mask, f'{symbol}_acceleration'] = price_change.diff()
                
                # High-low range (volatility proxy)
                if 'pred_long_term' in self.df.columns and 'pred_short_term' in self.df.columns:
                    self.df.loc[symbol_mask, f'{symbol}_range'] = (
                        self.df.loc[symbol_mask, 'pred_long_term'] - 
                        self.df.loc[symbol_mask, 'pred_short_term']
                    )
                    
                    # Normalized range
                    self.df.loc[symbol_mask, f'{symbol}_range_normalized'] = (
                        self.df.loc[symbol_mask, f'{symbol}_range'] / 
                        self.df.loc[symbol_mask, 'pred_price']
                    )
                
                # Volume profile features would go here if we had volume data
                # For now, we'll use time-based volume proxies
                
                # Pivot points (daily)
                daily_data = self.df[symbol_mask].groupby(
                    self.df[symbol_mask]['interval_datetime'].dt.date
                )
                
                # Previous day's high, low, close
                prev_high = daily_data['pred_price'].transform('max').shift(1)
                prev_low = daily_data['pred_price'].transform('min').shift(1)
                prev_close = daily_data['pred_price'].transform('last').shift(1)
                
                # Classic pivot points
                pivot = (prev_high + prev_low + prev_close) / 3
                r1 = 2 * pivot - prev_low
                s1 = 2 * pivot - prev_high
                
                self.df.loc[symbol_mask, f'{symbol}_pivot'] = pivot
                self.df.loc[symbol_mask, f'{symbol}_r1'] = r1
                self.df.loc[symbol_mask, f'{symbol}_s1'] = s1
                
                # Distance from pivot levels (normalized)
                if f'{symbol}_atr' in self.df.columns:
                    atr = self.df.loc[symbol_mask, f'{symbol}_atr']
                    self.df.loc[symbol_mask, f'{symbol}_dist_pivot'] = (
                        (self.df.loc[symbol_mask, 'pred_price'] - pivot) / atr
                    )
                    self.df.loc[symbol_mask, f'{symbol}_dist_r1'] = (
                        (self.df.loc[symbol_mask, 'pred_price'] - r1) / atr
                    )
                    self.df.loc[symbol_mask, f'{symbol}_dist_s1'] = (
                        (self.df.loc[symbol_mask, 'pred_price'] - s1) / atr
                    )
        
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
        
        # Create additional targets for multi-task learning
        if 'prof_ratio' in self.df.columns:
            # Profit ratio buckets for regression
            self.df['profit_ratio_bucket'] = pd.cut(
                self.df['prof_ratio'],
                bins=[-np.inf, -0.5, 0, 0.5, 1, 2, np.inf],
                labels=['large_loss', 'small_loss', 'breakeven', 'small_win', 'medium_win', 'large_win']
            )
        
        print(f"Target distribution: {self.df['target'].value_counts().to_dict()}")
        return self
        
    def create_sequences(self, sequence_length=60, prediction_horizon=1):
        """Create sequences for time series modeling"""
        print(f"Creating sequences with length {sequence_length}...")
        
        # Select feature columns (exclude metadata and target)
        exclude_cols = [
            'interval_datetime', 'date', 'time_est', 'target', 
            'file_types', 'record_count', 'market_regime',
            'strategy_clean', 'strategy_type', 'profit_ratio_bucket',
            # Exclude text columns
            'prof_trade', 'trad_trade', 'trad_source'
        ]
        
        feature_cols = [col for col in self.df.columns 
                       if col not in exclude_cols and not col.endswith('_symbol')]
        
        # Fill missing values
        self.df[feature_cols] = self.df[feature_cols].fillna(method='ffill').fillna(0)
        
        # Replace infinity values
        self.df[feature_cols] = self.df[feature_cols].replace([np.inf, -np.inf], 0)
        
        # Store feature names
        self.feature_names = feature_cols
        
        return self
        
    def add_event_indicators(self):
        """Add economic event and market structure indicators"""
        print("Adding event indicators...")
        
        # Fed meeting days (typically Tuesday/Wednesday of FOMC weeks)
        # This is a simplified version - in production, you'd use actual Fed calendar
        self.df['is_fed_day'] = (
            (self.df['day_of_week'].isin([1, 2])) &  # Tuesday or Wednesday
            (self.df['day_of_month'] >= 14) & (self.df['day_of_month'] <= 22)
        ).astype(int)
        
        # Major economic releases (typically 8:30 AM ET)
        self.df['is_econ_release'] = (
            (self.df['hour'] == 8) & (self.df['minute'] == 30) &
            (self.df['day_of_week'] < 5)
        ).astype(int)
        
        # Pre-market indicator
        self.df['is_premarket'] = (
            (self.df['hour'] >= 4) & (self.df['hour'] < 9) &
            (self.df['day_of_week'] < 5)
        ).astype(int)
        
        # After-hours indicator
        self.df['is_afterhours'] = (
            (self.df['hour'] >= 16) & (self.df['hour'] <= 20) &
            (self.df['day_of_week'] < 5)
        ).astype(int)
        
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
            'symbols': self.symbols,
            'strategies': self.strategies,
            'train_samples': len(train_data),
            'val_samples': len(val_data),
            'test_samples': len(test_data),
            'class_distribution': {
                'train': train_data['target'].value_counts().to_dict(),
                'val': val_data['target'].value_counts().to_dict(),
                'test': test_data['target'].value_counts().to_dict()
            }
        }
        
        # Add feature importance hints
        stats['feature_categories'] = {
            'temporal': [f for f in self.feature_names if any(t in f for t in ['hour', 'minute', 'day', 'time', 'decay'])],
            'market_structure': [f for f in self.feature_names if any(t in f for t in ['vix', 'vvix', 'regime', 'yield'])],
            'technical': [f for f in self.feature_names if any(t in f for t in ['rsi', 'ma', 'momentum', 'volatility', 'bb', 'atr'])],
            'option_specific': [f for f in self.feature_names if any(t in f for t in ['delta', 'moneyness', 'premium', 'strategy'])],
            'price_action': [f for f in self.feature_names if any(t in f for t in ['pivot', 'range', 'acceleration', 'dist'])],
            'cross_asset': [f for f in self.feature_names if any(t in f for t in ['DXY', 'TY', 'TU', 'XLF', 'XLK', 'ES', 'NQ'])]
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
        self.fetch_market_data()
        self.add_temporal_features()
        self.add_technical_indicators()
        self.merge_market_data()
        self.add_option_specific_features()
        self.add_price_action_features()
        self.add_event_indicators()
        self.create_target_variable()
        self.create_sequences()
        train_data, val_data, test_data = self.split_data()
        
        print("\nData preparation complete!")
        print(f"Total features: {len(self.feature_names)}")
        print(f"Feature categories: {len(self.feature_names)} total features across temporal, market structure, technical, option-specific, and cross-asset categories")
        
        return train_data, val_data, test_data


if __name__ == "__main__":
    # Run data preparation
    prep = DataPreparation()
    train_data, val_data, test_data = prep.run_pipeline()
