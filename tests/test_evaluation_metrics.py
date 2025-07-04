import numpy as np
import pandas as pd
import types

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models.xgboost_baseline import XGBoostBaseline

class StubModel:
    def __init__(self, preds):
        self.preds = preds
    def predict(self, dmatrix):
        n = dmatrix.num_row()
        return np.array(self.preds[:n])

def make_baseline():
    model = XGBoostBaseline()
    # Minimal data with two strategies
    df = pd.DataFrame({
        'feature1': [0, 1, 2, 3],
        'strategy_Iron Condor': [1, 0, 1, 0],
        'strategy_Butterfly': [0, 1, 0, 1],
        'target': [1, 0, 0, 1],
    })
    model.test_df = df.copy()
    model.X_test = df[['feature1']]
    model.y_test = df['target']
    model.model = StubModel([0.6, 0.6, 0.4, 0.2])
    return model

def test_enhanced_strategy_metrics():
    bl = make_baseline()
    results = bl.evaluate_by_strategy_enhanced()
    ic = results['Iron Condor']
    bf = results['Butterfly']
    assert ic['accuracy'] == 0.5
    assert bf['accuracy'] == 0.5
    assert ic['confusion_matrix'] == [[0,1],[0,1]]
    assert bf['confusion_matrix'] == [[0,1],[0,1]]

def test_profit_impact():
    bl = make_baseline()
    prof = bl.evaluate_profit_impact()
    # Baseline profit is zero in this setup
    assert prof['baseline_profit'] == 0
    # Model profit = 50 (IC win) + (-100) (BF loss)
    assert prof['model_profit'] == 1500

