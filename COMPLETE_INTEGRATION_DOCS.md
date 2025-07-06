# Complete Integration Docs

## 11. Enhanced ML Predictor Integration

This update introduces an improved parser used by DiscordTrading. The new
`parse_magic8_message_enhanced` function extracts prediction lines and trade
instructions from raw Discord messages and calculates risk/reward for each
instruction. Use it in place of the older parser.

### Usage

1. Import the parser in your DiscordTrading bot:
   ```python
   from magic8_integration import parse_magic8_message_enhanced
   ```
2. When a message is received, call:
   ```python
   parsed_message = parse_magic8_message_enhanced(content)
   ```
3. The returned dictionary contains `predictions` and a list of `trades` with
   risk/reward details.

This function wraps the logic from `src/enhanced_discord_parser.py` and keeps
trade analysis in a single place for easier integration.
