#!/usr/bin/env python3
"""
Simple example of using the trained model for predictions
No API needed - direct Python usage
"""

import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime

def load_model_and_config():
    """Load the trained model and feature configuration"""
    
    # Load model
    model = joblib.load('models/xgboost_phase1.pkl')
    
    # Load feature configuration
    with open('data/phase1_processed/feature_info.json', 'r') as f:
        feature_config = json.load(f)
    
    return model, feature_config['feature_names']

def create_features_for_trade(symbol, strategy, premium, predicted_price, current_price=None):
    """
    Create features for a single trade prediction
    
    Parameters:
    - symbol: Trading symbol (e.g., 'SPX', 'SPY')
    - strategy: Strategy name ('Butterfly', 'Iron Condor', 'Vertical', 'Sonar')
    - premium: Option premium
    - predicted_price: Magic8's predicted price
    - current_price: Current market price (if None, uses predicted_price)
    """
    
    if current_price is None:
        current_price = predicted_price
    
    # Initialize feature dataframe
    features = pd.DataFrame(index=[0])
    
    # Time features
    now = datetime.now()
    features['hour'] = now.hour
    features['minute'] = now.minute
    features['day_of_week'] = now.weekday()
    
    # Cyclical time encoding
    features['hour_sin'] = np.sin(2 * np.pi * now.hour / 24)
    features['hour_cos'] = np.cos(2 * np.pi * now.hour / 24)
    features['minute_sin'] = np.sin(2 * np.pi * now.minute / 60)
    features['minute_cos'] = np.cos(2 * np.pi * now.minute / 60)
    
    # Market session features
    market_open = 9.5  # 9:30 AM
    market_close = 16  # 4:00 PM
    current_time = now.hour + now.minute / 60
    
    features['is_open_hour'] = int(market_open <= current_time <= market_open + 1)
    features['is_close_hour'] = int(market_close - 1 <= current_time <= market_close)
    features['minutes_to_close'] = max(0, (market_close - current_time) * 60)
    
    # Create features for all symbols (most will be zero)
    all_symbols = ['SPX', 'SPY', 'RUT', 'QQQ', 'XSP', 'NDX', 'AAPL', 'TSLA']
    
    for sym in all_symbols:
        if sym == symbol:
            # Active symbol gets real values
            features[f'{sym}_price'] = current_price
            features[f'{sym}_sma_20'] = current_price  # Simplified
            features[f'{sym}_momentum_5'] = 0  # No historical data
            features[f'{sym}_volatility_20'] = 0.15 if sym == 'SPX' else 0.20  # Typical values
            features[f'{sym}_rsi_14'] = 50  # Neutral RSI
            features[f'{sym}_price_position'] = 0.5  # Mid-range
        else:
            # Other symbols get zeros
            features[f'{sym}_price'] = 0
            features[f'{sym}_sma_20'] = 0
            features[f'{sym}_momentum_5'] = 0
            features[f'{sym}_volatility_20'] = 0
            features[f'{sym}_rsi_14'] = 0
            features[f'{sym}_price_position'] = 0
    
    # VIX features (using typical values)
    vix_level = 15  # Typical VIX
    features['vix_level'] = vix_level
    features['vix_sma_20'] = vix_level
    features['vix_change_1d'] = 0
    features['vix_change_5d'] = 0
    
    # VIX regime
    features['vix_regime_low'] = int(vix_level < 12)
    features['vix_regime_normal'] = int(12 <= vix_level < 20)
    features['vix_regime_elevated'] = int(20 <= vix_level < 30)
    features['vix_regime_high'] = int(vix_level >= 30)
    
    # Strategy one-hot encoding
    strategies = ['Butterfly', 'Iron Condor', 'Vertical', 'Sonar']
    for strat in strategies:
        features[f'strategy_{strat}'] = int(strategy == strat)
    
    # Trade-specific features
    features['premium'] = premium
    features['premium_pct_of_price'] = (premium / current_price) * 100
    features['predicted_move'] = predicted_price - current_price
    features['predicted_move_pct'] = ((predicted_price - current_price) / current_price) * 100
    
    # Risk/reward ratio (typical values by strategy)
    risk_reward_ratios = {
        'Butterfly': 1.0,
        'Iron Condor': 10.0,
        'Vertical': 5.0,
        'Sonar': 2.0
    }
    features['risk_reward_ratio'] = risk_reward_ratios.get(strategy, 5.0)
    
    # Trade probability (default)
    features['trade_probability'] = 0.5
    
    return features

def predict_trade(model, feature_names, symbol, strategy, premium, predicted_price, current_price=None):
    """
    Make a prediction for a single trade
    
    Returns:
    - Dictionary with prediction results
    """
    
    # Create features
    features_df = create_features_for_trade(symbol, strategy, premium, predicted_price, current_price)
    
    # Ensure we have all required features in the right order
    for feature in feature_names:
        if feature not in features_df.columns:
            features_df[feature] = 0
    
    # Select only the features the model expects
    features_df = features_df[feature_names]
    
    # Make prediction
    win_probability = model.predict_proba(features_df)[0, 1]
    prediction = 'WIN' if win_probability >= 0.5 else 'LOSS'
    confidence = max(win_probability, 1 - win_probability)
    
    # Get recommendation based on probability
    if win_probability >= 0.7:
        recommendation = "STRONG BUY"
    elif win_probability >= 0.6:
        recommendation = "BUY"
    elif win_probability >= 0.5:
        recommendation = "HOLD"
    elif win_probability < 0.4:
        recommendation = "AVOID"
    else:
        recommendation = "CAUTION"
    
    return {
        'timestamp': datetime.now().isoformat(),
        'symbol': symbol,
        'strategy': strategy,
        'premium': premium,
        'predicted_price': predicted_price,
        'current_price': current_price or predicted_price,
        'win_probability': round(win_probability, 4),
        'prediction': prediction,
        'confidence': round(confidence, 4),
        'recommendation': recommendation
    }

def main():
    """Example usage"""
    
    print("Loading model...")
    model, feature_names = load_model_and_config()
    print(f"Model loaded with {len(feature_names)} features")
    
    # Example trades to predict
    example_trades = [
        {'symbol': 'SPX', 'strategy': 'Butterfly', 'premium': 25.50, 'predicted_price': 5850.00},
        {'symbol': 'SPX', 'strategy': 'Iron Condor', 'premium': 0.65, 'predicted_price': 5850.00},
        {'symbol': 'SPY', 'strategy': 'Vertical', 'premium': 0.75, 'predicted_price': 585.00},
        {'symbol': 'QQQ', 'strategy': 'Butterfly', 'premium': 3.20, 'predicted_price': 490.00},
        {'symbol': 'SPX', 'strategy': 'Sonar', 'premium': 15.00, 'predicted_price': 5850.00}
    ]
    
    print("\n" + "="*80)
    print("PREDICTIONS")
    print("="*80)
    
    for trade in example_trades:
        result = predict_trade(
            model=model,
            feature_names=feature_names,
            symbol=trade['symbol'],
            strategy=trade['strategy'],
            premium=trade['premium'],
            predicted_price=trade['predicted_price']
        )
        
        print(f"\n{trade['symbol']} {trade['strategy']} @ ${trade['premium']}")
        print(f"  Prediction: {result['prediction']}")
        print(f"  Win Probability: {result['win_probability']:.2%}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Recommendation: {result['recommendation']}")
    
    # Example: Filter trades by recommendation
    print("\n" + "="*80)
    print("FILTERING TRADES")
    print("="*80)
    
    approved_trades = []
    for trade in example_trades:
        result = predict_trade(model, feature_names, **trade)
        
        if result['recommendation'] in ['BUY', 'STRONG BUY']:
            approved_trades.append(trade)
            print(f"✅ APPROVED: {trade['symbol']} {trade['strategy']} "
                  f"(confidence: {result['confidence']:.2%})")
        else:
            print(f"❌ REJECTED: {trade['symbol']} {trade['strategy']} "
                  f"(win prob: {result['win_probability']:.2%})")
    
    print(f"\nApproved {len(approved_trades)} out of {len(example_trades)} trades")
    
    # Example: Batch processing
    print("\n" + "="*80)
    print("BATCH PROCESSING EXAMPLE")
    print("="*80)
    
    # Simulate getting 100 trades from Magic8
    import random
    
    symbols = ['SPX', 'SPY', 'QQQ', 'RUT']
    strategies = ['Butterfly', 'Iron Condor', 'Vertical', 'Sonar']
    
    batch_trades = []
    for _ in range(100):
        symbol = random.choice(symbols)
        strategy = random.choice(strategies)
        
        # Realistic premiums by strategy
        if strategy == 'Butterfly':
            premium = random.uniform(15, 35)
        elif strategy == 'Iron Condor':
            premium = random.uniform(0.3, 1.5)
        elif strategy == 'Vertical':
            premium = random.uniform(0.5, 2.0)
        else:  # Sonar
            premium = random.uniform(10, 25)
        
        batch_trades.append({
            'symbol': symbol,
            'strategy': strategy,
            'premium': round(premium, 2),
            'predicted_price': 5850.00 if symbol == 'SPX' else 585.00
        })
    
    # Process batch
    start_time = datetime.now()
    results = []
    
    for trade in batch_trades:
        result = predict_trade(model, feature_names, **trade)
        results.append(result)
    
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    
    # Summarize results
    wins = sum(1 for r in results if r['prediction'] == 'WIN')
    buys = sum(1 for r in results if r['recommendation'] in ['BUY', 'STRONG BUY'])
    
    print(f"Processed {len(batch_trades)} trades in {processing_time:.2f} seconds")
    print(f"Average time per trade: {processing_time/len(batch_trades)*1000:.2f} ms")
    print(f"Predicted wins: {wins}/{len(batch_trades)} ({wins/len(batch_trades):.2%})")
    print(f"Recommended trades: {buys}/{len(batch_trades)} ({buys/len(batch_trades):.2%})")

if __name__ == "__main__":
    main()
