"""
Model wrappers for compatibility between different model formats.
"""

import xgboost as xgb
import numpy as np
from typing import Optional, Dict, Any


class XGBoostModelWrapper:
    """Wrapper for XGBoost model to work with real-time predictor."""
    
    def __init__(self, booster, feature_names, scaler=None):
        self.booster = booster
        self.feature_names = feature_names
        self.scaler = scaler
        self.version = "1.0.0"
    
    def predict_proba(self, X):
        """Predict probabilities in scikit-learn format."""
        # Create DMatrix with feature names to avoid XGBoost warnings
        dmatrix = xgb.DMatrix(X, feature_names=self.feature_names)
        # Get probabilities for positive class
        proba_pos = self.booster.predict(dmatrix)
        # Create two-column format [prob_negative, prob_positive]
        proba_neg = 1 - proba_pos
        return np.column_stack([proba_neg, proba_pos])
    
    def predict(self, X):
        """Predict classes."""
        proba = self.predict_proba(X)
        return (proba[:, 1] > 0.5).astype(int)
    
    def get_booster(self):
        """Get the underlying XGBoost booster."""
        return self.booster
    
    def get_score(self, importance_type='gain'):
        """Get feature importance scores."""
        return self.booster.get_score(importance_type=importance_type)
