#!/bin/bash

# Download IBKR Data for Phase 1 - Magic8 Accuracy Predictor
# This script downloads historical price data for all required symbols

echo "Magic8 Accuracy Predictor - Phase 1 Data Download"
echo "================================================"
echo "This script will download historical data from IBKR for all symbols"
echo ""

# Check if data directory exists
mkdir -p data/ibkr

# Set default values
PORT=7497
DURATION="3 Y"
BAR_SIZE="5 mins"

# Allow override from command line
if [ ! -z "$1" ]; then
    PORT=$1
fi

echo "Using IBKR Gateway/TWS port: $PORT"
echo "Duration: $DURATION"
echo "Bar size: $BAR_SIZE"
echo ""

# List of symbols to download
SYMBOLS=(
    "INDEX:SPX"      # S&P 500 Index
    "INDEX:VIX"      # Volatility Index
    "STOCK:SPY"      # S&P 500 ETF
    "INDEX:RUT"      # Russell 2000
    "INDEX:NDX"      # NASDAQ-100
    "STOCK:QQQ"      # NASDAQ-100 ETF
    "INDEX:XSP"      # Mini S&P 500
    "STOCK:AAPL"     # Apple
    "STOCK:TSLA"     # Tesla
)

echo "Symbols to download: ${#SYMBOLS[@]}"
echo "Starting download..."
echo ""

# Download each symbol
for symbol in "${SYMBOLS[@]}"
do
    echo "----------------------------------------"
    echo "Downloading: $symbol"
    echo "----------------------------------------"
    
    python ibkr_downloader.py \
        --symbols "$symbol" \
        --bar_sizes "$BAR_SIZE" \
        --duration "$DURATION" \
        --port $PORT
    
    # Check if download was successful
    if [ $? -eq 0 ]; then
        echo "✓ Successfully downloaded $symbol"
    else
        echo "✗ Failed to download $symbol"
    fi
    
    # Small delay between downloads to avoid rate limiting
    sleep 2
done

echo ""
echo "========================================="
echo "Download process completed!"
echo "========================================="
echo ""

# Move downloaded files to the correct directory
echo "Moving files to data/ibkr/..."
mv data/historical_data_*.csv data/ibkr/ 2>/dev/null

# List downloaded files
echo ""
echo "Downloaded files:"
ls -la data/ibkr/historical_data_*.csv 2>/dev/null | wc -l
echo ""
ls -la data/ibkr/historical_data_*.csv 2>/dev/null

echo ""
echo "Next steps:"
echo "1. Run the Phase 1 data preparation:"
echo "   python src/phase1_data_preparation.py"
echo ""
echo "2. Train the XGBoost baseline model:"
echo "   python src/models/xgboost_baseline.py"
