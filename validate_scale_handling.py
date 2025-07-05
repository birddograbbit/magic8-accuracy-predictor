#!/usr/bin/env python3
"""Utility to validate 76x profit scale difference using sample data."""
from pathlib import Path
from symbol_analysis_report import generate_symbol_report


def main():
    input_file = Path('data/analysis/sample_trades.csv')
    output_dir = 'data/analysis'
    if not input_file.exists():
        # Create a tiny sample dataset
        import pandas as pd
        df = pd.DataFrame({
            'symbol': ['NDX']*3 + ['XSP']*3,
            'profit': [3800, 4000, 3600, 40, 60, 50],
            'date': ['2025-07-01']*6,
            'time': ['10:00']*6,
            'strategy': ['Butterfly']*6,
        })
        df.to_csv(input_file, index=False)

    report = generate_symbol_report(str(input_file), output_dir)
    ratio = report.get('scale_ratio')
    print(f"Scale ratio: {ratio}")


if __name__ == '__main__':
    main()
