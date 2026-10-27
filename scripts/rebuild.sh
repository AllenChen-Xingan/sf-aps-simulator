#!/bin/sh
# One command after every ABM change: sync model and results -> tests -> demo recordings.
set -e
cd "$(dirname "$0")/.."
./scripts/sync_model.sh
python3 -I scripts/sync_results.py
./tests/run_consistency.sh
.venv/bin/python -I tests/test_replay.py
.venv/bin/python -I scripts/record_demos.py
