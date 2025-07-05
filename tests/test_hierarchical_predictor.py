from src.models.hierarchical_predictor import HierarchicalPredictor

class DummyModel:
    def __init__(self, value: float):
        self.value = value
    def predict_proba(self, X):
        return [[1 - self.value, self.value] for _ in range(len(X))]

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
