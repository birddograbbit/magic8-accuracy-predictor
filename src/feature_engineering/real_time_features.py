"""
Real-time feature generator that matches Phase 1 training features.

This module generates the same features used in training:
- Temporal features (9)
- Price features (5-6 per symbol)
- VIX features (6-8)
- Trade features (8-10)
"""

import asyncio
import logging
import math
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..data_providers.base_provider import BaseDataProvider

logger = logging.getLogger(__name__)


class RealTimeFeatureGenerator:
    """
    Generates features for real-time predictions matching Phase 1 training.
    
    Total features: ~60-70 depending on configuration
    """
    
    def __init__(
        self,
        data_provider: BaseDataProvider,
        config: Optional[Dict] = None
    ):
        """
        Initialize the feature generator.
        
        Args:
            data_provider: Data provider instance
            config: Optional configuration for feature generation
        """
        self.data_provider = data_provider
        self.config = config or self._default_config()
        
        # Feature configuration
        self.temporal_config = self.config.get('temporal', {})
        self.price_config = self.config.get('price', {})
        self.vix_config = self.config.get('vix', {})
        
        logger.info("RealTimeFeatureGenerator initialized")
    
    def _default_config(self) -> Dict:
        """Get default feature configuration matching Phase 1."""
        return {
            'temporal': {
                'enabled': True,
                'features': ['hour', 'minute', 'day_of_week', 'minutes_to_close']
            },
            'price': {
                'enabled': True,
                'sma_periods': [20],
                'momentum_periods': [5],
                'rsi_period': 14
            },
            'vix': {
                'enabled': True,
                'sma_period': 20,
                'regime_thresholds': [15, 20, 25]
            }
        }
    
    async def generate_features(
        self,
        symbol: str,
        order_details: Dict
    ) -> Tuple[List[float], List[str]]:
        """
        Generate all features for a prediction.
        
        Args:
            symbol: Trading symbol
            order_details: Order details dictionary
            
        Returns:
            Tuple of (feature_values, feature_names)
        """
        features = {}
        
        # Parallel data fetching
        tasks = []
        
        # Fetch price data
        if self.price_config.get('enabled', True):
            tasks.append(self._fetch_price_data(symbol))
            
        # Fetch VIX data
        if self.vix_config.get('enabled', True):
            tasks.append(self._fetch_vix_data())
        
        # Wait for all data
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        price_data = None
        vix_data = None
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Data fetch failed: {result}")
            else:
                if i == 0:  # Price data
                    price_data = result
                elif i == 1:  # VIX data
                    vix_data = result
        
        # Generate features
        if self.temporal_config.get('enabled', True):
            features.update(self._generate_temporal_features())
            
        if price_data and self.price_config.get('enabled', True):
            features.update(self._generate_price_features(symbol, price_data))
            
        if vix_data and self.vix_config.get('enabled', True):
            features.update(self._generate_vix_features(vix_data))
            
        # Trade features
        features.update(self._generate_trade_features(symbol, order_details))
        
        # Convert to ordered list matching training features
        feature_values, feature_names = self._align_features(features)
        
        return feature_values, feature_names
    
    async def _fetch_price_data(self, symbol: str) -> Dict:
        """Fetch price data for feature generation."""
        # Get historical bars for technical indicators
        bars = await self.data_provider.get_price_data(symbol, bars=100)
        
        # Get current price
        current = await self.data_provider.get_current_price(symbol)
        
        return {
            'bars': bars,
            'current': current
        }
    
    async def _fetch_vix_data(self) -> Dict:
        """Fetch VIX data for feature generation."""
        # Get current VIX
        vix_current = await self.data_provider.get_vix_data()
        
        # Get VIX history for SMA
        vix_bars = await self.data_provider.get_price_data('VIX', bars=30)
        
        return {
            'current': vix_current,
            'bars': vix_bars
        }
    
    def _generate_temporal_features(self) -> Dict[str, float]:
        """Generate temporal features (9 features)."""
        features = {}
        now = datetime.now()
        
        # Basic time features
        features['hour'] = now.hour
        features['minute'] = now.minute
        features['day_of_week'] = now.weekday()
        
        # Cyclical encoding
        hour_angle = 2 * math.pi * now.hour / 24
        features['hour_sin'] = math.sin(hour_angle)
        features['hour_cos'] = math.cos(hour_angle)
        
        minute_angle = 2 * math.pi * now.minute / 60
        features['minute_sin'] = math.sin(minute_angle)
        features['minute_cos'] = math.cos(minute_angle)
        
        # Market session indicators
        market_open = time(9, 30)
        market_close = time(16, 0)
        current_time = now.time()
        
        features['is_market_hours'] = float(
            market_open <= current_time <= market_close
        )
        
        # Minutes to close (important for 0DTE)
        if features['is_market_hours']:
            close_minutes = 16 * 60  # 4:00 PM
            current_minutes = now.hour * 60 + now.minute
            features['minutes_to_close'] = max(0, close_minutes - current_minutes)
        else:
            features['minutes_to_close'] = 0
            
        return features
    
    def _generate_price_features(
        self,
        symbol: str,
        price_data: Dict
    ) -> Dict[str, float]:
        """Generate price-based features (5-6 per symbol)."""
        features = {}
        
        bars = price_data['bars']
        current = price_data['current']
        
        if not bars:
            logger.warning(f"No price bars available for {symbol}")
            return features
        
        # Convert to DataFrame for easier calculation
        df = pd.DataFrame(bars)
        df['time'] = pd.to_datetime(df['time'])
        df.set_index('time', inplace=True)
        
        # Current price
        current_price = current['last']
        features[f'{symbol}_price'] = current_price
        
        # SMA features
        for period in self.price_config.get('sma_periods', [20]):
            if len(df) >= period:
                sma = df['close'].rolling(window=period).mean().iloc[-1]
                features[f'{symbol}_sma_{period}'] = sma
                features[f'{symbol}_price_vs_sma_{period}'] = (
                    (current_price - sma) / sma * 100
                )
        
        # Momentum
        for period in self.price_config.get('momentum_periods', [5]):
            if len(df) >= period:
                momentum = (current_price - df['close'].iloc[-period]) / df['close'].iloc[-period] * 100
                features[f'{symbol}_momentum_{period}'] = momentum
        
        # Volatility (20-period)
        if len(df) >= 20:
            returns = df['close'].pct_change().dropna()
            volatility = returns.tail(20).std() * math.sqrt(252)  # Annualized
            features[f'{symbol}_volatility_20'] = volatility
        
        # RSI
        rsi_period = self.price_config.get('rsi_period', 14)
        if len(df) >= rsi_period + 1:
            rsi = self._calculate_rsi(df['close'], rsi_period)
            features[f'{symbol}_rsi_{rsi_period}'] = rsi
        
        # Price position in range
        if len(df) >= 20:
            high_20 = df['high'].tail(20).max()
            low_20 = df['low'].tail(20).min()
            if high_20 > low_20:
                price_position = (current_price - low_20) / (high_20 - low_20)
                features[f'{symbol}_price_position_20'] = price_position
        
        return features
    
    def _generate_vix_features(self, vix_data: Dict) -> Dict[str, float]:
        """Generate VIX-based features (6-8 features)."""
        features = {}
        
        current = vix_data['current']
        bars = vix_data['bars']
        
        # Current VIX level
        vix_level = current['last']
        features['vix_level'] = vix_level
        
        # VIX change
        features['vix_change'] = current.get('change', 0)
        features['vix_change_pct'] = current.get('change_pct', 0)
        
        # VIX SMA
        if bars and len(bars) >= self.vix_config.get('sma_period', 20):
            df = pd.DataFrame(bars)
            vix_sma = df['close'].tail(20).mean()
            features['vix_sma_20'] = vix_sma
            features['vix_vs_sma'] = (vix_level - vix_sma) / vix_sma * 100
        
        # VIX regime
        thresholds = self.vix_config.get('regime_thresholds', [15, 20, 25])
        if vix_level < thresholds[0]:
            regime = 0  # Low
        elif vix_level < thresholds[1]:
            regime = 1  # Normal
        elif vix_level < thresholds[2]:
            regime = 2  # Elevated
        else:
            regime = 3  # High
            
        features['vix_regime'] = regime
        
        # One-hot encode regime
        for i in range(4):
            features[f'vix_regime_{i}'] = float(regime == i)
        
        return features
    
    def _generate_trade_features(
        self,
        symbol: str,
        order_details: Dict
    ) -> Dict[str, float]:
        """Generate trade-specific features (8-10 features)."""
        features = {}
        
        # Strategy one-hot encoding
        strategy = order_details.get('strategy', 'Unknown')
        strategies = ['Butterfly', 'Iron Condor', 'Vertical']
        
        for strat in strategies:
            features[f'strategy_{strat}'] = float(strategy == strat)
        
        # Premium normalized by price (if available)
        premium = order_details.get('premium', 0)
        if premium and 'current_price' in features:
            features['premium_normalized'] = premium / features.get(f'{symbol}_price', 1)
        else:
            features['premium_normalized'] = 0
        
        # Risk-reward ratio
        risk = order_details.get('risk', 0)
        reward = order_details.get('reward', 0)
        if risk and reward:
            features['risk_reward_ratio'] = reward / risk
        else:
            features['risk_reward_ratio'] = 0
        
        # Trade probability (if provided)
        features['trade_probability'] = order_details.get('probability', 0.5)
        
        # Strike distance for single-leg strategies
        if strategy == 'Vertical':
            strikes = order_details.get('strikes', [])
            if len(strikes) >= 2 and f'{symbol}_price' in features:
                current_price = features[f'{symbol}_price']
                avg_strike = sum(strikes[:2]) / 2
                features['strike_distance_pct'] = (
                    (avg_strike - current_price) / current_price * 100
                )
        
        # Expiry features (for 0DTE)
        expiry = order_details.get('expiry')
        if expiry:
            expiry_date = datetime.strptime(expiry, '%Y-%m-%d').date()
            today = datetime.now().date()
            features['is_0dte'] = float(expiry_date == today)
        else:
            features['is_0dte'] = 0
        
        return features
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def _align_features(
        self,
        features: Dict[str, float]
    ) -> Tuple[List[float], List[str]]:
        """
        Align features with training feature order.
        
        Returns:
            Tuple of (feature_values, feature_names)
        """
        # Define feature order matching Phase 1 training
        feature_order = [
            # Temporal features
            'hour', 'minute', 'day_of_week',
            'hour_sin', 'hour_cos', 'minute_sin', 'minute_cos',
            'is_market_hours', 'minutes_to_close',
            
            # Price features (for main symbol)
            'SPX_price', 'SPX_sma_20', 'SPX_price_vs_sma_20',
            'SPX_momentum_5', 'SPX_volatility_20', 'SPX_rsi_14',
            'SPX_price_position_20',
            
            # VIX features
            'vix_level', 'vix_change', 'vix_change_pct',
            'vix_sma_20', 'vix_vs_sma',
            'vix_regime', 'vix_regime_0', 'vix_regime_1',
            'vix_regime_2', 'vix_regime_3',
            
            # Trade features
            'strategy_Butterfly', 'strategy_Iron Condor', 'strategy_Vertical',
            'premium_normalized', 'risk_reward_ratio', 'trade_probability',
            'strike_distance_pct', 'is_0dte'
        ]
        
        # Extract values in order, using 0 for missing features
        feature_values = []
        feature_names = []
        
        for feature_name in feature_order:
            if feature_name in features:
                feature_values.append(features[feature_name])
                feature_names.append(feature_name)
            else:
                # Handle symbol-specific features
                if feature_name.startswith('SPX_'):
                    # Try with actual symbol
                    symbol = list(features.keys())[0].split('_')[0] if features else 'SPX'
                    alt_name = feature_name.replace('SPX_', f'{symbol}_')
                    if alt_name in features:
                        feature_values.append(features[alt_name])
                        feature_names.append(alt_name)
                    else:
                        feature_values.append(0.0)
                        feature_names.append(feature_name)
                else:
                    feature_values.append(0.0)
                    feature_names.append(feature_name)
        
        return feature_values, feature_names
