#!/usr/bin/env python3
"""
Magic8 Trading Data Comprehensive Analysis Script
Analyzes the normalized trading data to understand actual performance
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

class Magic8DataAnalyzer:
    def __init__(self, data_path='/Users/jt/magic8/magic8-accuracy-predictor/data/normalized/normalized_aggregated.csv'):
        self.data_path = Path(data_path)
        self.df = None
        self.results = {}
        
    def load_data(self):
        """Load the normalized aggregated data"""
        print(f"Loading data from: {self.data_path}")
        self.df = pd.read_csv(self.data_path)
        print(f"Loaded {len(self.df):,} trades")
        
        # Convert timestamp to datetime
        if 'timestamp' in self.df.columns:
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'], errors='coerce')
        
        return self
    
    def analyze_overall_performance(self):
        """Analyze overall trading performance"""
        print("\n" + "="*60)
        print("OVERALL PERFORMANCE ANALYSIS")
        print("="*60)
        
        # Total trades
        total_trades = len(self.df)
        
        # Trades with profit data
        profit_trades = self.df[self.df['profit'].notna()]
        trades_with_profit = len(profit_trades)
        
        # Win rate
        if 'win' in self.df.columns:
            overall_win_rate = self.df['win'].mean()
        else:
            # Calculate win based on profit > 0
            self.df['win'] = (self.df['profit'] > 0).astype(int)
            overall_win_rate = profit_trades['win'].mean()
        
        # Profit statistics
        total_profit = profit_trades['profit'].sum()
        avg_profit = profit_trades['profit'].mean()
        median_profit = profit_trades['profit'].median()
        
        # Win/Loss statistics
        wins = profit_trades[profit_trades['profit'] > 0]
        losses = profit_trades[profit_trades['profit'] <= 0]
        
        avg_win = wins['profit'].mean() if len(wins) > 0 else 0
        avg_loss = losses['profit'].mean() if len(losses) > 0 else 0
        
        # Date range
        if 'timestamp' in self.df.columns:
            date_range = f"{self.df['timestamp'].min()} to {self.df['timestamp'].max()}"
        else:
            date_range = "Unknown"
        
        results = {
            'total_trades': total_trades,
            'trades_with_profit_data': trades_with_profit,
            'overall_win_rate': overall_win_rate,
            'total_profit': total_profit,
            'average_profit_per_trade': avg_profit,
            'median_profit': median_profit,
            'average_win_amount': avg_win,
            'average_loss_amount': avg_loss,
            'total_wins': len(wins),
            'total_losses': len(losses),
            'date_range': date_range
        }
        
        print(f"Total Trades: {total_trades:,}")
        print(f"Trades with Profit Data: {trades_with_profit:,} ({trades_with_profit/total_trades*100:.1f}%)")
        print(f"Overall Win Rate: {overall_win_rate:.1%}")
        print(f"Total Profit: ${total_profit:,.2f}")
        print(f"Average Profit per Trade: ${avg_profit:.2f}")
        print(f"Median Profit: ${median_profit:.2f}")
        print(f"Average Win: ${avg_win:.2f}")
        print(f"Average Loss: ${avg_loss:.2f}")
        print(f"Date Range: {date_range}")
        
        self.results['overall'] = results
        return self
    
    def analyze_by_strategy(self):
        """Analyze performance by strategy"""
        print("\n" + "="*60)
        print("STRATEGY-SPECIFIC ANALYSIS")
        print("="*60)
        
        strategies = ['Butterfly', 'Iron Condor', 'Sonar', 'Vertical']
        strategy_results = {}
        
        for strategy in strategies:
            mask = self.df['strategy'] == strategy
            strategy_df = self.df[mask]
            
            if len(strategy_df) == 0:
                print(f"\n{strategy}: No data found")
                continue
            
            # Get trades with profit data
            profit_df = strategy_df[strategy_df['profit'].notna()]
            
            if len(profit_df) == 0:
                print(f"\n{strategy}: No profit data available")
                continue
            
            total_trades = len(strategy_df)
            trades_with_profit = len(profit_df)
            win_rate = (profit_df['profit'] > 0).mean()
            
            # Profit statistics
            total_profit = profit_df['profit'].sum()
            avg_profit = profit_df['profit'].mean()
            
            # Win/Loss breakdown
            wins = profit_df[profit_df['profit'] > 0]
            losses = profit_df[profit_df['profit'] <= 0]
            
            avg_win = wins['profit'].mean() if len(wins) > 0 else 0
            avg_loss = losses['profit'].mean() if len(losses) > 0 else 0
            max_win = wins['profit'].max() if len(wins) > 0 else 0
            max_loss = losses['profit'].min() if len(losses) > 0 else 0
            
            # Expected value
            expected_value = win_rate * avg_win + (1 - win_rate) * avg_loss
            
            # Profit distribution
            profit_percentiles = profit_df['profit'].quantile([0.05, 0.25, 0.5, 0.75, 0.95]).to_dict()
            
            strategy_results[strategy] = {
                'total_trades': total_trades,
                'trades_with_profit': trades_with_profit,
                'win_rate': win_rate,
                'total_profit': total_profit,
                'avg_profit': avg_profit,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'max_win': max_win,
                'max_loss': max_loss,
                'expected_value': expected_value,
                'profit_percentiles': profit_percentiles,
                'win_count': len(wins),
                'loss_count': len(losses)
            }
            
            print(f"\n{strategy} Analysis:")
            print(f"  Total trades: {total_trades:,}")
            print(f"  Win rate: {win_rate:.1%}")
            print(f"  Total profit: ${total_profit:,.0f}")
            print(f"  Avg profit per trade: ${avg_profit:.0f}")
            print(f"  Avg win: ${avg_win:.0f}")
            print(f"  Avg loss: ${avg_loss:.0f}")
            print(f"  Max win: ${max_win:.0f}")
            print(f"  Max loss: ${max_loss:.0f}")
            print(f"  Expected value: ${expected_value:.2f}")
            print(f"  Profit distribution (5th/25th/50th/75th/95th percentile):")
            print(f"    ${profit_percentiles[0.05]:.0f} / ${profit_percentiles[0.25]:.0f} / "
                  f"${profit_percentiles[0.5]:.0f} / ${profit_percentiles[0.75]:.0f} / "
                  f"${profit_percentiles[0.95]:.0f}")
        
        self.results['strategies'] = strategy_results
        return self
    
    def check_profit_consistency(self):
        """Check if profit amounts match expected patterns"""
        print("\n" + "="*60)
        print("PROFIT CONSISTENCY CHECK")
        print("="*60)
        
        # Expected profit/loss profiles
        expected_profiles = {
            'Butterfly': {'win': 2000, 'loss': -100},
            'Iron Condor': {'win': 50, 'loss': -450},
            'Sonar': {'win': 90, 'loss': -810},
            'Vertical': {'win': 100, 'loss': -300}
        }
        
        for strategy, profile in expected_profiles.items():
            strategy_df = self.df[self.df['strategy'] == strategy]
            profit_df = strategy_df[strategy_df['profit'].notna()]
            
            if len(profit_df) == 0:
                continue
            
            # Find most common profit/loss values
            wins = profit_df[profit_df['profit'] > 0]['profit']
            losses = profit_df[profit_df['profit'] < 0]['profit']
            
            if len(wins) > 0:
                common_wins = wins.value_counts().head(5)
                print(f"\n{strategy} - Most common win amounts:")
                for amount, count in common_wins.items():
                    print(f"  ${amount:.0f}: {count} times ({count/len(wins)*100:.1f}%)")
            
            if len(losses) > 0:
                common_losses = losses.value_counts().head(5)
                print(f"{strategy} - Most common loss amounts:")
                for amount, count in common_losses.items():
                    print(f"  ${amount:.0f}: {count} times ({count/len(losses)*100:.1f}%)")
            
            # Check if actual values match expected
            print(f"Expected: Win=${profile['win']}, Loss=${profile['loss']}")
        
        return self
    
    def analyze_temporal_patterns(self):
        """Analyze win rates over time"""
        print("\n" + "="*60)
        print("TEMPORAL ANALYSIS")
        print("="*60)
        
        if 'timestamp' not in self.df.columns:
            print("No timestamp data available for temporal analysis")
            return self
        
        # Add month column
        self.df['month'] = self.df['timestamp'].dt.to_period('M')
        
        # Monthly win rates
        monthly_stats = []
        for month in self.df['month'].dropna().unique():
            month_df = self.df[self.df['month'] == month]
            profit_df = month_df[month_df['profit'].notna()]
            
            if len(profit_df) > 0:
                win_rate = (profit_df['profit'] > 0).mean()
                total_profit = profit_df['profit'].sum()
                trade_count = len(profit_df)
                
                monthly_stats.append({
                    'month': str(month),
                    'win_rate': win_rate,
                    'total_profit': total_profit,
                    'trade_count': trade_count
                })
        
        if monthly_stats:
            monthly_df = pd.DataFrame(monthly_stats).sort_values('month')
            print("\nMonthly Performance (last 12 months):")
            for _, row in monthly_df.tail(12).iterrows():
                print(f"  {row['month']}: Win Rate={row['win_rate']:.1%}, "
                      f"Profit=${row['total_profit']:,.0f}, Trades={row['trade_count']}")
        
        self.results['monthly_stats'] = monthly_stats
        return self
    
    def save_analysis_report(self, output_dir='data/analysis'):
        """Save comprehensive analysis report"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save JSON report
        report_path = output_path / 'trading_data_analysis.json'
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\nAnalysis report saved to: {report_path}")
        
        # Create summary report
        summary = []
        summary.append("MAGIC8 TRADING DATA ANALYSIS SUMMARY")
        summary.append("=" * 60)
        summary.append(f"Generated: {datetime.now()}")
        summary.append("")
        
        if 'overall' in self.results:
            o = self.results['overall']
            summary.append("OVERALL PERFORMANCE:")
            summary.append(f"  Total Trades: {o['total_trades']:,}")
            summary.append(f"  Win Rate: {o['overall_win_rate']:.1%}")
            summary.append(f"  Total Profit: ${o['total_profit']:,.0f}")
            summary.append("")
        
        if 'strategies' in self.results:
            summary.append("STRATEGY PERFORMANCE:")
            for strategy, stats in self.results['strategies'].items():
                summary.append(f"\n{strategy}:")
                summary.append(f"  Win Rate: {stats['win_rate']:.1%} (Expected from docs: varies)")
                summary.append(f"  Avg Win: ${stats['avg_win']:.0f}")
                summary.append(f"  Avg Loss: ${stats['avg_loss']:.0f}")
                summary.append(f"  Expected Value: ${stats['expected_value']:.2f}")
        
        summary_path = output_path / 'analysis_summary.txt'
        with open(summary_path, 'w') as f:
            f.write('\n'.join(summary))
        
        print(f"Summary report saved to: {summary_path}")
        
        return self
    
    def create_visualizations(self, output_dir='data/analysis/plots'):
        """Create analysis visualizations"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 1. Win rate by strategy
        if 'strategies' in self.results:
            strategies = list(self.results['strategies'].keys())
            win_rates = [self.results['strategies'][s]['win_rate'] for s in strategies]
            
            plt.figure(figsize=(10, 6))
            bars = plt.bar(strategies, win_rates)
            
            # Color bars based on performance
            for i, bar in enumerate(bars):
                if win_rates[i] > 0.5:
                    bar.set_color('green')
                else:
                    bar.set_color('red')
            
            plt.axhline(y=0.5, color='black', linestyle='--', alpha=0.5)
            plt.ylabel('Win Rate')
            plt.title('Win Rate by Strategy')
            plt.ylim(0, 1)
            
            # Add value labels
            for i, v in enumerate(win_rates):
                plt.text(i, v + 0.01, f'{v:.1%}', ha='center')
            
            plt.tight_layout()
            plt.savefig(output_path / 'win_rate_by_strategy.png', dpi=300)
            plt.close()
        
        # 2. Profit distribution by strategy
        plt.figure(figsize=(12, 8))
        
        for i, strategy in enumerate(['Butterfly', 'Iron Condor', 'Sonar', 'Vertical']):
            plt.subplot(2, 2, i+1)
            
            strategy_df = self.df[self.df['strategy'] == strategy]
            profit_data = strategy_df[strategy_df['profit'].notna()]['profit']
            
            if len(profit_data) > 0:
                plt.hist(profit_data, bins=50, alpha=0.7, edgecolor='black')
                plt.axvline(x=0, color='red', linestyle='--')
                plt.title(f'{strategy} Profit Distribution')
                plt.xlabel('Profit ($)')
                plt.ylabel('Frequency')
                
                # Add statistics
                mean_profit = profit_data.mean()
                plt.axvline(x=mean_profit, color='green', linestyle='-', 
                           label=f'Mean: ${mean_profit:.0f}')
                plt.legend()
        
        plt.tight_layout()
        plt.savefig(output_path / 'profit_distributions.png', dpi=300)
        plt.close()
        
        print(f"\nVisualizations saved to: {output_path}")
        
        return self


def main():
    """Run comprehensive analysis"""
    analyzer = Magic8DataAnalyzer()
    
    # Run full analysis pipeline
    analyzer.load_data() \
            .analyze_overall_performance() \
            .analyze_by_strategy() \
            .check_profit_consistency() \
            .analyze_temporal_patterns() \
            .save_analysis_report() \
            .create_visualizations()
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE!")
    print("="*60)


if __name__ == "__main__":
    main()