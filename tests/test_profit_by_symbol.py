import pandas as pd
import numpy as np
from src.models.xgboost_baseline import XGBoostBaseline

class DummyModel:
    def predict(self, dmatrix):
        n = dmatrix.num_row()
        return np.array([1]*n)


def make_model():
    model = XGBoostBaseline()
    df = pd.DataFrame({
        'feature1': [0, 1],
        'symbol': ['NDX', 'XSP'],
        'profit': [100, 10],
        'target': [1, 0],
    })
    model.test_df = df
    model.X_test = df[['feature1']]
    model.y_test = df['target']
    model.model = DummyModel()
    return model


def test_profit_by_symbol():
    m = make_model()
    res = m.evaluate_profit_by_symbol()
    assert res['NDX']['model_profit'] == 100
    assert res['XSP']['model_profit'] == 10

