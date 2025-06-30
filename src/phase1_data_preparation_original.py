"""
Phase 1 MVP Data Preparation Script for Magic8 Accuracy Predictor

This script focuses on readily available data:
- Your existing normalized trading data
- Historical price data from IBKR
- VIX data (from IBKR or Yahoo Finance)
- Basic technical indicators calculated from price data
- Simple time-based features

Note: IBKR data is in UTC, while trading data is likely in US Eastern Time.
This script handles the timezone conversion appropriately.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import ta
from sklearn.preprocessing import StandardScaler
import json
import os
import logging
import pytz

class Phase1DataPreparation:
    def __init__(self, data_path='data/normalized/normalized_aggregated.csv', 
                 trading_timezone='US/Eastern'):
        self.data_path = data_path
        self.df = None
        self.logger = self._setup_logger()
        self.trading_timezone = trading_timezone  # Timezone for trading data
        
        # Phase 1: Focus on symbols we can easily get data for
        self.symbols = ['SPX', 'SPY', 'XSP', 'NDX', 'QQQ', 'RUT', 'AAPL', 'TSLA']
        
    def _setup_logger(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
        
    def load_data(self):
        """Load the normalized aggregated data"""
        self.logger.info("Loading normalized data...")
        self.df = pd.read_csv(self.data_path)
        self.df['interval_datetime'] = pd.to_datetime(self.df['interval_datetime'])
        
        # Check if timezone-aware
        if self.df['interval_datetime'].dt.tz is not None:
            self.logger.info(f"Trade data has timezone: {self.df['interval_datetime'].dt.tz}")
            # Convert to timezone-naive for consistency
            self.df['interval_datetime'] = self.df['interval_datetime'].dt.tz_localize(None)
        else:
            # Assume the data is in Eastern Time if no timezone info
            self.logger.info(f"Trade data assumed to be in {self.trading_timezone}")
            
        self.df = self.df.sort_values('interval_datetime')
        self.logger.info(f"Loaded {len(self.df)} records")
        return self
        
    def load_ibkr_data(self, ibkr_data_path='data/ibkr'):
        """
        Load historical price data downloaded from IBKR.
        Assumes files are named like: historical_data_INDEX_SPX_5_mins.csv
        
        IBKR data is in UTC, so we need to convert it to match the trading data timezone.
        """
        self.logger.info("Loading IBKR historical data...")
        self.price_data = {}
        
        # Map our symbols to IBKR file naming
        symbol_mapping = {
            'SPX': 'INDEX_SPX',
            'SPY': 'STOCK_SPY',
            'XSP': 'INDEX_XSP',
            'NDX': 'INDEX_NDX',
            'QQQ': 'STOCK_QQQ',
            'RUT': 'INDEX_RUT',
            'AAPL': 'STOCK_AAPL',
            'TSLA': 'STOCK_TSLA'
        }
        
        for symbol, ibkr_name in symbol_mapping.items():
            # Try to load 5-minute data (primary timeframe for features)
            filename = os.path.join(ibkr_data_path, f'historical_data_{ibkr_name}_5_mins.csv')
            if os.path.exists(filename):
                df = pd.read_csv(filename)
                df['date'] = pd.to_datetime(df['date'])
                
                # IBKR data is in UTC - convert to Eastern Time for US markets
                if df['date'].dt.tz is not None:
                    # Data has timezone (UTC), convert to Eastern
                    df['date'] = df['date'].dt.tz_convert(pytz.timezone(self.trading_timezone))
                    # Then remove timezone info to match normalized data
                    df['date'] = df['date'].dt.tz_localize(None)
                    self.logger.info(f"Converted {symbol} from UTC to {self.trading_timezone}")
                else:
                    # If no timezone, assume it's already in the correct timezone
                    self.logger.warning(f"{symbol} data has no timezone info, assuming {self.trading_timezone}")
                
                df = df.set_index('date')
                self.price_data[symbol] = df
                self.logger.info(f"Loaded {len(df)} records for {symbol}")
            else:
                self.logger.warning(f"No IBKR data found for {symbol} at {filename}")
                
        # Load VIX separately
        vix_file = os.path.join(ibkr_data_path, 'historical_data_INDEX_VIX_5_mins.csv')
        if os.path.exists(vix_file):
            self.vix_data = pd.read_csv(vix_file)
            self.vix_data['date'] = pd.to_datetime(self.vix_data['date'])
            
            # Convert VIX data from UTC to Eastern
            if self.vix_data['date'].dt.tz is not None:
                self.vix_data['date'] = self.vix_data['date'].dt.tz_convert(pytz.timezone(self.trading_timezone))
                self.vix_data['date'] = self.vix_data['date'].dt.tz_localize(None)
                self.logger.info(f"Converted VIX from UTC to {self.trading_timezone}")
                
            self.vix_data = self.vix_data.set_index('date')
            self.logger.info(f"Loaded {len(self.vix_data)} VIX records")
        else:
            self.logger.warning("No VIX data found, will try Yahoo Finance")
            self.fetch_vix_fallback()
            
        return self
        
    def fetch_vix_fallback(self):
        """Fallback to Yahoo Finance for VIX data if IBKR data not available"""
        self.logger.info("Fetching VIX data from Yahoo Finance...")
        start_date = self.df['interval_datetime'].min() - timedelta(days=30)
        end_date = self.df['interval_datetime'].max() + timedelta(days=1)
        
        vix = yf.download('^VIX', start=start_date, end=end_date, interval='5m')
        if not vix.empty:
            self.vix_data = vix[['Close', 'Volume']].rename(columns={'Close': 'close', 'Volume': 'volume'})
            self.logger.info(f"Downloaded {len(self.vix_data)} VIX records from Yahoo")
        else:
            self.logger.error("Failed to download VIX data")
            
    def add_basic_temporal_features(self):
        """Add simple time-based features that are proven useful for trading"""
        self.logger.info("Adding temporal features...")
        
        # Basic time components
        self.df['hour'] = self.df['interval_datetime'].dt.hour
        self.df['minute'] = self.df['interval_datetime'].dt.minute
        self.df['day_of_week'] = self.df['interval_datetime'].dt.dayofweek
        
        # Cyclical encoding for hour (important for intraday patterns)
        self.df['hour_sin'] = np.sin(2 * np.pi * self.df['hour'] / 24)
        self.df['hour_cos'] = np.cos(2 * np.pi * self.df['hour'] / 24)
        
        # Market session indicators
        self.df['is_market_open'] = (
            (self.df['hour'] >= 9) & (self.df['hour'] < 16) &
            (self.df['day_of_week'] < 5)
        ).astype(int)
        
        # First and last 30 minutes (high activity periods)
        self.df['is_open_30min'] = (
            (self.df['hour'] == 9) & (self.df['minute'] >= 30)
        ).astype(int)
        
        self.df['is_close_30min'] = (
            (self.df['hour'] == 15) & (self.df['minute'] >= 30)
        ).astype(int)
        
        # Simple time to close for 0DTE
        self.df['minutes_to_close'] = 0
        market_open_mask = self.df['is_market_open'] == 1
        self.df.loc[market_open_mask, 'minutes_to_close'] = (
            (16 - self.df.loc[market_open_mask, 'hour']) * 60 - 
            self.df.loc[market_open_mask, 'minute']
        )
        
        return self
        
    def add_price_features(self):
        """Add price-based features using IBKR data"""
        self.logger.info("Adding price features...")
        
        # For each symbol in our data
        for symbol in self.symbols:
            if symbol not in self.price_data:
                self.logger.warning(f"No price data for {symbol}, skipping")
                continue
                
            # Get price data for this symbol
            price_df = self.price_data[symbol]
            
            # Calculate simple technical indicators
            # 20-period SMA (about 100 minutes)
            price_df['sma_20'] = price_df['close'].rolling(20).mean()
            
            # Price momentum (5-period)
            price_df['momentum_5'] = price_df['close'].pct_change(5)
            
            # Volatility (20-period)
            price_df['volatility_20'] = price_df['close'].rolling(20).std()
            
            # RSI
            if len(price_df) > 14:
                price_df['rsi'] = ta.momentum.RSIIndicator(close=price_df['close'], window=14).rsi()
            
            # Distance from high/low
            price_df['high_20'] = price_df['high'].rolling(20).max()
            price_df['low_20'] = price_df['low'].rolling(20).min()
            price_df['price_position'] = (price_df['close'] - price_df['low_20']) / (price_df['high_20'] - price_df['low_20'] + 1e-8)
            
            # Merge with main dataframe
            # First, create a mapping based on symbol and time
            symbol_mask = self.df['pred_symbol'] == symbol
            if symbol_mask.sum() > 0:
                # Align the price data with our main data
                for col in ['close', 'sma_20', 'momentum_5', 'volatility_20', 'rsi', 'price_position']:
                    if col in price_df.columns:
                        # Create feature name
                        feature_name = f'{symbol}_{col}'
                        
                        # Merge based on nearest time
                        self.df.loc[symbol_mask, feature_name] = self.df.loc[symbol_mask, 'interval_datetime'].apply(
                            lambda x: self._get_nearest_value(price_df, x, col)
                        )
        
        return self
        
    def _get_nearest_value(self, df, timestamp, column):
        """Get the nearest value from a dataframe based on timestamp"""
        # Ensure timestamp is timezone-naive
        if hasattr(timestamp, 'tz') and timestamp.tz is not None:
            timestamp = timestamp.tz_localize(None)
            
        if timestamp in df.index:
            return df.loc[timestamp, column]
        else:
            # Find nearest timestamp
            time_diff = abs(df.index - timestamp)
            if len(time_diff) > 0:
                nearest_idx = time_diff.argmin()
                if time_diff[nearest_idx] < timedelta(minutes=10):  # Within 10 minutes
                    return df.iloc[nearest_idx][column]
        return np.nan
        
    def add_vix_features(self):
        """Add VIX-based features"""
        self.logger.info("Adding VIX features...")
        
        if hasattr(self, 'vix_data') and self.vix_data is not None:
            # Basic VIX features
            vix_df = self.vix_data.copy()
            
            # VIX moving average
            vix_df['vix_sma_20'] = vix_df['close'].rolling(20).mean()
            
            # VIX change
            vix_df['vix_change'] = vix_df['close'].pct_change()
            
            # Merge VIX data with main dataframe
            for col in ['close', 'vix_sma_20', 'vix_change']:
                if col in vix_df.columns:
                    feature_name = f'vix_{col}' if col != 'close' else 'vix'
                    self.df[feature_name] = self.df['interval_datetime'].apply(
                        lambda x: self._get_nearest_value(vix_df, x, col)
                    )
            
            # Simple VIX regime
            self.df['vix_regime'] = pd.cut(
                self.df['vix'],
                bins=[0, 15, 20, 25, 100],
                labels=['low', 'normal', 'elevated', 'high']
            )
            
            # One-hot encode VIX regime
            regime_dummies = pd.get_dummies(self.df['vix_regime'], prefix='vix_regime')
            self.df = pd.concat([self.df, regime_dummies], axis=1)
            
            # Drop the original categorical column
            self.df = self.df.drop('vix_regime', axis=1)
            self.logger.info("Dropped original 'vix_regime' categorical column")
        
        return self
        
    def add_trade_features(self):
        """Add features from existing trade data"""
        self.logger.info("Adding trade-specific features...")
        
        # Strategy encoding
        if 'prof_strategy_name' in self.df.columns:
            # Simplified strategy mapping
            self.df['strategy_type'] = 'Unknown'
            self.df.loc[self.df['prof_strategy_name'].str.contains('Butterfly', na=False), 'strategy_type'] = 'Butterfly'
            self.df.loc[self.df['prof_strategy_name'].str.contains('Condor', na=False), 'strategy_type'] = 'Iron_Condor'
            self.df.loc[self.df['prof_strategy_name'].str.contains('Spread', na=False), 'strategy_type'] = 'Vertical'
            
            # One-hot encode
            strategy_dummies = pd.get_dummies(self.df['strategy_type'], prefix='strategy')
            self.df = pd.concat([self.df, strategy_dummies], axis=1)
            
            # Drop the original categorical column
            self.df = self.df.drop('strategy_type', axis=1)
            self.logger.info("Dropped original 'strategy_type' categorical column")
        
        # Premium normalized by underlying price (if we have it)
        if 'prof_premium' in self.df.columns:
            # Try to get the underlying price at the time
            for symbol in self.symbols:
                symbol_mask = self.df['pred_symbol'] == symbol
                if symbol_mask.sum() > 0 and f'{symbol}_close' in self.df.columns:
                    self.df.loc[symbol_mask, 'premium_normalized'] = (
                        self.df.loc[symbol_mask, 'prof_premium'] / 
                        self.df.loc[symbol_mask, f'{symbol}_close']
                    )
        
        # Risk-reward ratio
        if 'prof_risk' in self.df.columns and 'prof_reward' in self.df.columns:
            self.df['risk_reward_ratio'] = self.df['prof_reward'] / (self.df['prof_risk'] + 1e-8)
        
        return self
        
    def create_target_variable(self):
        """Create binary target variable from profit data
        
        Uses Raw profit/loss as the determinant:
        - Raw profit > 0 = Win (1)
        - Raw profit <= 0 = Loss (0)
        
        Raw P/L represents the pure quality of the trade without external management.
        """
        self.logger.info("Creating target variable from Raw profit data...")
        
        # First, let's find the correct Raw profit column
        raw_profit_col = None
        
        # Look for columns containing 'raw' (case insensitive)
        for col in self.df.columns:
            if 'raw' in col.lower() and ('profit' in col.lower() or 'p/l' in col.lower() or 'pnl' in col.lower()):
                raw_profit_col = col
                self.logger.info(f"Found Raw profit column: {col}")
                break
        
        # If no raw profit column found, try common variations
        if raw_profit_col is None:
            # Try common column names
            possible_names = ['prof_raw', 'prof_raw_profit', 'prof_raw_pnl', 'prof_raw_p/l', 
                            'trad_raw', 'trad_raw_profit', 'Raw', 'raw', 'raw_profit', 'raw_pnl']
            for col_name in possible_names:
                if col_name in self.df.columns:
                    raw_profit_col = col_name
                    self.logger.info(f"Found Raw profit column: {col_name}")
                    break
        
        # Create target based on Raw profit
        if raw_profit_col is not None:
            # Raw profit > 0 = Win (1), Raw profit <= 0 = Loss (0)
            self.df['target'] = (self.df[raw_profit_col] > 0).astype(int)
            
            # Log statistics
            non_null_count = self.df['target'].notna().sum()
            self.logger.info(f"Created target from {raw_profit_col}: {non_null_count} records")
            self.logger.info(f"Target distribution: {self.df['target'].value_counts().to_dict()}")
            self.logger.info(f"Win rate: {self.df['target'].mean():.2%}")
        else:
            # Fallback to prof_profit if no raw column found
            self.logger.warning("No Raw profit column found! Falling back to prof_profit")
            if 'prof_profit' in self.df.columns:
                self.df['target'] = (self.df['prof_profit'] > 0).astype(int)
                self.logger.info(f"Created target from prof_profit: {self.df['target'].notna().sum()} records")
                self.logger.info(f"Target distribution: {self.df['target'].value_counts().to_dict()}")
            else:
                raise ValueError("No suitable profit column found for creating target variable!")
        
        return self
        
    def select_features(self):
        """Select only the features we've calculated for Phase 1"""
        self.logger.info("Selecting Phase 1 features...")
        
        # Define feature groups
        temporal_features = [
            'hour', 'minute', 'day_of_week', 'hour_sin', 'hour_cos',
            'is_market_open', 'is_open_30min', 'is_close_30min', 'minutes_to_close'
        ]
        
        # Price features for each symbol
        price_features = []
        for symbol in self.symbols:
            for suffix in ['close', 'sma_20', 'momentum_5', 'volatility_20', 'rsi', 'price_position']:
                feature = f'{symbol}_{suffix}'
                if feature in self.df.columns:
                    price_features.append(feature)
        
        # VIX features (excluding the original vix_regime which was dropped)
        vix_features = [col for col in self.df.columns if col.startswith('vix') and col != 'vix_regime']
        
        # Strategy features
        strategy_features = [col for col in self.df.columns if col.startswith('strategy_')]
        
        # Trade features
        trade_features = ['premium_normalized', 'risk_reward_ratio']
        trade_features = [f for f in trade_features if f in self.df.columns]
        
        # Original features to keep
        original_features = [
            'pred_predicted', 'pred_price', 'pred_difference',
            'prof_premium', 'prof_risk', 'prof_reward',
            'trad_probability', 'trad_expected_move'
        ]
        original_features = [f for f in original_features if f in self.df.columns]
        
        # Combine all features
        self.feature_names = (
            temporal_features + price_features + vix_features + 
            strategy_features + trade_features + original_features
        )
        
        # Remove any that don't exist
        self.feature_names = [f for f in self.feature_names if f in self.df.columns]
        
        self.logger.info(f"Selected {len(self.feature_names)} features for Phase 1")
        return self
        
    def split_data(self, test_size=0.2, val_size=0.2):
        """Split data temporally into train/val/test sets"""
        self.logger.info("Splitting data into train/val/test sets...")
        
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
        
        self.logger.info(f"Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}")
        
        # Save splits
        os.makedirs('data/phase1_processed', exist_ok=True)
        
        # Save only selected features + metadata
        save_columns = ['interval_datetime', 'pred_symbol', 'target'] + self.feature_names
        save_columns = [col for col in save_columns if col in train_data.columns]
        
        train_data[save_columns].to_csv('data/phase1_processed/train_data.csv', index=False)
        val_data[save_columns].to_csv('data/phase1_processed/val_data.csv', index=False)
        test_data[save_columns].to_csv('data/phase1_processed/test_data.csv', index=False)
        
        # Save feature info
        feature_info = {
            'n_features': len(self.feature_names),
            'feature_names': self.feature_names,
            'feature_groups': {
                'temporal': [f for f in self.feature_names if f in ['hour', 'minute', 'day_of_week', 'hour_sin', 'hour_cos', 'is_market_open', 'is_open_30min', 'is_close_30min', 'minutes_to_close']],
                'price': [f for f in self.feature_names if any(f.startswith(s) for s in self.symbols) and not f.startswith('strategy')],
                'vix': [f for f in self.feature_names if f.startswith('vix')],
                'strategy': [f for f in self.feature_names if f.startswith('strategy')],
                'trade': [f for f in self.feature_names if f in ['premium_normalized', 'risk_reward_ratio']]
            },
            'train_samples': len(train_data),
            'val_samples': len(val_data),
            'test_samples': len(test_data),
            'class_distribution': {
                'train': train_data['target'].value_counts().to_dict(),
                'val': val_data['target'].value_counts().to_dict(),
                'test': test_data['target'].value_counts().to_dict()
            }
        }
        
        with open('data/phase1_processed/feature_info.json', 'w') as f:
            json.dump(feature_info, f, indent=2)
        
        self.logger.info("Phase 1 data preparation complete!")
        return train_data, val_data, test_data
    
    def run_phase1_pipeline(self):
        """Run the complete Phase 1 data preparation pipeline"""
        # Load normalized trade data
        self.load_data()
        
        # Load IBKR historical price data
        self.load_ibkr_data()
        
        # Add features
        self.add_basic_temporal_features()
        self.add_price_features()
        self.add_vix_features()
        self.add_trade_features()
        
        # Create target
        self.create_target_variable()
        
        # Select features
        self.select_features()
        
        # Split and save
        train_data, val_data, test_data = self.split_data()
        
        return train_data, val_data, test_data


if __name__ == "__main__":
    # Run Phase 1 data preparation
    prep = Phase1DataPreparation()
    train_data, val_data, test_data = prep.run_phase1_pipeline()
