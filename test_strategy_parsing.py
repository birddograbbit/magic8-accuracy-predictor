#!/usr/bin/env python3
"""
Quick test script to verify the strategy parsing fix
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

def test_strategy_parsing():
    """Test parsing strategies from a few sample files."""
    source_path = Path("/Users/jt/magic8/magic8-accuracy-predictor/data/source")
    
    # Test folders from different periods
    test_folders = [
        "2023-01-25-E370D",  # Early 2023
        "2024-06-10-2CD32",  # Mid 2024
        "2025-01-15-26F27",  # Recent with trades file
    ]
    
    results = {}
    
    for folder_name in test_folders:
        folder_path = source_path / folder_name
        if not folder_path.exists():
            print(f"Folder {folder_name} not found")
            continue
            
        print(f"\nTesting {folder_name}:")
        results[folder_name] = {
            'profit_strategies': defaultdict(int),
            'trades_strategies': defaultdict(int),
            'sonar_examples': []
        }
        
        # Check profit file
        profit_files = list(folder_path.glob("profit*.csv"))
        if profit_files:
            with open(profit_files[0], 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'Name' in row and row.get('Symbol') in ['SPX', 'SPY', 'RUT', 'QQQ', 'XSP', 'NDX', 'AAPL', 'TSLA']:
                        strategy = row['Name']
                        results[folder_name]['profit_strategies'][strategy] += 1
                        
                        # Capture Sonar examples
                        if strategy == 'Sonar' and len(results[folder_name]['sonar_examples']) < 3:
                            results[folder_name]['sonar_examples'].append({
                                'Name': row['Name'],
                                'Trade': row.get('Trade', '')[:80] + '...'
                            })
        
        # Check trades file
        trades_files = list(folder_path.glob("trades*.csv"))
        if trades_files:
            with open(trades_files[0], 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'Name' in row and row.get('Symbol') in ['SPX', 'SPY', 'RUT', 'QQQ', 'XSP', 'NDX']:
                        strategy = row['Name']
                        results[folder_name]['trades_strategies'][strategy] += 1
                        
                        # Capture Sonar examples
                        if strategy == 'Sonar' and len(results[folder_name]['sonar_examples']) < 3:
                            results[folder_name]['sonar_examples'].append({
                                'Name': row['Name'],
                                'Trade': row.get('Trade', '')[:80] + '...'
                            })
        
        # Print results for this folder
        print(f"  Profit file strategies: {dict(results[folder_name]['profit_strategies'])}")
        if results[folder_name]['trades_strategies']:
            print(f"  Trades file strategies: {dict(results[folder_name]['trades_strategies'])}")
        
        if results[folder_name]['sonar_examples']:
            print(f"  Sonar trade examples:")
            for ex in results[folder_name]['sonar_examples']:
                print(f"    Name: {ex['Name']}")
                print(f"    Trade: {ex['Trade']}")
    
    # Save results
    with open('strategy_parsing_test.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nResults saved to strategy_parsing_test.json")
    
    # Calculate totals
    all_strategies = defaultdict(int)
    for folder_data in results.values():
        for strategy, count in folder_data['profit_strategies'].items():
            all_strategies[strategy] += count
    
    total = sum(all_strategies.values())
    print(f"\nOverall strategy distribution from test folders:")
    for strategy, count in sorted(all_strategies.items()):
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {strategy}: {count} ({pct:.1f}%)")


if __name__ == "__main__":
    test_strategy_parsing()
