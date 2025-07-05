from src.risk_reward_calculator import RiskRewardCalculator


def test_butterfly_calculation():
    calc = RiskRewardCalculator()
    result = calc.calculate_butterfly([50, 55, 60], 2.0, "BUY", 1)
    assert result["max_profit"] == 300.0
    assert result["max_loss"] == -200.0
    assert result["breakeven_lower"] == 52.0
    assert result["breakeven_upper"] == 58.0


def test_iron_condor_calculation():
    calc = RiskRewardCalculator()
    result = calc.calculate_iron_condor([50, 55, 65, 70], 3.0, "SELL", 1)
    assert result["max_profit"] == 300.0
    assert result["max_loss"] == -200.0
    assert result["breakeven_lower"] == 52.0
    assert result["breakeven_upper"] == 68.0


def test_vertical_calculation():
    calc = RiskRewardCalculator()
    result = calc.calculate_vertical([55, 60], 1.5, "SELL", "CALL", 1)
    assert result["max_profit"] == 150.0
    assert result["max_loss"] == -350.0
    assert result["breakeven"] == 56.5
