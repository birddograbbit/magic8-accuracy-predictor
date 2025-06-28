# Magic8 Accuracy Predictor

## Project Overview
This project aims to predict the accuracy (win or loss) of Magic8's trading predictions using a hybrid Decision Tree + Transformer architecture. The system analyzes historical trading data to identify patterns based on time of day, day of month, symbol, VIX levels, and stock price levels.

## Data Structure

### Data Sources
The project analyzes trading data from 2022-2025, with the following file types:
- **prediction**: Stock price predictions (UTC timezone)
- **trades**: Executed trades and their outcomes (UTC timezone)
- **delta**: Option delta values (EST timezone)
- **profit**: Profit/loss summaries (EST timezone)

### Key Findings from Data Analysis

#### File Type Distribution
- 13 total CSV files across 5 date folders
- File types: delta (5), prediction (1), profit (4), trades (3)

#### Symbols Traded
- SPX, SPY, XSP (S&P 500 variants)
- NDX, QQQ (Nasdaq variants)
- RUT (Russell 2000)

#### Trading Strategies Found
- Butterfly
- Broken Butterfly
- Iron Condor
- Vertical
- Sonar
- Sniper
- JOIF

### Data Normalization

The data normalization process handles:
1. **Timezone Conversion**: UTC to EST conversion for trades/predictions
2. **Timestamp Formats**: 
   - Single column format: "12-05-2022 14:35:01"
   - Separate columns: Date "09-18-2024" + Time "13:35"
   - Day/Hour columns: Day "01-23-2023" + Hour "09:35"
3. **5-minute Interval Alignment**: All trades normalized to 5-minute intervals from 9:35 AM to 4:00 PM EST

### Output Files

#### 1. normalized_raw.csv
- 10,640 individual records
- All trades with normalized timestamps
- Original field values preserved

#### 2. normalized_aggregated.csv
- 384 unique 5-minute intervals
- Data from all file types merged by interval
- Fields prefixed by type: pred_, trad_, delt_, prof_

#### 3. normalization_stats.json
- Summary statistics
- Date range: 2022-12-05 to 2025-05-15
- Record counts by type and year

## Scripts

### 1. analyze_data_stdlib.py
Analyzes all CSV files to understand structure, columns, and timestamp formats.

```bash
python3 analyze_data_stdlib.py
```

### 2. normalize_data.py
Normalizes all data into consolidated CSV files aligned to 5-minute intervals.

```bash
python3 normalize_data.py
```

## Next Steps

1. **Feature Engineering**
   - Extract VIX data for each trading day
   - Calculate technical indicators
   - Create time-based features (hour of day, day of week, etc.)

2. **Model Development**
   - Implement Decision Tree for market regime classification
   - Build Transformer model for pattern recognition
   - Create ensemble integration layer

3. **Backtesting Framework**
   - Validate predictions against historical data
   - Calculate performance metrics
   - Optimize model parameters

## Installation

```bash
# Clone the repository
git clone https://github.com/birddograbbit/magic8-accuracy-predictor.git

# Install dependencies
pip install -r requirements.txt

# Run data analysis
python3 analyze_data_stdlib.py

# Normalize data
python3 normalize_data.py
```

## Project Structure

```
magic8-accuracy-predictor/
├── data/
│   ├── source/          # Original CSV files by date
│   └── normalized/      # Processed data files
├── analyze_data_stdlib.py
├── normalize_data.py
├── requirements.txt
├── README.md
└── data_analysis_report.md
```

## Key Insights

1. **Trading Schedule**: All trades occur between 9:35 AM and 4:00 PM EST
2. **Multiple Strategies**: Each 5-minute interval may have multiple strategy types
3. **Symbol Coverage**: Focus on major indices (SPX, NDX, RUT) and their ETFs
4. **Data Quality**: Some profit files contain summary rows that need filtering

## Contact

For questions or contributions, please open an issue on GitHub.
