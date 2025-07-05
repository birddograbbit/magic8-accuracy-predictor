"""Option spread risk/reward calculator."""
from typing import List, Dict


class RiskRewardCalculator:
    """Calculate max profit/loss and breakevens for option spreads."""

    def __init__(self, multiplier: int = 100):
        self.multiplier = multiplier

    def calculate_butterfly(
        self, strikes: List[float], premium: float, action: str, quantity: int = 1
    ) -> Dict[str, float]:
        """Calculate risk/reward for a butterfly spread."""
        spread_width = strikes[1] - strikes[0]

        if action.upper() == "BUY":
            max_loss = premium * self.multiplier * quantity
            max_profit = (spread_width - premium) * self.multiplier * quantity
        else:
            max_profit = premium * self.multiplier * quantity
            max_loss = (spread_width - premium) * self.multiplier * quantity

        breakeven_lower = strikes[0] + premium
        breakeven_upper = strikes[2] - premium

        return {
            "max_profit": max_profit,
            "max_loss": -abs(max_loss),
            "risk_reward_ratio": abs(max_profit / max_loss) if max_loss != 0 else 0,
            "breakeven_lower": breakeven_lower,
            "breakeven_upper": breakeven_upper,
        }

    def calculate_iron_condor(
        self, strikes: List[float], premium: float, action: str, quantity: int = 1
    ) -> Dict[str, float]:
        """Calculate risk/reward for an iron condor."""
        put_spread_width = strikes[1] - strikes[0]
        call_spread_width = strikes[3] - strikes[2]
        max_spread_width = max(put_spread_width, call_spread_width)

        if action.upper() == "SELL":
            max_profit = premium * self.multiplier * quantity
            max_loss = (max_spread_width - premium) * self.multiplier * quantity
        else:
            max_loss = premium * self.multiplier * quantity
            max_profit = (max_spread_width - premium) * self.multiplier * quantity

        breakeven_lower = strikes[1] - premium
        breakeven_upper = strikes[2] + premium

        return {
            "max_profit": max_profit,
            "max_loss": -abs(max_loss),
            "risk_reward_ratio": abs(max_profit / max_loss) if max_loss != 0 else 0,
            "breakeven_lower": breakeven_lower,
            "breakeven_upper": breakeven_upper,
        }

    def calculate_vertical(
        self,
        strikes: List[float],
        premium: float,
        action: str,
        option_type: str,
        quantity: int = 1,
    ) -> Dict[str, float]:
        """Calculate risk/reward for a vertical spread."""
        spread_width = abs(strikes[1] - strikes[0])

        if action.upper() == "SELL":
            max_profit = premium * self.multiplier * quantity
            max_loss = (spread_width - premium) * self.multiplier * quantity
        else:
            max_loss = premium * self.multiplier * quantity
            max_profit = (spread_width - premium) * self.multiplier * quantity

        if option_type.upper() == "PUT":
            breakeven = strikes[0] - premium
        else:
            breakeven = strikes[0] + premium

        return {
            "max_profit": max_profit,
            "max_loss": -abs(max_loss),
            "risk_reward_ratio": abs(max_profit / max_loss) if max_loss != 0 else 0,
            "breakeven": breakeven,
        }
