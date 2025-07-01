#!/usr/bin/env python3
"""
Real-time monitoring dashboard for Magic8 Accuracy Predictor.
Shows live prediction statistics and performance metrics.

Usage:
    python monitor_predictions.py [--log-file logs/predictions.jsonl]
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, deque
import argparse
from typing import Dict, List, Any
import os

# Try to import rich for better terminal output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for better dashboard display: pip install rich")


class PredictionMonitor:
    """Monitor and display prediction statistics."""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.predictions = deque(maxlen=1000)  # Keep last 1000 predictions
        self.stats = {
            'total': 0,
            'approved': 0,
            'rejected': 0,
            'errors': 0,
            'by_symbol': defaultdict(lambda: {'total': 0, 'approved': 0}),
            'by_strategy': defaultdict(lambda: {'total': 0, 'approved': 0}),
            'latencies': deque(maxlen=100),
            'win_probs': deque(maxlen=100)
        }
        self.last_position = 0
        
    def read_new_predictions(self):
        """Read new predictions from log file."""
        if not self.log_file.exists():
            return []
        
        new_predictions = []
        
        try:
            with open(self.log_file, 'r') as f:
                # Seek to last position
                f.seek(self.last_position)
                
                for line in f:
                    if line.strip():
                        try:
                            pred = json.loads(line)
                            new_predictions.append(pred)
                            self.predictions.append(pred)
                        except json.JSONDecodeError:
                            pass
                
                # Update position
                self.last_position = f.tell()
                
        except Exception as e:
            print(f"Error reading log: {e}")
        
        return new_predictions
    
    def update_stats(self, predictions: List[Dict[str, Any]]):
        """Update statistics with new predictions."""
        for pred in predictions:
            self.stats['total'] += 1
            
            # Get prediction details
            win_prob = pred.get('win_probability', 0)
            symbol = pred.get('symbol', 'Unknown')
            strategy = pred.get('strategy', 'Unknown')
            latency = pred.get('prediction_time_ms', 0)
            threshold = pred.get('threshold', 0.55)
            
            # Update approval stats
            if win_prob >= threshold:
                self.stats['approved'] += 1
                self.stats['by_symbol'][symbol]['approved'] += 1
                self.stats['by_strategy'][strategy]['approved'] += 1
            else:
                self.stats['rejected'] += 1
            
            # Update symbol and strategy totals
            self.stats['by_symbol'][symbol]['total'] += 1
            self.stats['by_strategy'][strategy]['total'] += 1
            
            # Update metrics
            self.stats['latencies'].append(latency)
            self.stats['win_probs'].append(win_prob)
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        total = self.stats['total']
        if total == 0:
            return {
                'total': 0,
                'approval_rate': 0,
                'avg_win_prob': 0,
                'avg_latency': 0
            }
        
        approval_rate = (self.stats['approved'] / total) * 100
        avg_win_prob = sum(self.stats['win_probs']) / len(self.stats['win_probs']) if self.stats['win_probs'] else 0
        avg_latency = sum(self.stats['latencies']) / len(self.stats['latencies']) if self.stats['latencies'] else 0
        
        return {
            'total': total,
            'approved': self.stats['approved'],
            'rejected': self.stats['rejected'],
            'approval_rate': approval_rate,
            'avg_win_prob': avg_win_prob,
            'avg_latency': avg_latency
        }
    
    def get_recent_predictions(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get n most recent predictions."""
        return list(self.predictions)[-n:]
    
    def format_simple_display(self) -> str:
        """Format display for terminals without rich."""
        summary = self.get_summary_stats()
        
        output = []
        output.append("\n" + "="*60)
        output.append("Magic8 Prediction Monitor")
        output.append("="*60)
        output.append(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("")
        
        # Summary stats
        output.append("SUMMARY STATISTICS")
        output.append("-"*30)
        output.append(f"Total Predictions: {summary['total']}")
        output.append(f"Approved: {summary['approved']} ({summary['approval_rate']:.1f}%)")
        output.append(f"Rejected: {summary['rejected']}")
        output.append(f"Avg Win Probability: {summary['avg_win_prob']:.1%}")
        output.append(f"Avg Latency: {summary['avg_latency']:.0f}ms")
        output.append("")
        
        # By symbol
        output.append("BY SYMBOL")
        output.append("-"*30)
        for symbol, stats in sorted(self.stats['by_symbol'].items()):
            rate = (stats['approved'] / stats['total'] * 100) if stats['total'] > 0 else 0
            output.append(f"{symbol:8} Total: {stats['total']:4} Approved: {stats['approved']:4} ({rate:5.1f}%)")
        output.append("")
        
        # By strategy
        output.append("BY STRATEGY")
        output.append("-"*30)
        for strategy, stats in sorted(self.stats['by_strategy'].items()):
            rate = (stats['approved'] / stats['total'] * 100) if stats['total'] > 0 else 0
            output.append(f"{strategy:12} Total: {stats['total']:4} Approved: {stats['approved']:4} ({rate:5.1f}%)")
        output.append("")
        
        # Recent predictions
        output.append("RECENT PREDICTIONS")
        output.append("-"*30)
        recent = self.get_recent_predictions(5)
        for pred in recent:
            timestamp = pred.get('timestamp', '')
            symbol = pred.get('symbol', 'Unknown')
            strategy = pred.get('strategy', 'Unknown')
            win_prob = pred.get('win_probability', 0)
            status = "✓" if win_prob >= pred.get('threshold', 0.55) else "✗"
            output.append(f"{status} {timestamp} {symbol:6} {strategy:12} Win: {win_prob:.1%}")
        
        return "\n".join(output)
    
    def create_rich_display(self):
        """Create rich terminal display."""
        if not RICH_AVAILABLE:
            return self.format_simple_display()
        
        summary = self.get_summary_stats()
        
        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=10)
        )
        
        # Header
        header = Panel(
            f"[bold blue]Magic8 Prediction Monitor[/bold blue]\n"
            f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            style="blue"
        )
        layout["header"].update(header)
        
        # Main area - split into columns
        layout["main"].split_row(
            Layout(name="summary", ratio=1),
            Layout(name="by_symbol", ratio=1),
            Layout(name="by_strategy", ratio=1)
        )
        
        # Summary panel
        summary_text = Text()
        summary_text.append("SUMMARY\n\n", style="bold")
        summary_text.append(f"Total: {summary['total']}\n")
        summary_text.append(f"Approved: {summary['approved']} ", style="green")
        summary_text.append(f"({summary['approval_rate']:.1f}%)\n")
        summary_text.append(f"Rejected: {summary['rejected']}\n", style="red")
        summary_text.append(f"\nAvg Win Prob: {summary['avg_win_prob']:.1%}\n")
        summary_text.append(f"Avg Latency: {summary['avg_latency']:.0f}ms\n")
        
        layout["summary"].update(Panel(summary_text, title="Statistics"))
        
        # By Symbol table
        symbol_table = Table(title="By Symbol")
        symbol_table.add_column("Symbol", style="cyan")
        symbol_table.add_column("Total", justify="right")
        symbol_table.add_column("Approved", justify="right", style="green")
        symbol_table.add_column("Rate", justify="right")
        
        for symbol, stats in sorted(self.stats['by_symbol'].items()):
            rate = (stats['approved'] / stats['total'] * 100) if stats['total'] > 0 else 0
            symbol_table.add_row(
                symbol,
                str(stats['total']),
                str(stats['approved']),
                f"{rate:.1f}%"
            )
        
        layout["by_symbol"].update(Panel(symbol_table))
        
        # By Strategy table
        strategy_table = Table(title="By Strategy")
        strategy_table.add_column("Strategy", style="magenta")
        strategy_table.add_column("Total", justify="right")
        strategy_table.add_column("Approved", justify="right", style="green")
        strategy_table.add_column("Rate", justify="right")
        
        for strategy, stats in sorted(self.stats['by_strategy'].items()):
            rate = (stats['approved'] / stats['total'] * 100) if stats['total'] > 0 else 0
            strategy_table.add_row(
                strategy,
                str(stats['total']),
                str(stats['approved']),
                f"{rate:.1f}%"
            )
        
        layout["by_strategy"].update(Panel(strategy_table))
        
        # Recent predictions
        recent_table = Table(title="Recent Predictions", show_header=True)
        recent_table.add_column("Status", width=6)
        recent_table.add_column("Time", width=8)
        recent_table.add_column("Symbol", width=8)
        recent_table.add_column("Strategy", width=12)
        recent_table.add_column("Win Prob", justify="right", width=10)
        recent_table.add_column("Latency", justify="right", width=8)
        
        recent = self.get_recent_predictions(8)
        for pred in recent:
            timestamp = datetime.fromisoformat(pred.get('timestamp', '')).strftime('%H:%M:%S') if pred.get('timestamp') else 'N/A'
            symbol = pred.get('symbol', 'Unknown')
            strategy = pred.get('strategy', 'Unknown')
            win_prob = pred.get('win_probability', 0)
            latency = pred.get('prediction_time_ms', 0)
            threshold = pred.get('threshold', 0.55)
            
            status = "[green]✓ PASS[/green]" if win_prob >= threshold else "[red]✗ FAIL[/red]"
            
            recent_table.add_row(
                status,
                timestamp,
                symbol,
                strategy,
                f"{win_prob:.1%}",
                f"{latency:.0f}ms"
            )
        
        layout["footer"].update(Panel(recent_table))
        
        return layout


async def monitor_loop(monitor: PredictionMonitor, refresh_rate: int = 2):
    """Main monitoring loop."""
    if RICH_AVAILABLE:
        console = Console()
        
        with Live(monitor.create_rich_display(), console=console, refresh_per_second=1) as live:
            while True:
                # Read new predictions
                new_preds = monitor.read_new_predictions()
                if new_preds:
                    monitor.update_stats(new_preds)
                
                # Update display
                live.update(monitor.create_rich_display())
                
                await asyncio.sleep(refresh_rate)
    else:
        # Simple display without rich
        while True:
            # Clear screen (works on most terminals)
            os.system('clear' if os.name != 'nt' else 'cls')
            
            # Read new predictions
            new_preds = monitor.read_new_predictions()
            if new_preds:
                monitor.update_stats(new_preds)
            
            # Print display
            print(monitor.format_simple_display())
            
            await asyncio.sleep(refresh_rate)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Monitor Magic8 predictions in real-time")
    parser.add_argument(
        '--log-file',
        type=str,
        default='logs/predictions.jsonl',
        help='Path to predictions log file'
    )
    parser.add_argument(
        '--refresh-rate',
        type=int,
        default=2,
        help='Refresh rate in seconds'
    )
    args = parser.parse_args()
    
    log_file = Path(args.log_file)
    
    print(f"Monitoring predictions from: {log_file}")
    print("Press Ctrl+C to exit\n")
    
    if not log_file.exists():
        print(f"Warning: Log file doesn't exist yet: {log_file}")
        print("It will be created when predictions start.\n")
    
    monitor = PredictionMonitor(log_file)
    
    try:
        asyncio.run(monitor_loop(monitor, args.refresh_rate))
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")


if __name__ == "__main__":
    main()
