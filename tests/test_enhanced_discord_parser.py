from src.enhanced_discord_parser import EnhancedDiscordParser

sample_message = """Magic8 Alert SPX\nPrice: 5860\nPredicted Close: 5875\nShort term: 0.65\nLong term: 0.7\nTarget 1: 5885\nTarget 2: 5895\nSELL 1 SPX 15 NOV 5850/5875/5900 Butterfly for 2.0 credit\nBUY 2 SPX 15 NOV 5800/5900/6000/6100 Iron Condor for 3.5 debit\nSELL 1 SPX 15 NOV 5900/5950 Call Vertical for 1.5 credit\n"""

def test_parse_message():
    parser = EnhancedDiscordParser()
    result = parser.parse_magic8_message(sample_message)
    assert result["predictions"]["current_price"] == 5860.0
    assert len(result["trades"]) == 3
    bfly = result["trades"][0]
    assert bfly["strategy"] == "Butterfly"
    assert bfly["risk_reward_ratio"] > 0
    assert "short_term" in bfly
    assert "long_term" in bfly
