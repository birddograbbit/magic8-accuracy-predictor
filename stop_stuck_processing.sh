#!/bin/bash

# Helper script to stop stuck data processing

echo "Magic8 Data Processing - Process Killer"
echo "======================================"
echo ""
echo "This script helps stop the stuck data processing script."
echo ""

# Find python processes related to data processing
echo "Looking for stuck data processing scripts..."
echo ""

# Show running python processes with magic8 data processing
ps aux | grep -E "python.*process_magic8_data" | grep -v grep

echo ""
echo "To kill the stuck process, use one of these methods:"
echo ""
echo "1. Press Ctrl+C in the terminal where the script is running"
echo ""
echo "2. Or find the process ID (PID) from above and run:"
echo "   kill -9 <PID>"
echo ""
echo "3. Or kill all python processes related to magic8 (BE CAREFUL):"
echo "   pkill -f 'python.*process_magic8_data'"
echo ""
echo "After stopping the old process, run the new optimized version:"
echo "   chmod +x run_data_processing_optimized.sh"
echo "   ./run_data_processing_optimized.sh"
echo ""
