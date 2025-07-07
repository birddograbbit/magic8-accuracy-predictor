#!/usr/bin/env python3
"""Helper script to run the comprehensive API tests with coverage."""

import subprocess
import sys

cmd = [
    sys.executable,
    "-m",
    "pytest",
    "-v",
    "--cov=src",
    "tests/test_api_comprehensive.py",
    "tests/test_evaluation_metrics.py",
    "tests/test_batch_prediction.py",
]
result = subprocess.run(cmd)
sys.exit(result.returncode)

