"""
Comprehensive diagnostic of Phase 1 model issues
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, auc, precision_recall_curve
import json
import warnings
warnings.filterwarnings('ignore')

def diagnose_model_issues():
    print("Phase 1 Model Diagnostic")
    print("=" * 60)
    
    # 1. Load the data
    print("\n1. DATA ANALYSIS")
    print("-" * 40)
    
    train_df = pd.read_csv('data/phase1_processed/train_data.csv')
    val_df = pd.read_csv('data/phase1_processed/val_data.csv')
    test_df = pd.read_csv('data/phase1_processed/test_data.csv')
    
    print(f"Train size: {len(train_df):,}")
    print(f"Val size: {len(val_df):,}")
    print(f"Test size: {len(test_df):,}")
    
    # Check class distribution
    print("\nClass distribution:")
    for name, df in [('Train', train_df), ('Val', val_df), ('Test', test_df)]:
        if 'target' in df.columns:
            counts = df['target'].value_counts()
            print(f"{name}: Class 0={counts.get(0, 0):,}, Class 1={counts.get(1, 0):,}, "
                  f"Win rate={df['target'].mean():.2%}")
    
    # 2. Feature Analysis
    print("\n2. FEATURE ANALYSIS")
    print("-" * 40)
    
    # Load feature info
    with open('data/phase1_processed/feature_info.json', 'r') as f:
        feature_info = json.load(f)
    
    print(f"Number of features: {feature_info['n_features']}")
    print(f"Features: {feature_info['features'][:10]}...")  # Show first 10
    
    # Check for constant features
    feature_cols = [col for col in train_df.columns if col not in ['target', 'prof_strategy_name']]
    
    print("\nChecking for problematic features:")
    constant_features = []
    low_variance_features = []
    
    for col in feature_cols:
        if col in train_df.columns:
            unique_vals = train_df[col].nunique()
            variance = train_df[col].var()
            
            if unique_vals == 1:
                constant_features.append(col)
            elif variance < 0.01:
                low_variance_features.append((col, variance))
    
    print(f"Constant features: {len(constant_features)}")
    if constant_features:
        print(f"  {constant_features[:5]}...")
    
    print(f"Low variance features: {len(low_variance_features)}")
    if low_variance_features:
        for feat, var in low_variance_features[:5]:
            print(f"  {feat}: variance={var:.6f}")
    
    # 3. Model Predictions Analysis
    print("\n3. MODEL PREDICTIONS ANALYSIS")
    print("-" * 40)
    
    # Load model predictions if saved
    try:
        import joblib
        from xgboost import XGBClassifier
        import warnings
        warnings.filterwarnings('ignore')
        
        # Load the trained model
        model = joblib.load('models/phase1/xgboost_model.pkl')
        preprocessor = joblib.load('models/phase1/preprocessor.pkl')
        
        # Get predictions
        X_test = test_df[feature_cols]
        X_test_transformed = preprocessor.transform(X_test)
        
        # Get prediction probabilities
        y_pred_proba = model.predict_proba(X_test_transformed)[:, 1]
        y_pred = model.predict(X_test_transformed)
        
        print(f"Unique predictions: {np.unique(y_pred, return_counts=True)}")
        print(f"Probability range: [{y_pred_proba.min():.4f}, {y_pred_proba.max():.4f}]")
        print(f"Probability mean: {y_pred_proba.mean():.4f}")
        print(f"Probability std: {y_pred_proba.std():.4f}")
        
        # Analyze probability distribution
        plt.figure(figsize=(15, 10))
        
        # Plot 1: Probability distribution
        plt.subplot(2, 2, 1)
        plt.hist(y_pred_proba, bins=50, alpha=0.7, edgecolor='black')
        plt.axvline(0.5, color='red', linestyle='--', label='Decision threshold')
        plt.xlabel('Predicted Probability')
        plt.ylabel('Count')
        plt.title('Distribution of Predicted Probabilities')
        plt.legend()
        
        # Plot 2: ROC Curve
        plt.subplot(2, 2, 2)
        fpr, tpr, thresholds = roc_curve(test_df['target'], y_pred_proba)
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, label=f'ROC curve (AUC = {roc_auc:.3f})')
        plt.plot([0, 1], [0, 1], 'k--', label='Random')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curve')
        plt.legend()
        
        # Plot 3: Precision-Recall Curve
        plt.subplot(2, 2, 3)
        precision, recall, thresholds_pr = precision_recall_curve(test_df['target'], y_pred_proba)
        plt.plot(recall, precision)
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('Precision-Recall Curve')
        plt.axhline(test_df['target'].mean(), color='red', linestyle='--', 
                   label=f'Baseline precision: {test_df["target"].mean():.3f}')
        plt.legend()
        
        # Plot 4: Feature importance
        plt.subplot(2, 2, 4)
        feature_names = feature_info['features']
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1][:15]  # Top 15
        
        plt.barh(range(15), importances[indices])
        plt.yticks(range(15), [feature_names[i] for i in indices])
        plt.xlabel('Feature Importance')
        plt.title('Top 15 Feature Importances')
        
        plt.tight_layout()
        plt.savefig('phase1_diagnostic_plots.png', dpi=300, bbox_inches='tight')
        print("\nSaved diagnostic plots to phase1_diagnostic_plots.png")
        
    except Exception as e:
        print(f"Could not load model for prediction analysis: {e}")
    
    # 4. Root Cause Analysis
    print("\n4. ROOT CAUSE ANALYSIS")
    print("-" * 40)
    
    print("\nIDENTIFIED ISSUES:")
    print("1. SEVERE OVERFITTING")
    print("   - Train accuracy: 70.9% vs Test accuracy: 50.2%")
    print("   - Model memorized training patterns but can't generalize")
    print("   - Early stopping too aggressive (iteration 6/100)")
    
    print("\n2. CLASS IMBALANCE HANDLING")
    print("   - Despite scale_pos_weight, model predicts mostly losses")
    print("   - Test set: 4,530 false negatives vs 214 true positives (4.5% recall)")
    
    print("\n3. FEATURE ISSUES")
    if constant_features:
        print(f"   - {len(constant_features)} constant features providing no information")
    if low_variance_features:
        print(f"   - {len(low_variance_features)} low variance features")
    
    print("\n4. TEMPORAL LEAKAGE POTENTIAL")
    print("   - Need to verify no future information in features")
    print("   - Time-based split might have distribution shift")
    
    # 5. Recommendations
    print("\n5. RECOMMENDATIONS")
    print("-" * 40)
    
    recommendations = [
        "IMMEDIATE FIXES:",
        "1. Adjust XGBoost parameters:",
        "   - Increase min_child_weight (try 5-10)",
        "   - Reduce max_depth (try 3-4)",
        "   - Increase reg_alpha and reg_lambda (try 1.0)",
        "   - Set subsample=0.8, colsample_bytree=0.8",
        "",
        "2. Fix early stopping:",
        "   - Increase early_stopping_rounds to 20-30",
        "   - Monitor validation loss, not accuracy",
        "   - Use eval_metric='logloss' or 'auc'",
        "",
        "3. Handle class imbalance better:",
        "   - Try SMOTE or other oversampling techniques",
        "   - Adjust decision threshold based on precision-recall curve",
        "   - Use class_weight='balanced' or tune scale_pos_weight",
        "",
        "4. Feature engineering:",
        "   - Remove constant and low-variance features",
        "   - Add rolling statistics (5-min, 15-min windows)",
        "   - Create interaction features (time × volatility)",
        "",
        "5. Model alternatives:",
        "   - Try LightGBM (handles imbalance better)",
        "   - Ensemble with different algorithms",
        "   - Consider anomaly detection approach"
    ]
    
    for rec in recommendations:
        print(rec)
    
    # Save diagnostic report
    report = {
        'issues': {
            'overfitting': True,
            'class_imbalance': True,
            'constant_features': len(constant_features),
            'low_variance_features': len(low_variance_features),
            'test_accuracy': 0.502,
            'test_recall_class_1': 0.045
        },
        'recommendations': recommendations,
        'feature_issues': {
            'constant': constant_features,
            'low_variance': [f[0] for f in low_variance_features]
        }
    }
    
    with open('phase1_diagnostic_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\nDiagnostic report saved to phase1_diagnostic_report.json")
    
    return report

if __name__ == "__main__":
    diagnose_model_issues()
