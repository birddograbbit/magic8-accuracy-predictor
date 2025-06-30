#!/usr/bin/env python3
"""
Real-time prediction service for Magic8 trading system
Generates predictions every 5 minutes during market hours
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
from datetime import datetime, time
import time
import os
import json
import logging
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/realtime_predictions.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IBKRDataFetcher(EWrapper, EClient):
    """Fetches real-time market data from IBKR"""
    
    def __init__(self):
        EWrapper.__init__(self)
        EClient.__init__(self, self)
        self.data_queue = queue.Queue()
        self.current_prices = {}
        self.historical_data = {}
        
    def error(self, reqId, errorCode, errorString):
        logger.error(f"Error {errorCode}: {errorString}")
        
    def tickPrice(self, reqId, tickType, price, attrib):
        """Handle real-time price updates"""
        if tickType == 4:  # Last price
            symbol = self.req_id_to_symbol.get(reqId)
            if symbol:
                self.current_prices[symbol] = price
                
    def historicalData(self, reqId, bar):
        """Store historical data for feature calculation"""
        symbol = self.req_id_to_symbol.get(reqId)
        if symbol:
            if symbol not in self.historical_data:
                self.historical_data[symbol] = []
            self.historical_data[symbol].append({
                'time': bar.date,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume
            })

class Magic8Predictor:
    """Real-time prediction engine for Magic8 trades"""
    
    def __init__(self, model_path='models/xgboost_phase1.pkl', 
                 feature_config_path='data/phase1_processed/feature_info.json'):
        """Initialize predictor with trained model and feature configuration"""
        
        # Load model
        self.model = joblib.load(model_path)
        logger.info(f"Loaded model from {model_path}")
        
        # Load feature configuration
        with open(feature_config_path, 'r') as f:
            self.feature_config = json.load(f)
        self.feature_names = self.feature_config['feature_names']
        logger.info(f"Loaded {len(self.feature_names)} features")
        
        # Initialize IBKR connection
        self.ibkr = IBKRDataFetcher()
        self.ibkr.req_id_to_symbol = {}
        
        # Trading parameters
        self.symbols = ['SPX', 'SPY', 'RUT', 'QQQ', 'XSP', 'NDX', 'AAPL', 'TSLA']
        self.strategies = ['Butterfly', 'Iron Condor', 'Vertical', 'Sonar']
        
        # Market hours (ET)
        self.market_open = time(9, 30)
        self.market_close = time(16, 0)
        
    def connect_to_ibkr(self, host='127.0.0.1', port=7497, client_id=1):
        """Connect to IBKR TWS/Gateway"""
        self.ibkr.connect(host, port, client_id)
        
        # Start the client thread
        api_thread = threading.Thread(target=self.ibkr.run, daemon=True)
        api_thread.start()
        
        # Wait for connection
        time.sleep(2)
        
        # Subscribe to market data
        self._subscribe_market_data()
        logger.info("Connected to IBKR and subscribed to market data")
        
    def _subscribe_market_data(self):
        """Subscribe to real-time data for all symbols"""
        for i, symbol in enumerate(self.symbols):
            contract = Contract()
            
            if symbol in ['SPX', 'RUT', 'NDX', 'XSP']:
                contract.symbol = symbol
                contract.secType = "IND"
                contract.exchange = "CBOE"
                contract.currency = "USD"
            else:  # Stocks
                contract.symbol = symbol
                contract.secType = "STK"
                contract.exchange = "SMART"
                contract.currency = "USD"
            
            # Request real-time data
            self.ibkr.req_id_to_symbol[i] = symbol
            self.ibkr.reqMktData(i, contract, "", False, False, [])
            
            # Request historical data for feature calculation
            self.ibkr.reqHistoricalData(
                i + 100,  # Different request ID
                contract,
                "",  # End datetime (now)
                "1 D",  # Duration
                "5 mins",  # Bar size
                "TRADES",
                0,  # RTH only
                1,  # Date format
                False,  # Keep updated
                []
            )
            
    def calculate_features(self, strategy, symbol, premium, predicted_price):
        """Calculate features for prediction matching the training pipeline"""
        features = pd.DataFrame(index=[0])
        
        # Get current time features
        now = datetime.now()
        features['hour'] = now.hour
        features['minute'] = now.minute
        features['day_of_week'] = now.weekday()
        
        # Cyclical encoding
        features['hour_sin'] = np.sin(2 * np.pi * now.hour / 24)
        features['hour_cos'] = np.cos(2 * np.pi * now.hour / 24)
        features['minute_sin'] = np.sin(2 * np.pi * now.minute / 60)
        features['minute_cos'] = np.cos(2 * np.pi * now.minute / 60)
        
        # Market session indicators
        current_time = now.time()
        features['is_open_hour'] = int(time(9, 30) <= current_time <= time(10, 30))
        features['is_close_hour'] = int(time(15, 0) <= current_time <= time(16, 0))
        features['minutes_to_close'] = (16 * 60) - (now.hour * 60 + now.minute)
        
        # Get current price data
        current_price = self.ibkr.current_prices.get(symbol, predicted_price)
        
        # Price features for each symbol
        for sym in self.symbols:
            if sym == symbol:
                # Features for the traded symbol
                features[f'{sym}_price'] = current_price
                features[f'{sym}_momentum_5'] = 0  # Will calculate from historical
                features[f'{sym}_volatility_20'] = 0  # Will calculate from historical
                features[f'{sym}_rsi_14'] = 50  # Default RSI
                features[f'{sym}_price_position'] = 0.5  # Will calculate
                
                # Calculate from historical data if available
                if sym in self.ibkr.historical_data:
                    hist_data = pd.DataFrame(self.ibkr.historical_data[sym])
                    if len(hist_data) >= 20:
                        # Simple moving average
                        features[f'{sym}_sma_20'] = hist_data['close'].tail(20).mean()
                        
                        # Momentum
                        if len(hist_data) >= 5:
                            features[f'{sym}_momentum_5'] = (
                                current_price / hist_data['close'].iloc[-5] - 1
                            ) * 100
                        
                        # Volatility
                        returns = hist_data['close'].pct_change().dropna()
                        features[f'{sym}_volatility_20'] = returns.tail(20).std() * np.sqrt(252 * 78)
                        
                        # Price position in range
                        high_20 = hist_data['high'].tail(20).max()
                        low_20 = hist_data['low'].tail(20).min()
                        if high_20 > low_20:
                            features[f'{sym}_price_position'] = (current_price - low_20) / (high_20 - low_20)
                else:
                    features[f'{sym}_sma_20'] = current_price
            else:
                # Zero out features for non-traded symbols
                features[f'{sym}_price'] = 0
                features[f'{sym}_sma_20'] = 0
                features[f'{sym}_momentum_5'] = 0
                features[f'{sym}_volatility_20'] = 0
                features[f'{sym}_rsi_14'] = 0
                features[f'{sym}_price_position'] = 0
        
        # VIX features (if available)
        vix_price = self.ibkr.current_prices.get('VIX', 15)  # Default VIX
        features['vix_level'] = vix_price
        features['vix_sma_20'] = vix_price  # Simplified
        features['vix_change_1d'] = 0
        features['vix_change_5d'] = 0
        
        # VIX regime
        if vix_price < 12:
            vix_regime = 'low'
        elif vix_price < 20:
            vix_regime = 'normal'
        elif vix_price < 30:
            vix_regime = 'elevated'
        else:
            vix_regime = 'high'
            
        for regime in ['low', 'normal', 'elevated', 'high']:
            features[f'vix_regime_{regime}'] = int(vix_regime == regime)
        
        # Strategy encoding
        for strat in self.strategies:
            features[f'strategy_{strat}'] = int(strategy == strat)
        
        # Trade-specific features
        features['premium'] = premium
        features['premium_pct_of_price'] = (premium / current_price) * 100
        features['predicted_move'] = predicted_price - current_price
        features['predicted_move_pct'] = ((predicted_price - current_price) / current_price) * 100
        
        # Risk/reward features (simplified for real-time)
        if strategy == 'Butterfly':
            features['risk_reward_ratio'] = 1.0  # Typical for butterfly
        elif strategy == 'Iron Condor':
            features['risk_reward_ratio'] = 10.0  # High risk for IC
        else:
            features['risk_reward_ratio'] = 5.0  # Medium for others
        
        # Trade probability (simplified)
        features['trade_probability'] = 0.5  # Default
        
        # Ensure all required features are present
        for feature in self.feature_names:
            if feature not in features.columns:
                features[feature] = 0
                
        # Select only the features used in training
        features = features[self.feature_names]
        
        return features
    
    def predict_trade(self, strategy, symbol, premium, predicted_price):
        """Generate prediction for a single trade"""
        
        # Calculate features
        features = self.calculate_features(strategy, symbol, premium, predicted_price)
        
        # Make prediction
        win_probability = self.model.predict_proba(features)[0, 1]
        prediction = self.model.predict(features)[0]
        
        # Get feature importance for this prediction
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            top_features_idx = np.argsort(importances)[-5:][::-1]
            top_features = [
                (self.feature_names[i], importances[i]) 
                for i in top_features_idx
            ]
        else:
            top_features = []
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'strategy': strategy,
            'symbol': symbol,
            'premium': premium,
            'predicted_price': predicted_price,
            'current_price': self.ibkr.current_prices.get(symbol, predicted_price),
            'win_probability': float(win_probability),
            'prediction': 'WIN' if prediction == 1 else 'LOSS',
            'confidence': max(win_probability, 1 - win_probability),
            'top_features': top_features
        }
        
        return result
    
    def predict_magic8_orders(self, orders):
        """Predict outcomes for a batch of Magic8 orders"""
        predictions = []
        
        for order in orders:
            try:
                pred = self.predict_trade(
                    strategy=order['strategy'],
                    symbol=order['symbol'],
                    premium=order['premium'],
                    predicted_price=order['predicted_price']
                )
                predictions.append(pred)
                
            except Exception as e:
                logger.error(f"Error predicting order {order}: {e}")
                
        return predictions
    
    def run_prediction_loop(self, order_source_func, output_path='predictions/'):
        """Run continuous prediction loop during market hours"""
        
        os.makedirs(output_path, exist_ok=True)
        
        while True:
            now = datetime.now()
            current_time = now.time()
            
            # Check if market is open
            if self.market_open <= current_time <= self.market_close:
                try:
                    # Get pending orders from Magic8 system
                    # This function should be implemented to fetch orders
                    pending_orders = order_source_func()
                    
                    if pending_orders:
                        logger.info(f"Processing {len(pending_orders)} orders")
                        
                        # Generate predictions
                        predictions = self.predict_magic8_orders(pending_orders)
                        
                        # Save predictions
                        output_file = os.path.join(
                            output_path,
                            f"predictions_{now.strftime('%Y%m%d_%H%M%S')}.json"
                        )
                        with open(output_file, 'w') as f:
                            json.dump(predictions, f, indent=2)
                            
                        logger.info(f"Saved {len(predictions)} predictions to {output_file}")
                        
                        # Log summary
                        win_preds = sum(1 for p in predictions if p['prediction'] == 'WIN')
                        avg_confidence = np.mean([p['confidence'] for p in predictions])
                        logger.info(f"Summary: {win_preds}/{len(predictions)} WIN predictions, "
                                  f"avg confidence: {avg_confidence:.2%}")
                        
                except Exception as e:
                    logger.error(f"Error in prediction loop: {e}")
                    
            else:
                logger.info("Market closed, waiting...")
                
            # Wait 5 minutes
            time.sleep(300)
            
def example_order_source():
    """Example function to simulate getting orders from Magic8
    In production, this would connect to Magic8's order generation system"""
    
    # Simulate some orders
    orders = [
        {
            'strategy': 'Butterfly',
            'symbol': 'SPX',
            'premium': 25.50,
            'predicted_price': 5850.00
        },
        {
            'strategy': 'Iron Condor',
            'symbol': 'SPX',
            'premium': 0.65,
            'predicted_price': 5850.00
        }
    ]
    
    # In production, this would:
    # 1. Connect to Magic8's database or API
    # 2. Fetch pending orders that need predictions
    # 3. Return them in the expected format
    
    return orders

def main():
    """Main entry point for real-time prediction service"""
    
    # Initialize predictor
    predictor = Magic8Predictor()
    
    # Connect to IBKR
    predictor.connect_to_ibkr()
    
    # Run prediction loop
    # In production, replace example_order_source with actual Magic8 integration
    predictor.run_prediction_loop(example_order_source)
    
if __name__ == "__main__":
    main()
