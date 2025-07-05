#!/bin/bash
# Run comprehensive tests including integration flows
python tests/run_comprehensive_tests.py
pytest tests/test_integration_real.py -v
