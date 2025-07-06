import re
from typing import Dict, List

from src.risk_reward_calculator import RiskRewardCalculator


def _extract_number(line: str) -> float | None:
    match = re.search(r"[-+]?\d*\.?\d+", line.split(":")[-1])
    return float(match.group()) if match else None


def _parse_trade_instruction(line: str) -> Dict | None:
    action_match = re.search(r"\b(BUY|SELL)\b", line, re.IGNORECASE)
    if not action_match:
        return None
    action = action_match.group(1).upper()

    qty_match = re.search(r"\b(?:BUY|SELL)\s+(\d+)", line, re.IGNORECASE)
    quantity = int(qty_match.group(1)) if qty_match else 1

    strategy = None
    for s in ["Butterfly", "Iron Condor", "Sonar", "Vertical"]:
        if s in line:
            strategy = s
            break
    if not strategy:
        return None

    strikes_match = re.search(r"(\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)+)", line)
    strikes: List[float] = [float(x) for x in strikes_match.group(1).split("/")] if strikes_match else []

    premium_match = re.search(r"for\s+([0-9]*\.?[0-9]+)", line)
    premium = float(premium_match.group(1)) if premium_match else 0.0

    option_type = "CALL"
    if "Put" in line or "PUT" in line:
        option_type = "PUT"

    trade = {
        "action": action,
        "quantity": quantity,
        "strategy": strategy,
        "strikes": strikes,
        "premium": premium,
    }
    if strategy == "Vertical":
        trade["option_type"] = option_type
    return trade


def parse_magic8_message_enhanced(message: str) -> Dict:
    """Parse Magic8 Discord messages and calculate risk/reward."""
    result: Dict[str, Dict] = {"metadata": {}, "predictions": {}, "trades": []}
    lines = message.split("\n")
    calc = RiskRewardCalculator()

    for line in lines:
        if "Price:" in line:
            result["predictions"]["current_price"] = _extract_number(line)
        elif "Predicted Close:" in line:
            result["predictions"]["predicted_close"] = _extract_number(line)
        elif "Short term:" in line and "bias" not in line:
            result["predictions"]["short_term"] = _extract_number(line)
        elif "Long term:" in line and "bias" not in line:
            result["predictions"]["long_term"] = _extract_number(line)
        elif "Target 1:" in line:
            result["predictions"]["target1"] = _extract_number(line)
        elif "Target 2:" in line:
            result["predictions"]["target2"] = _extract_number(line)
        elif any(s in line for s in ["Butterfly", "Iron Condor", "Sonar", "Vertical"]):
            trade = _parse_trade_instruction(line)
            if trade:
                if trade["strategy"] == "Butterfly":
                    rr = calc.calculate_butterfly(trade["strikes"], trade["premium"], trade["action"], trade["quantity"])
                elif trade["strategy"] in ["Iron Condor", "Sonar"]:
                    rr = calc.calculate_iron_condor(trade["strikes"], trade["premium"], trade["action"], trade["quantity"])
                else:
                    rr = calc.calculate_vertical(
                        trade["strikes"], trade["premium"], trade["action"], trade["option_type"], trade["quantity"]
                    )
                trade.update(rr)
                if "short_term" in result["predictions"]:
                    trade["short_term"] = result["predictions"]["short_term"]
                if "long_term" in result["predictions"]:
                    trade["long_term"] = result["predictions"]["long_term"]
                result["trades"].append(trade)
    return result
