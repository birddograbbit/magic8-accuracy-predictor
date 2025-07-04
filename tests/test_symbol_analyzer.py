from src.symbol_analyzer import SymbolSpecificAnalyzer

def test_recommend_model_grouping():
    analyzer = SymbolSpecificAnalyzer()
    groups = {
        'large_scale': ['NDX', 'RUT'],
        'medium_scale': ['SPX', 'SPY', 'QQQ', 'XSP'],
        'small_scale': ['AAPL']
    }
    rec = analyzer.recommend_model_grouping(groups)
    assert 'NDX' in rec['separate_models']
    assert rec['grouped_models']['medium_scale'] == ['SPX', 'SPY', 'QQQ', 'XSP']
    assert rec['unified_model'] == ['AAPL']
