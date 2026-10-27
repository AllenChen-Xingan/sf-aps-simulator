#!/bin/sh
# Self-host Pyodide 314.0.7 + numpy so the page does not depend on a CDN at run time.
# Source: the pyodide npm package (tests/node_modules), numpy wheel cached from the official
# Pyodide CDN by tests/pyodide_side.mjs. The wheel's sha256 is checked against pyodide-lock.json.
set -e
cd "$(dirname "$0")/.."
SRC=tests/node_modules/pyodide
DST=vendor/pyodide
mkdir -p "$DST"
WHL=$(python3 -c "import json;print(json.load(open('$SRC/pyodide-lock.json'))['packages']['numpy']['file_name'])")
WANT=$(python3 -c "import json;print(json.load(open('$SRC/pyodide-lock.json'))['packages']['numpy']['sha256'])")
GOT=$(shasum -a 256 "$SRC/$WHL" | cut -d' ' -f1)
[ "$WANT" = "$GOT" ] || { echo "numpy wheel hash mismatch"; exit 1; }
for f in pyodide.js pyodide.mjs pyodide.asm.mjs pyodide.asm.wasm python_stdlib.zip pyodide-lock.json package.json "$WHL"; do cp "$SRC/$f" "$DST/"; done
cat > "$DST/README.md" <<'TXT'
Pyodide 314.0.7 (Mozilla Public License 2.0, https://github.com/pyodide/pyodide) and numpy 2.4.6
(BSD-3-Clause) built for Pyodide, copied unchanged from the pyodide npm package and the official
Pyodide package index. Regenerate with scripts/vendor_pyodide.sh.
TXT
echo "numpy wheel sha256 ok: $GOT"; du -sh "$DST"
