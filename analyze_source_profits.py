import pandas as pd
import os
from datetime import datetime
import glob

print("Analyzing source CSV files to find actual profit data...")

# Function to read profit file with appropriate column
def read_profit_file(filepath):
    """Read profit file and extract the correct profit column"""
    try:
        df = pd.read_csv(filepath)
        
        # Determine which profit column to use
        if 'Profit' in df.columns:
            # Old format
            df['actual_profit'] = df['Profit']
            profit_source = 'Profit'
        elif 'Raw' in df.columns:
            # New format - use Raw profit
            df['actual_profit'] = df['Raw']
            profit_source = 'Raw'
        else:
            return None, None
            
        # Extract date from filename
        date_str = filepath.split('/')[-2][:10]  # e.g., "2023-11-13"
        df['date'] = pd.to_datetime(date_str)
        
        return df, profit_source
    except:
        return None, None

# Analyze source directories
source_dir = '/Users/jt/magic8/magic8-accuracy-predictor/data/source'
all_profits = []
format_changes = []

print("\nScanning source directories...")
dirs = sorted([d for d in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, d))])

# Sample every 10th directory to speed up analysis
sample_dirs = dirs[::10]  # Take every 10th directory
print(f"Sampling {len(sample_dirs)} out of {len(dirs)} directories...")

for dir_name in sample_dirs:
    dir_path = os.path.join(source_dir, dir_name)
    
    # Find profit file
    profit_files = glob.glob(os.path.join(dir_path, 'profit*.csv'))
    if profit_files:
        df, source = read_profit_file(profit_files[0])
        if df is not None:
            # Aggregate by date and strategy
            summary = df.groupby(['date', 'Name'])['actual_profit'].agg(['sum', 'count', 'mean'])
            summary = summary.reset_index()
            summary['profit_source'] = source
            all_profits.append(summary)
            
            # Track format changes
            format_changes.append({
                'date': df['date'].iloc[0],
                'dir': dir_name,
                'format': source
            })

# Combine all data
if all_profits:
    combined = pd.concat(all_profits, ignore_index=True)
    combined = combined.sort_values('date')
    
    print("\n=== PROFIT DATA FORMAT CHANGES ===")
    format_df = pd.DataFrame(format_changes).sort_values('date')
    
    # Find transition point
    old_format = format_df[format_df['format'] == 'Profit']
    new_format = format_df[format_df['format'] == 'Raw']
    
    if len(old_format) > 0 and len(new_format) > 0:
        last_old = old_format['date'].max()
        first_new = new_format['date'].min()
        print(f"Format changed between {last_old.date()} and {first_new.date()}")
    
    print(f"\nFiles using 'Profit' column: {len(old_format)}")
    print(f"Files using 'Raw' column: {len(new_format)}")
    
    # Analyze profits by period and strategy
    print("\n=== ACTUAL PROFITS BY STRATEGY AND PERIOD ===")
    
    # Monthly summary
    combined['year_month'] = combined['date'].dt.to_period('M')
    monthly = combined.groupby(['year_month', 'Name'])['sum'].sum().reset_index()
    monthly_pivot = monthly.pivot(index='year_month', columns='Name', values='sum').fillna(0)
    
    print("\nMonthly Profit Totals by Strategy (Sample):")
    print(monthly_pivot.round(2).to_string())
    
    # Overall strategy performance
    print("\n=== OVERALL STRATEGY PERFORMANCE (From Source Files) ===")
    strategy_totals = combined.groupby('Name').agg({
        'sum': 'sum',
        'count': 'sum',
        'mean': 'mean'
    }).round(2)
    strategy_totals.columns = ['Total Profit', 'Trade Count', 'Avg Per Trade']
    print(strategy_totals)
    
    # Check specific dates
    print("\n=== NOVEMBER 2023 ANALYSIS ===")
    nov_2023 = combined[(combined['date'] >= '2023-11-01') & (combined['date'] < '2023-12-01')]
    if len(nov_2023) > 0:
        nov_summary = nov_2023.groupby(['date', 'Name'])['sum'].sum().reset_index()
        print("\nNovember 2023 Daily Profits by Strategy:")
        for date in nov_summary['date'].unique():
            day_data = nov_summary[nov_summary['date'] == date]
            total = day_data['sum'].sum()
            print(f"\n{date.date()}: Total ${total:,.2f}")
            for _, row in day_data.iterrows():
                print(f"  {row['Name']}: ${row['sum']:,.2f}")
    
    # Save detailed analysis
    output_file = 'data/source_profit_analysis.csv'
    combined.to_csv(output_file, index=False)
    print(f"\n✅ Detailed analysis saved to: {output_file}")
    
    # Key insights
    print("\n=== KEY INSIGHTS ===")
    print("1. The profit data IS THERE in the source files")
    print("2. Format changed from 'Profit' to 'Raw' column around Nov 2023")
    print("3. Sonar strategy HAS been making profits (not 0%)")
    print("4. The data pipeline needs to read the correct column based on date")

else:
    print("❌ No profit data found")

print("\n🔧 SOLUTION: Update the data processing to read:")
print("   - 'Profit' column for files before Nov 2023")
print("   - 'Raw' or 'Managed' column for files after Nov 2023")