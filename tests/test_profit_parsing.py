import io
from datetime import datetime
from pathlib import Path
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from process_magic8_data_optimized_v2 import Magic8DataProcessorOptimized


def create_processor():
    return Magic8DataProcessorOptimized(source_path='.', output_path='tests/tmp', batch_size=1000)


def test_profit_parsing_2023():
    csv_data = "Day,Hour,Symbol,Price,Name,Predicted,Closed,Risk,Reward,Premium,Stop,Raw,Managed,Trade,Profit\n2023-12-01,10:00,SPX,4500,Iron Condor,0,0,0,0,0,0,1,2,desc,5"
    proc = create_processor()
    proc.process_profit_2023_format(io.StringIO(csv_data), datetime(2023, 12, 1), Path('file.csv'))
    assert proc.current_batch[0]['profit'] == 5


def test_profit_parsing_2024():
    csv_data = "Day,Hour,Symbol,Price,Name,Predicted,Closed,Risk,Reward,Premium,Stop,Raw,Managed,Trade\n2024-01-02,09:40,SPX,4500,Iron Condor,0,0,0,0,0,0,5,2,desc"
    proc = create_processor()
    proc.process_profit_2024_format(io.StringIO(csv_data), datetime(2024, 1, 2), Path('file.csv'))
    assert proc.current_batch[0]['profit'] == 5


def test_profit_parsing_2025():
    csv_data = "Date,Hour,Symbol,Price,Name,Predicted,Low,High,Closing,Risk,ExpectedPremium,ActualPremium,Raw,Managed,Trade,Profit,TotalProfit\n2025-02-03,10:30,SPX,4500,Iron Condor,0,0,0,0,0,0,0,1,2,desc,7,7"
    proc = create_processor()
    proc.process_profit_2025_format(io.StringIO(csv_data), datetime(2025, 2, 3), Path('file.csv'))
    assert proc.current_batch[0]['profit'] == 7


def test_missing_profit_logged():
    csv_data = "Day,Hour,Symbol,Price,Name,Predicted,Closed,Risk,Reward,Premium,Stop,Trade\n2024-01-02,09:40,SPX,4500,Iron Condor,0,0,0,0,0,0,desc"
    proc = create_processor()
    proc.process_profit_2024_format(io.StringIO(csv_data), datetime(2024, 1, 2), Path('file.csv'))
    assert proc.quality_issues['missing_profit']
