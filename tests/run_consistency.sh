#!/bin/sh
# One command: CPython and Pyodide run the same fixed cases (61); outputs must match.
set -e
cd "$(dirname "$0")"
../.venv/bin/python -I py_side.py
node pyodide_side.mjs
../.venv/bin/python -I compare.py
