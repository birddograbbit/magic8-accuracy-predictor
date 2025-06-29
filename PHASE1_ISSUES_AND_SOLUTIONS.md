# Phase 1 Model Issues and Solutions

## Q1. Identified Problems

### 1. **Critical Model Performance Issues**
- **Test Accuracy: 50.2%** - Model performs at random chance
- **Severe Overfitting**: 70.9% train accuracy vs 50.2% test accuracy
- **Class Imbalance Failure**: Model predicts almost all samples as losses
  - Only 214 true positives out of 4,744 actual wins (4.5% recall)
  - Model learned to maximize accuracy by predicting the majority class

### 2. **Training Issues**
- **Early Stopping Too Aggressive**: Stopped at iteration 6 out of 100
- **Wrong Evaluation Metric**: Using accuracy instead of logloss/AUC
- **Validation Performance Degrading**: AUC dropped from start (0.479 → 0.486)

### 3. **Feature Engineering Problems**
- **VIX Data Loading Failed** in feature analysis script
- **Potential Constant/Low-Variance Features** not filtered
- **No Feature Selection** applied despite having only 32 features

### 4. **Data Quality Issues**
- **Mixed Data Types Warning** in multiple columns
- **Timezone handling** may have issues

### 5. **Model Hyperparameter Issues**
- **Insufficient Regularization**: reg_alpha=0, reg_lambda=1
- **Tree Depth Too High**: max_depth=6 allows overfitting
- **min_child_weight Too Low**: Set to 1, allows fitting to noise

## Q2. Missing Strategy Types

**Expected**: 4 strategies (Butterfly, Iron Condor, Sonar, Vertical)  
**Found**: Only Butterfly (97.1%) and Unknown (0.3%)

### Possible Causes:
1. **Data Issue**: The normalized dataset may only contain Butterfly trades
2. **Naming Mismatch**: Other strategies might be named differently in the data
3. **Data Processing Error**: Other strategies might have been filtered out
4. **Historical Data**: Perhaps only Butterfly strategy was used during this time period

### Investigation Needed:
```bash
# Run this to check strategy distribution
python check_strategies.py
```

## Immediate Action Plan

### Step 1: Investigate Data Issues
```bash
# Check strategy distribution
python check_strategies.py

# Run comprehensive diagnostic
python diagnose_phase1_model.py
```

### Step 2: Fix Model Issues
```bash
# Train improved model with better hyperparameters
python src/models/xgboost_improved.py
```

### Step 3: Key Improvements in New Model
1. **Better Regularization**:
   - max_depth: 6 → 3
   - min_child_weight: 1 → 10
   - reg_alpha: 0 → 1.0
   - reg_lambda: 1 → 2.0

2. **Better Early Stopping**:
   - rounds: 10 → 30
   - metric: default → logloss

3. **Optimal Threshold Selection**:
   - Find best threshold using F1 score on validation set
   - Don't rely on default 0.5 threshold

4. **Feature Cleaning**:
   - Remove constant features
   - Remove low-variance features

## Expected Improvements

With the improved model, you should see:
- **Reduced Overfitting**: Train/test gap should narrow
- **Better Class Balance**: Higher recall for minority class
- **More Stable Training**: Smoother learning curves
- **Better F1 Score**: Currently 0.0828, target > 0.30

## Root Cause Analysis

The fundamental issue is that the model found it easier to achieve high training accuracy by memorizing patterns and defaulting to predicting losses. The 2:1 class imbalance made this strategy "work" during training but fail completely on new data.

The missing strategies suggest either:
1. A data collection issue where only Butterfly trades were included
2. A preprocessing error that filtered out other strategies
3. The actual trading system only used Butterfly during this period

## Next Steps

1. **Run diagnostics**:
   ```bash
   python check_strategies.py
   python diagnose_phase1_model.py
   ```

2. **Train improved model**:
   ```bash
   python src/models/xgboost_improved.py
   ```

3. **If other strategies are truly missing**, consider:
   - Checking the original data source
   - Adjusting the model to work with single-strategy data
   - Planning for multi-strategy models in Phase 2

4. **Consider alternative approaches**:
   - Anomaly detection instead of classification
   - Separate models per strategy (if data becomes available)
   - Time-series specific models (LSTM, Transformer)

The improved model should address most technical issues, but the missing strategy data needs investigation at the source level.
