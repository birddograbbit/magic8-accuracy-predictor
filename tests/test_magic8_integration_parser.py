from magic8_integration import parse_magic8_message_enhanced

sample_message = """Magic8 Alert SPX
Price: 5860
Predicted Close: 5875
Short term: 0.65
Long term: 0.7
Target 1: 5885
Target 2: 5895
SELL 1 SPX 15 NOV 5850/5875/5900 Butterfly for 2.0 credit
"""

def test_parse_magic8_message_enhanced():
    result = parse_magic8_message_enhanced(sample_message)
    assert result["predictions"]["current_price"] == 5860.0
    assert len(result["trades"]) == 1
    trade = result["trades"][0]
    assert trade["strategy"] == "Butterfly"
    assert trade["risk_reward_ratio"] > 0
