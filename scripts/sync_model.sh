#!/bin/sh
# Copy the ABM (maintained in a separate research repository) into the site, unchanged,
# and record checksums. The site never edits these files.
# Source folder: $ABM_DIR, or the first line of .abm-path (not committed): <abm>/model
set -e
cd "$(dirname "$0")/.."
SRC="${ABM_DIR:-$(head -1 .abm-path 2>/dev/null)}"
[ -n "$SRC" ] || { echo "Set ABM_DIR or write the model folder path into .abm-path"; exit 1; }
mkdir -p model/abm
cp "$SRC/model.py" "$SRC/params.py" model/abm/
cp "$SRC/data/inputs.json" model/abm/inputs.json
{ echo "synced: $(date -u +%Y-%m-%dT%H:%MZ)"; (cd model/abm && shasum -a 256 model.py params.py inputs.json); } > model/abm/SOURCE.txt
cat model/abm/SOURCE.txt
# parameter table of the live model, for the control panel before Pyodide loads
.venv/bin/python -I -c "import sys,json;sys.path.insert(0,'model/abm');import params;json.dump(params.param_schema(),open('model/abm/params-schema.json','w'),indent=0)"
# small JSON for the page footer
python3 -c "import json,hashlib;h=hashlib.sha256(open('model/abm/model.py','rb').read()).hexdigest()[:12];import datetime;json.dump({'model_sha256_12':h,'synced':datetime.date.today().isoformat()},open('model/abm/version.json','w'))"
