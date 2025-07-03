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
]
result = subprocess.run(cmd)
sys.exit(result.returncode)

