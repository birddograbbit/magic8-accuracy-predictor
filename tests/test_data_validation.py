import io
from datetime import datetime
from pathlib import Path
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from process_magic8_data_optimized_v2 import Magic8DataProcessorOptimized


def test_duplicate_detection():
    proc = Magic8DataProcessorOptimized(source_path='.', output_path='tests/tmp')
    trade = {
        'date': '2025-01-01',
        'time': '09:35',
        'symbol': 'SPX',
        'strategy': 'Butterfly',
        'premium': 1,
        'profit': 1,
    }
    proc.validate_and_add_trade(trade.copy(), 'file')
    proc.validate_and_add_trade(trade.copy(), 'file')
    assert len(proc.quality_issues['duplicates']) == 1
