# Magic8 Accuracy Predictor - Project Summary for Next Chat

## Project Overview
Building a machine learning system to predict win/loss outcomes for Magic8's 0DTE options trading system using XGBoost and historical market data.

**Repository**: https://github.com/birddograbbit/magic8-accuracy-predictor

## Critical Discovery (June 29, 2025)
The model was using trade magnitude features (prof_reward, prof_risk) to predict outcomes, but these only determine HOW MUCH you win/lose, not WHETHER you win/lose. A butterfly with $50 max profit isn't more likely to win than one with $30 max profit.

**Key Insight**: We need to predict WHEN trades win (market conditions), not HOW MUCH they win by (trade structure).

## Current Status: Phase 1.5 - Refocusing on Market Conditions

### Phase 1 Results
- **Test Accuracy**: 49.34% (random chance)
- **Problem**: Model dominated by prof_reward/prof_risk features
- **Root Cause**: Confusing trade size with trade probability

### What We've Learned
1. **prof_reward/prof_risk are NOT predictive** - they're just the max profit/loss of the options structure
2. **Temporal distribution shift exists** - strategy improved over time (21% → 50% win rate)
3. **Market conditions matter most** - time of day, VIX levels, technical indicators

### New Files Created
1. `src/phase1_data_preparation_v2.py` - Removes magnitude bias, focuses on market conditions
2. `analyze_feature_predictiveness.py` - Shows which features actually predict wins
3. `phase1_5_action_plan.py` - Detailed roadmap for fixes

## Phase 1.5 Action Plan (3 Weeks)

### Week 1: Feature Engineering ✨
Focus on features available at trade entry that indicate market conditions:
- **Temporal**: Hour, day of week, minutes to close, time × VIX interactions
- **Market State**: VIX level/changes, price vs moving averages, RSI, momentum
- **Microstructure**: Recent volatility, volume patterns
- **Remove/Transform**: prof_reward, prof_risk (or convert to buckets)

### Week 2: Model Optimization 🎯
- Hyperparameter tuning with Optuna
- Try LightGBM and CatBoost
- Implement proper time-based cross-validation
- Address class imbalance with weights

### Week 3: Analysis & Insights 📊
- Performance by time period
- Feature importance analysis
- Extract trading rules from model insights
- Create evaluation notebooks

## Commands for Next Session

```bash
# 1. Analyze which features actually predict wins
python analyze_feature_predictiveness.py

# 2. Rebuild data with correct features
python src/phase1_data_preparation_v2.py

# 3. Retrain model
python src/models/xgboost_baseline.py

# 4. View the action plan
python phase1_5_action_plan.py
```

## Success Metrics for Phase 1.5
- **Validation accuracy > 58%** (up from 53%)
- **Test accuracy > 55%** (up from 49%)
- **No single feature > 30% importance** (currently prof_reward has 1930!)
- **Clear insights about when to trade**

## Key Technical Fixes Needed

1. **Feature Selection**
   - Remove prof_reward, prof_risk from features
   - Add time × market condition interactions
   - Focus on technical indicators

2. **Model Configuration**
   ```python
   params = {
       'max_depth': 3,  # Reduce from 5
       'learning_rate': 0.01,  # Reduce from 0.1
       'scale_pos_weight': 3.7,  # Handle class imbalance
       'n_estimators': 1000,
       'early_stopping_rounds': 50
   }
   ```

3. **Data Handling**
   - Consider using only recent 18-24 months
   - Implement time-based cross-validation
   - Stratify by time periods

## Expected Outcomes
With correct features focusing on market conditions:
- 55-65% accuracy (achievable)
- Insights about best times to trade
- Understanding of VIX impact
- Day of week patterns

## Remember
**We're predicting IF trades win, not HOW MUCH they win!**

The model needs to learn patterns like:
- "Trades at 10 AM on high VIX days tend to lose"
- "Friday afternoon trades with RSI > 70 tend to win"
- "First 30 minutes after open are unpredictable"

NOT patterns like:
- "Trades with $50 reward are different from $30 reward"

---

**Last Updated**: June 29, 2025  
**Current Phase**: Phase 1.5 (Feature Engineering)  
**Next Milestone**: Achieve 55%+ test accuracy with market condition features
