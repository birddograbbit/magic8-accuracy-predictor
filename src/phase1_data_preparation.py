"""
Phase 1 MVP Data Preparation Script for Magic8 Accuracy Predictor - OPTIMIZED VERSION

Performance optimizations:
- Uses pd.merge_asof() instead of apply/lambda for time-series joins (100x+ faster)
- Processes each symbol's data in bulk instead of row-by-row
- Adds progress tracking to monitor performance
- Maintains same accuracy with 10-minute tolerance for matching

Expected runtime: 2-5 minutes instead of 3+ hours
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
import time

from src.feature_engineering.magic8_features import Magic8FeatureEngineer, SymbolNormalizer
from src.feature_engineering.delta_features import DeltaFeatureGenerator
from validate_profit_coverage import validate_profit_data

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
        
    def _log_time(self, start_time, operation):
        """Log the time taken for an operation"""
        elapsed = time.time() - start_time
        self.logger.info(f"{operation} completed in {elapsed:.2f} seconds")
        
    def load_data(self):
        """Load the normalized aggregated data and map columns"""
        start_time = time.time()
        self.logger.info("Loading normalized data...")
        self.df = pd.read_csv(self.data_path)
        
        # Create interval_datetime from available columns
        if 'timestamp' in self.df.columns and self.df['timestamp'].notna().any():
            self.df['interval_datetime'] = pd.to_datetime(self.df['timestamp'], errors='coerce')
        elif 'datetime' in self.df.columns and self.df['datetime'].notna().any():
            self.df['interval_datetime'] = pd.to_datetime(self.df['datetime'], errors='coerce')
        elif 'date' in self.df.columns and 'time' in self.df.columns:
            # Combine date and time columns
            self.df['interval_datetime'] = pd.to_datetime(
                self.df['date'].astype(str) + ' ' + self.df['time'].astype(str), 
                errors='coerce'
            )
        else:
            raise ValueError("No suitable datetime column found!")
        
        # Map column names to expected names
        column_mapping = {
            'symbol': 'pred_symbol',
            'strategy': 'prof_strategy_name',
            'premium': 'prof_premium',
            'risk': 'prof_risk',
            'reward': 'prof_reward',
            'predicted': 'pred_predicted',
            'price': 'pred_price',
            'profit': 'prof_profit'
        }
        
        # Apply column mapping
        for old_name, new_name in column_mapping.items():
            if old_name in self.df.columns and new_name not in self.df.columns:
                self.df[new_name] = self.df[old_name]
        
        # Calculate pred_difference if we have the data
        if 'pred_predicted' in self.df.columns and 'pred_price' in self.df.columns:
            self.df['pred_difference'] = self.df['pred_predicted'] - self.df['pred_price']
        
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
        
        # Log available columns
        self.logger.info(f"Available columns: {', '.join(self.df.columns)}")
        
        self._log_time(start_time, "Data loading")
        return self
        
    def load_ibkr_data(self, ibkr_data_path='data/ibkr'):
        """
        Load historical price data downloaded from IBKR.
        Assumes files are named like: historical_data_INDEX_SPX_5_mins.csv
        
        IBKR data is in UTC, so we need to convert it to match the trading data timezone.
        """
        start_time = time.time()
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
                
                # Pre-calculate technical indicators for this symbol
                self.logger.info(f"Calculating technical indicators for {symbol}...")
                # 20-period SMA (about 100 minutes)
                df['sma_20'] = df['close'].rolling(20).mean()
                
                # Price momentum (5-period)
                df['momentum_5'] = df['close'].pct_change(5)
                
                # Volatility (20-period)
                df['volatility_20'] = df['close'].rolling(20).std()
                
                # RSI
                if len(df) > 14:
                    df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi()
                
                # Distance from high/low
                df['high_20'] = df['high'].rolling(20).max()
                df['low_20'] = df['low'].rolling(20).min()
                df['price_position'] = (df['close'] - df['low_20']) / (df['high_20'] - df['low_20'] + 1e-8)
                
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
            
            # Pre-calculate VIX features
            self.logger.info("Calculating VIX technical indicators...")
            self.vix_data['vix_sma_20'] = self.vix_data['close'].rolling(20).mean()
            self.vix_data['vix_change'] = self.vix_data['close'].pct_change()
            
            self.logger.info(f"Loaded {len(self.vix_data)} VIX records")
        else:
            self.logger.warning("No VIX data found, will try Yahoo Finance")
            self.fetch_vix_fallback()
            
        self._log_time(start_time, "IBKR data loading and indicator calculation")
        return self
        
    def fetch_vix_fallback(self):
        """Fallback to Yahoo Finance for VIX data if IBKR data not available"""
        self.logger.info("Fetching VIX data from Yahoo Finance...")
        start_date = self.df['interval_datetime'].min() - timedelta(days=30)
        end_date = self.df['interval_datetime'].max() + timedelta(days=1)
        
        vix = yf.download('^VIX', start=start_date, end=end_date, interval='5m')
        if not vix.empty:
            self.vix_data = vix[['Close', 'Volume']].rename(columns={'Close': 'close', 'Volume': 'volume'})
            # Pre-calculate VIX features
            self.vix_data['vix_sma_20'] = self.vix_data['close'].rolling(20).mean()
            self.vix_data['vix_change'] = self.vix_data['close'].pct_change()
            self.logger.info(f"Downloaded {len(self.vix_data)} VIX records from Yahoo")
        else:
            self.logger.error("Failed to download VIX data")
            
    def add_basic_temporal_features(self):
        """Add simple time-based features that are proven useful for trading"""
        start_time = time.time()
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
        
        self._log_time(start_time, "Temporal features")
        return self
        
    def add_price_features(self):
        """Add price-based features using IBKR data - OPTIMIZED VERSION"""
        start_time = time.time()
        self.logger.info("Adding price features using merge_asof...")
        
        # Process each symbol
        for symbol in self.symbols:
            symbol_start = time.time()
            
            if symbol not in self.price_data:
                self.logger.warning(f"No price data for {symbol}, skipping")
                continue
                
            # Get rows for this symbol
            symbol_mask = self.df['pred_symbol'] == symbol
            symbol_count = symbol_mask.sum()
            
            if symbol_count == 0:
                continue
                
            self.logger.info(f"Processing {symbol_count} rows for {symbol}...")
            
            # Get price data for this symbol
            price_df = self.price_data[symbol]
            
            # Select features to merge
            feature_cols = ['close', 'sma_20', 'momentum_5', 'volatility_20', 'rsi', 'price_position']
            available_cols = [col for col in feature_cols if col in price_df.columns]
            
            # Create a temporary dataframe with the features we want
            price_features = price_df[available_cols].copy()
            
            # Rename columns to include symbol prefix
            price_features.columns = [f'{symbol}_{col}' for col in price_features.columns]
            
            # Get the subset of data for this symbol
            symbol_data = self.df.loc[symbol_mask, ['interval_datetime']].copy()
            symbol_data = symbol_data.reset_index(drop=False)  # Keep original index
            
            # Use merge_asof for efficient time-based merge
            merged = pd.merge_asof(
                symbol_data.sort_values('interval_datetime'),
                price_features.sort_index(),
                left_on='interval_datetime',
                right_index=True,
                direction='nearest',
                tolerance=pd.Timedelta('10min')
            )
            
            # Map back to original indices and update main dataframe
            merged = merged.set_index('index')
            for col in price_features.columns:
                self.df.loc[symbol_mask, col] = merged[col]
            
            self._log_time(symbol_start, f"Price features for {symbol}")
        
        self._log_time(start_time, "All price features")
        return self
        
    def add_vix_features(self):
        """Add VIX-based features - OPTIMIZED VERSION"""
        start_time = time.time()
        self.logger.info("Adding VIX features using merge_asof...")
        
        if hasattr(self, 'vix_data') and self.vix_data is not None:
            # Select VIX features to merge
            vix_features = self.vix_data[['close', 'vix_sma_20', 'vix_change']].copy()
            
            # Rename columns
            vix_features.columns = ['vix', 'vix_vix_sma_20', 'vix_vix_change']
            
            # Create a temporary dataframe with just the datetime
            temp_df = self.df[['interval_datetime']].copy()
            temp_df = temp_df.reset_index(drop=False)
            
            # Use merge_asof for efficient time-based merge
            merged = pd.merge_asof(
                temp_df.sort_values('interval_datetime'),
                vix_features.sort_index(),
                left_on='interval_datetime',
                right_index=True,
                direction='nearest',
                tolerance=pd.Timedelta('10min')
            )
            
            # Map back to original indices
            merged = merged.set_index('index')
            for col in vix_features.columns:
                self.df[col] = merged[col]
            
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
        
        self._log_time(start_time, "VIX features")
        return self
        
    def add_trade_features(self):
        """Add features from existing trade data"""
        start_time = time.time()
        self.logger.info("Adding trade-specific features...")
        
        # Strategy encoding
        if 'prof_strategy_name' in self.df.columns:
            # Create clean strategy type
            self.df['strategy_type'] = self.df['prof_strategy_name']
            
            # One-hot encode
            strategy_dummies = pd.get_dummies(self.df['strategy_type'], prefix='strategy')
            self.df = pd.concat([self.df, strategy_dummies], axis=1)
            
            # Drop the original categorical column
            self.df = self.df.drop('strategy_type', axis=1)
            self.logger.info("Dropped original 'strategy_type' categorical column")
        
        # Premium normalized by underlying price (if we have it)
        if 'prof_premium' in self.df.columns:
            # Vectorized operation for all symbols at once
            self.df['premium_normalized'] = np.nan
            
            for symbol in self.symbols:
                symbol_mask = self.df['pred_symbol'] == symbol
                close_col = f'{symbol}_close'
                
                if symbol_mask.sum() > 0 and close_col in self.df.columns:
                    self.df.loc[symbol_mask, 'premium_normalized'] = (
                        self.df.loc[symbol_mask, 'prof_premium'] / 
                        self.df.loc[symbol_mask, close_col]
                    )
        
        # Risk-reward ratio
        if 'prof_risk' in self.df.columns and 'prof_reward' in self.df.columns:
            self.df['risk_reward_ratio'] = self.df['prof_reward'] / (self.df['prof_risk'] + 1e-8)
        
        self._log_time(start_time, "Trade features")
        return self
        
    def create_target_variable(self):
        """Create binary target variable from profit data"""
        start_time = time.time()
        self.logger.info("Creating target variable from profit data...")
        
        profit_sources = ['prof_profit', 'raw', 'managed', 'profit_final']
        profit_col = None
        for col in profit_sources:
            if col in self.df.columns and self.df[col].notna().any():
                profit_col = col
                break

        if not profit_col:
            raise ValueError("No profit column found for creating target variable!")

        self.logger.info(f"Using '{profit_col}' column for target creation")
        non_null_count = self.df[profit_col].notna().sum()
        self.logger.info(f"Non-null profit values: {non_null_count}")

        self.df['target'] = (self.df[profit_col] > 0).astype(int)

        self.logger.info(f"Target distribution: {self.df['target'].value_counts().to_dict()}")
        self.logger.info(f"Win rate: {self.df['target'].mean():.2%}")

        self._log_time(start_time, "Target variable creation")
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
        
        # Original features to keep (if they exist)
        original_features = [
            'pred_predicted', 'pred_price', 'pred_difference',
            'prof_premium'
        ]
        
        # Add optional features if they exist
        optional_features = ['trad_probability', 'trad_expected_move']
        for feat in optional_features:
            if feat in self.df.columns:
                original_features.append(feat)
        
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
        start_time = time.time()
        self.logger.info("Splitting data into train/val/test sets...")
        
        # Remove rows without target
        valid_data = self.df[self.df['target'].notna()].copy()
        
        # Calculate temporal cut points
        n_samples = len(valid_data)
        train_val_end = int(n_samples * (1 - test_size))

        train_val = valid_data.iloc[:train_val_end]
        test_data = valid_data.iloc[train_val_end:]

        # Stratified split on the training portion for balanced classes
        from sklearn.model_selection import train_test_split
        train_data, val_data = train_test_split(
            train_val,
            test_size=val_size / (1 - test_size),
            stratify=train_val['target'],
            random_state=42,
            shuffle=True,
        )
        
        self.logger.info(
            f"Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}"
        )
        self.logger.info(
            f"Class distribution - Train: {train_data['target'].value_counts().to_dict()}"
        )
        self.logger.info(
            f"Class distribution - Val: {val_data['target'].value_counts().to_dict()}"
        )
        self.logger.info(
            f"Class distribution - Test: {test_data['target'].value_counts().to_dict()}"
        )
        
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
        
        self._log_time(start_time, "Data splitting and saving")
        self.logger.info("Phase 1 data preparation complete!")
        return train_data, val_data, test_data
    
    def run_phase1_pipeline(self):
        """Run the complete Phase 1 data preparation pipeline"""
        pipeline_start = time.time()
        
        # Load normalized trade data
        self.load_data()
        
        # Load IBKR historical price data
        self.load_ibkr_data()
        
        # Add features
        self.add_basic_temporal_features()
        self.add_price_features()
        self.add_vix_features()
        self.add_trade_features()
        # Magic8 specific prediction alignment features
        fe = Magic8FeatureEngineer()
        self.df = fe.engineer(self.df)

        # Delta-aware features
        delta_fe = DeltaFeatureGenerator()
        self.df = delta_fe.generate_delta_features(self.df)

        # Normalize profit columns per symbol if statistics available
        profit_col_candidates = ['prof_profit', 'raw', 'managed', 'profit_final']
        profit_col = next((c for c in profit_col_candidates if c in self.df.columns), None)
        if profit_col:
            stats_df = self.df.groupby('pred_symbol')[profit_col].agg(['mean', 'std']).reset_index().rename(columns={'pred_symbol': 'symbol'})
            normalizer = SymbolNormalizer(stats_df)
            self.df = normalizer.transform(self.df, [profit_col])

        # Create target
        self.create_target_variable()

        # Validate profit coverage and class balance
        validate_profit_data(self.df)

        # Select features
        self.select_features()
        
        # Split and save
        train_data, val_data, test_data = self.split_data()
        
        self._log_time(pipeline_start, "COMPLETE PIPELINE")
        
        return train_data, val_data, test_data


if __name__ == "__main__":
    # Run Phase 1 data preparation
    prep = Phase1DataPreparation()
    train_data, val_data, test_data = prep.run_phase1_pipeline()
