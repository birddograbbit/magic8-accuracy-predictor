#!/usr/bin/env python3
"""
Quick visualization of symbol profit scale differences
"""

import matplotlib.pyplot as plt
import numpy as np

# Approximate profit scales from the analysis
symbol_profits = {
    'Butterfly': {
        'NDX': 3800,
        'RUT': 2500,  # Estimated
        'SPX': 765,
        'SPY': 76,    # Estimated (SPX/10)
        'XSP': 50,
        'QQQ': 75,
        'AAPL': 100,  # Estimated
        'TSLA': 150   # Estimated
    },
    'Iron Condor': {
        'NDX': 500,   # Estimated
        'RUT': 300,   # Estimated
        'SPX': 868,
        'SPY': 87,    # Estimated
        'XSP': 5,
        'QQQ': 10,
        'AAPL': 15,   # Estimated
        'TSLA': 20    # Estimated
    }
}

# Create figure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Butterfly profits
symbols = list(symbol_profits['Butterfly'].keys())
butterfly_values = list(symbol_profits['Butterfly'].values())

bars1 = ax1.bar(symbols, butterfly_values, color='steelblue', alpha=0.8)
ax1.set_title('Butterfly Average Win Amount by Symbol', fontsize=14, fontweight='bold')
ax1.set_ylabel('Average Win ($)', fontsize=12)
ax1.set_xlabel('Symbol', fontsize=12)
ax1.set_yscale('log')  # Log scale due to huge differences

# Add value labels
for bar, value in zip(bars1, butterfly_values):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             f'${value:,.0f}',
             ha='center', va='bottom', fontsize=10)

# Add 76x difference annotation
ax1.annotate('', xy=(0, 3800), xytext=(4, 50),
            arrowprops=dict(arrowstyle='<->', color='red', lw=2))
ax1.text(2, 500, '76x\ndifference!', ha='center', color='red', 
         fontsize=12, fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))

# Iron Condor profits
ic_values = list(symbol_profits['Iron Condor'].values())

bars2 = ax2.bar(symbols, ic_values, color='darkgreen', alpha=0.8)
ax2.set_title('Iron Condor Average Win Amount by Symbol', fontsize=14, fontweight='bold')
ax2.set_ylabel('Average Win ($)', fontsize=12)
ax2.set_xlabel('Symbol', fontsize=12)
ax2.set_yscale('log')

# Add value labels
for bar, value in zip(bars2, ic_values):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             f'${value:,.0f}',
             ha='center', va='bottom', fontsize=10)

# Add scale difference annotation
ax2.annotate('', xy=(2, 868), xytext=(4, 5),
            arrowprops=dict(arrowstyle='<->', color='red', lw=2))
ax2.text(3, 50, '174x\ndifference!', ha='center', color='red', 
         fontsize=12, fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))

plt.suptitle('Symbol Profit Scale Differences Require Different Model Approaches', 
             fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()

# Save figure
plt.savefig('/Users/jt/magic8/magic8-accuracy-predictor/data/analysis/symbol_profit_scales.png', 
            dpi=300, bbox_inches='tight')
plt.close()

# Create a summary text file
summary = """
Symbol Profit Scale Analysis
============================

Butterfly Strategy:
- NDX: ~$3,800 per win (largest)
- SPX: ~$765 per win (baseline)
- XSP: ~$50 per win (smallest)
- Scale difference: 76x between NDX and XSP

Iron Condor Strategy:
- SPX: ~$868 per win
- XSP: ~$5 per win
- Scale difference: 174x

Implications:
1. Cannot use single model for all symbols
2. Need symbol-specific or grouped models
3. Feature normalization critical
4. Profit optimization must be symbol-aware

Recommendations:
- Separate models: NDX, RUT (large scale)
- Grouped model: SPX, SPY (medium scale)
- Grouped model: XSP, QQQ, AAPL, TSLA (small scale)
"""

with open('/Users/jt/magic8/magic8-accuracy-predictor/data/analysis/symbol_scale_analysis.txt', 'w') as f:
    f.write(summary)

print("Symbol profit scale visualization created!")
print(f"Saved to: data/analysis/symbol_profit_scales.png")
print(f"Summary saved to: data/analysis/symbol_scale_analysis.txt")
