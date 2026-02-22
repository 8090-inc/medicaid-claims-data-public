#!/bin/bash
# CI test runner for Medicaid FWA Analytics Pipeline
set -e

echo "=== Installing dependencies ==="
pip install -r requirements-dev.txt

echo "=== Running foundation setup ==="
python3 setup_project_foundation.py

echo "=== Running unit tests ==="
python3 -m pytest tests/ -v --tb=short -m "not slow and not integration"

echo "=== Running integration tests ==="
python3 -m pytest tests/ -v --tb=short -m "integration"

echo "=== All tests passed ==="
