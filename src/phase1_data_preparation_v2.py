"""
Modified Phase 1 Data Preparation - Focus on Market Conditions
Removes/transforms risk-reward features to prevent magnitude bias
"""

import pandas as pd
import numpy as np
from phase1_data_preparation import Phase1DataPreparation

class Phase1DataPreparationV2(Phase1DataPreparation):
    """Modified version that focuses on market condition features"""
    
    def select_features(self):
        """Select features focusing on market conditions, not trade magnitude
        
        This overrides the parent method to exclude risk/reward features
        """
        
        # First call parent method to get all available features
        super().select_features()
        
        # Features to exclude that dominate but don't predict probability
        features_to_exclude = ['prof_reward', 'prof_risk', 'risk_reward_ratio']
        
        # Remove excluded features from feature_names
        self.feature_names = [f for f in self.feature_names if f not in features_to_exclude]
        
        print(f"Selected {len(self.feature_names)} features for Phase 1 V2")
        print(f"Excluded: {features_to_exclude}")
        
        return self
    
    def add_enhanced_features(self):
        """Add interaction features between time and market conditions
        
        This should be called AFTER add_basic_temporal_features() and add_vix_features()
        """
        
        # Time of day × VIX regime interaction
        # High VIX at market open behaves differently than high VIX at close
        if 'vix_regime_high' in self.df.columns:
            self.df['morning_high_vix'] = ((self.df['hour'] < 11) & 
                                           (self.df.get('vix_regime_high', 0) == 1)).astype(int)
            
            self.df['afternoon_high_vix'] = ((self.df['hour'] >= 14) & 
                                            (self.df.get('vix_regime_high', 0) == 1)).astype(int)
        
        # Day of week × market conditions
        # Mondays and Fridays often behave differently
        if 'day_of_week' in self.df.columns:
            self.df['monday_trade'] = (self.df['day_of_week'] == 0).astype(int)
            self.df['friday_trade'] = (self.df['day_of_week'] == 4).astype(int)
        
        # Time to close buckets (for 0DTE decay acceleration)
        if 'minutes_to_close' in self.df.columns:
            self.df['final_hour'] = (self.df['minutes_to_close'] <= 60).astype(int)
            self.df['final_30min'] = (self.df['minutes_to_close'] <= 30).astype(int)
        
        print("Added enhanced time × market interaction features")
        
        return self
    
    def run_phase1_pipeline(self):
        """Run the complete Phase 1 V2 data preparation pipeline"""
        
        # Load normalized trade data
        self.load_data()
        
        # Load IBKR historical price data
        self.load_ibkr_data()
        
        # Add features in correct order
        self.add_basic_temporal_features()  # This creates day_of_week
        self.add_price_features()
        self.add_vix_features()
        self.add_trade_features()
        
        # Add enhanced features AFTER basic features exist
        self.add_enhanced_features()
        
        # Create target
        self.create_target_variable()
        
        # Select features (excluding risk/reward)
        self.select_features()
        
        # Split and save
        train_data, val_data, test_data = self.split_data()
        
        return train_data, val_data, test_data


if __name__ == "__main__":
    processor = Phase1DataPreparationV2()
    train_data, val_data, test_data = processor.run_phase1_pipeline()
