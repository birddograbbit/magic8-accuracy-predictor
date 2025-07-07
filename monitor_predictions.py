#!/usr/bin/env python3
"""Simple utility to monitor prediction logs in real time."""
import argparse
import json
import time
from collections import defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Live monitor for predictions.jsonl")
    parser.add_argument("--log-file", default="logs/predictions.jsonl", help="Path to prediction log file")
    parser.add_argument("--interval", type=float, default=1.0, help="Refresh interval when waiting for new data")
    args = parser.parse_args()

    log_path = Path(args.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        print(f"Waiting for log file {log_path}...")
        log_path.touch()

    counts = defaultdict(int)
    approved = defaultdict(int)

    try:
        with open(log_path, "r") as f:
            f.seek(0, 2)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(args.interval)
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                key = f"{entry.get('symbol')} {entry.get('strategy')}"
                counts[key] += 1
                if entry.get("approved"):
                    approved[key] += 1
                rate = approved[key] / counts[key] if counts[key] else 0
                print(f"{key}: {approved[key]}/{counts[key]} approved ({rate:.1%})")
    except KeyboardInterrupt:
        print("\nStopping monitor")


if __name__ == "__main__":
    main()
