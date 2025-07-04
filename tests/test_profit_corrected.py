import pandas as pd
import numpy as np
import types
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models.xgboost_baseline import XGBoostBaseline

class StubModel:
    def predict(self, dmatrix):
        n = dmatrix.num_row()
        return np.array([1] * n)

def make_model():
    model = XGBoostBaseline()
    df = pd.DataFrame({
        'feature1': [0,1],
        'profit': [10,-5],
        'target': [1,0],
    })
    model.test_df = df
    model.X_test = df[['feature1']]
    model.y_test = df['target']
    model.model = StubModel()
    return model

def test_profit_impact_corrected():
    m = make_model()
    res = m.evaluate_profit_impact_corrected()
    assert res['baseline_profit'] == 5
    assert res['model_profit'] == 5
