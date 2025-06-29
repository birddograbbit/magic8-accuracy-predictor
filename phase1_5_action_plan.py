#!/usr/bin/env python3
"""
Phase 1.5 Action Plan - Fix model to focus on market conditions
"""

import os
import sys

def print_header(text):
    print("\n" + "="*60)
    print(text)
    print("="*60)

def main():
    print_header("MAGIC8 ACCURACY PREDICTOR - PHASE 1.5 ACTION PLAN")
    
    print("\nCURRENT STATUS:")
    print("- Phase 1 technically complete but functionally unsuccessful")
    print("- Model accuracy: 49.34% (random chance)")
    print("- Issue: Model using trade magnitude (risk/reward) instead of market conditions")
    
    print_header("UNDERSTANDING THE PROBLEM")
    print("""
The model is confusing trade SIZE with trade PROBABILITY:
- prof_reward and prof_risk dominate feature importance
- These only determine how much you win/lose, not whether you win/lose
- A $50 max profit butterfly isn't more likely to win than a $30 one

We need to focus on WHEN trades win, not HOW MUCH they win by.
""")
    
    print_header("IMMEDIATE ACTIONS (This Week)")
    
    print("\n1. ANALYZE FEATURE PREDICTIVENESS")
    print("   Run: python analyze_feature_predictiveness.py")
    print("   This will show which features actually correlate with wins")
    
    print("\n2. REBUILD DATA WITH CORRECT FEATURES")
    print("   Run: python src/phase1_data_preparation_v2.py")
    print("   This removes/transforms risk/reward and adds interaction features")
    
    print("\n3. RETRAIN WITH BETTER PARAMETERS")
    print("   Create improved XGBoost with:")
    print("   - Lower max_depth (3 instead of 5)")
    print("   - Class weights for imbalanced data")
    print("   - More early stopping rounds")
    
    print_header("KEY FEATURES TO FOCUS ON")
    
    print("\nTEMPORAL PATTERNS:")
    print("- Hour of day (market open vs close behavior)")
    print("- Day of week (Monday/Friday effects)")
    print("- Minutes to close (0DTE decay acceleration)")
    print("- Time × VIX interactions")
    
    print("\nMARKET CONDITIONS:")
    print("- VIX level and recent changes")
    print("- Price position vs moving averages")
    print("- Recent volatility and momentum")
    print("- RSI and other technical indicators")
    
    print("\nSTRATEGY CONTEXT:")
    print("- Strategy type (Butterfly, Iron Condor, Vertical)")
    print("- Premium normalized by underlying price")
    print("- Days to expiration (if not all 0DTE)")
    
    print_header("EXPECTED IMPROVEMENTS")
    
    print("\nWith correct features, expect:")
    print("- 55-65% accuracy (up from 49%)")
    print("- Distributed feature importance")
    print("- Better generalization to test data")
    print("- Insights about WHEN to trade")
    
    print_header("PHASE 1.5 MILESTONES")
    
    print("\nWeek 1: Feature Engineering")
    print("[ ] Run feature predictiveness analysis")
    print("[ ] Identify top 10-15 predictive features")
    print("[ ] Create interaction features")
    print("[ ] Remove/transform magnitude features")
    
    print("\nWeek 2: Model Optimization")
    print("[ ] Hyperparameter tuning with Optuna")
    print("[ ] Try LightGBM and CatBoost")
    print("[ ] Implement time-based cross-validation")
    print("[ ] Create ensemble if individual models > 55%")
    
    print("\nWeek 3: Analysis & Insights")
    print("[ ] Performance by time period")
    print("[ ] Feature importance analysis")
    print("[ ] Create trading rules from insights")
    print("[ ] Document findings")
    
    print_header("SUCCESS CRITERIA")
    
    print("\nBefore moving to Phase 2:")
    print("✓ Validation accuracy > 58%")
    print("✓ Test accuracy > 55%")
    print("✓ Feature importance distributed (no single feature > 30%)")
    print("✓ Clear insights about when trades win")
    
    print_header("COMMANDS TO RUN NOW")
    
    print("\n# 1. Analyze current features")
    print("python analyze_feature_predictiveness.py")
    
    print("\n# 2. Rebuild with correct features")
    print("python src/phase1_data_preparation_v2.py")
    
    print("\n# 3. Retrain model")
    print("python src/models/xgboost_baseline.py")
    
    print("\n# 4. Compare results")
    print("python compare_model_results.py")
    
    print("\n" + "="*60)
    print("Remember: We're predicting IF trades win, not HOW MUCH they win!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
