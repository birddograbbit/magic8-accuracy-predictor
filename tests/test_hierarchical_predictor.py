import numpy as np
from src.models.hierarchical_predictor import HierarchicalPredictor

class DummyModel:
    def __init__(self, value: float):
        self.value = value
    def predict_proba(self, X):
        return [[1 - self.value, self.value] for _ in range(len(X))]


class FeatureLimitedModel(DummyModel):
    def __init__(self, value: float, n_features: int):
        super().__init__(value)
        self.n_features_in_ = n_features

    def predict_proba(self, X):
        assert len(X[0]) == self.n_features_in_
        return super().predict_proba(X)

def test_hierarchy_fallback():
    predictor = HierarchicalPredictor()
    predictor.symbol_strategy_models = {"SPX_Butterfly": DummyModel(0.8)}
    predictor.symbol_models = {"SPX": DummyModel(0.6)}
    predictor.strategy_models = {"Butterfly": DummyModel(0.4)}
    predictor.default_model = DummyModel(0.2)

    assert predictor.predict_proba("SPX", "Butterfly", [[0]])[0][1] == 0.8
    assert predictor.predict_proba("SPX", "Vertical", [[0]])[0][1] == 0.6
    assert predictor.predict_proba("XSP", "Butterfly", [[0]])[0][1] == 0.4
    assert predictor.predict_proba("QQQ", "Vertical", [[0]])[0][1] == 0.2


def test_feature_truncation_warning(caplog):
    predictor = HierarchicalPredictor()
    predictor.symbol_strategy_models = {"SPX_Butterfly": FeatureLimitedModel(0.7, 31)}

    X = [[0] * 85]
    with caplog.at_level("WARNING"):
        proba = predictor.predict_proba("SPX", "Butterfly", np.array(X))[0][1]
        assert "Feature mismatch for SPX_Butterfly" in caplog.text
    assert proba == 0.7

