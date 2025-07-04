import pandas as pd
import numpy as np


def test_scale_ratio_validation():
    df = pd.DataFrame({
        'symbol': ['NDX']*3 + ['XSP']*3,
        'profit': [3800, 4000, 3600, 40, 60, 50]
    })
    wins_ndx = df[df['symbol'] == 'NDX']['profit'].mean()
    wins_xsp = df[df['symbol'] == 'XSP']['profit'].mean()
    ratio = wins_ndx / wins_xsp
    assert ratio >= 75

