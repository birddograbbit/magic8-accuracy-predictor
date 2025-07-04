"""Utilities for analyzing symbol-specific profit patterns."""
from typing import Dict

class SymbolSpecificAnalyzer:
    """Analyze profit scales and recommend model grouping."""

    def analyze_profit_scales(self, symbol_stats: Dict) -> Dict:
        """Group symbols into large, medium and small profit scales."""
        profit_groups = {
            'large_scale': [],
            'medium_scale': [],
            'small_scale': []
        }
        for symbol, stats in symbol_stats.items():
            butterfly_profit = stats.get('profit_by_strategy', {}).get('Butterfly', {}).get('avg_profit', 0)
            if abs(butterfly_profit) > 1000:
                profit_groups['large_scale'].append(symbol)
            elif abs(butterfly_profit) > 100:
                profit_groups['medium_scale'].append(symbol)
            else:
                profit_groups['small_scale'].append(symbol)
        return profit_groups

    def recommend_model_grouping(self, profit_groups: Dict) -> Dict:
        """Recommend model grouping strategy based on profit scales."""
        recommendations = {
            'separate_models': list(profit_groups.get('large_scale', [])),
            'grouped_models': {},
            'unified_model': list(profit_groups.get('small_scale', []))
        }

        medium = profit_groups.get('medium_scale', [])
        if len(medium) > 3:
            recommendations['grouped_models']['medium_scale'] = medium
        else:
            recommendations['separate_models'].extend(medium)

        return recommendations
