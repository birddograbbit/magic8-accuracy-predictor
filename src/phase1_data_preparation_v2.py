"""
Modified Phase 1 Data Preparation - Focus on Market Conditions
Removes/transforms risk-reward features to prevent magnitude bias
"""

import pandas as pd
import numpy as np
from phase1_data_preparation import Phase1DataPreparation

class Phase1DataPreparationV2(Phase1DataPreparation):
    """Modified version that focuses on market condition features"""
    
    def select_phase1_features(self):
        """Select features focusing on market conditions, not trade magnitude"""
        
        # Get all available features
        all_features = [col for col in self.df.columns if col not in ['target', 'date', 'time_est']]
        
        # REMOVE risk/reward features that dominate but don't predict probability
        features_to_exclude = ['prof_reward', 'prof_risk', 'risk_reward_ratio']
        
        # OR ALTERNATIVELY: Transform them to categorical buckets
        # self.df['risk_bucket'] = pd.qcut(self.df['prof_risk'], q=5, labels=['very_low', 'low', 'medium', 'high', 'very_high'])
        # self.df['reward_bucket'] = pd.qcut(self.df['prof_reward'], q=5, labels=['very_low', 'low', 'medium', 'high', 'very_high'])
        
        # Focus on these feature groups:
        temporal_features = [f for f in all_features if any(x in f for x in ['hour', 'minute', 'day_of_week', 'minutes_to_close'])]
        
        vix_features = [f for f in all_features if 'vix' in f.lower()]
        
        price_features = [f for f in all_features if any(x in f for x in ['sma', 'momentum', 'volatility', 'rsi', 'price_position'])]
        
        strategy_features = [f for f in all_features if 'strategy_' in f]
        
        # Premium normalized by price is OK - it's a relative measure
        trade_features = ['premium_normalized']
        
        # Combine selected features
        selected_features = (temporal_features + vix_features + price_features + 
                           strategy_features + trade_features)
        
        # Remove excluded features
        selected_features = [f for f in selected_features if f not in features_to_exclude]
        
        # Remove duplicates while preserving order
        selected_features = list(dict.fromkeys(selected_features))
        
        print(f"Selected {len(selected_features)} features for Phase 1 V2")
        print(f"Excluded: {features_to_exclude}")
        
        return selected_features
    
    def add_enhanced_features(self):
        """Add interaction features between time and market conditions"""
        
        # Time of day × VIX regime interaction
        # High VIX at market open behaves differently than high VIX at close
        self.df['morning_high_vix'] = ((self.df['hour'] < 11) & 
                                       (self.df.get('vix_regime_high', 0) == 1)).astype(int)
        
        self.df['afternoon_high_vix'] = ((self.df['hour'] >= 14) & 
                                        (self.df.get('vix_regime_high', 0) == 1)).astype(int)
        
        # Day of week × market conditions
        # Mondays and Fridays often behave differently
        self.df['monday_trade'] = (self.df['day_of_week'] == 0).astype(int)
        self.df['friday_trade'] = (self.df['day_of_week'] == 4).astype(int)
        
        # Time to close buckets (for 0DTE decay acceleration)
        self.df['final_hour'] = (self.df['minutes_to_close'] <= 60).astype(int)
        self.df['final_30min'] = (self.df['minutes_to_close'] <= 30).astype(int)
        
        print("Added enhanced time × market interaction features")


if __name__ == "__main__":
    processor = Phase1DataPreparationV2()
    processor.load_data()
    processor.add_enhanced_features()  # Add this before other features
    processor.engineer_features()
    processor.create_target_variable()
    
    # Rest of pipeline...
    features = processor.select_phase1_features()
    processor.split_data(features)
    processor.save_processed_data()
