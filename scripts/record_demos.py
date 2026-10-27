"""Record one run per pathway (default parameters, mechanism M-D, seed 146, main switches) with
the full event stream, so the page can play an animation before the in-browser model loads.
Run: .venv/bin/python -I scripts/record_demos.py"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'model/abm'))
import model, params  # noqa: E402
inputs = json.load(open(ROOT / 'model/abm/inputs.json'))
out = ROOT / 'results/demo'; out.mkdir(parents=True, exist_ok=True)
for pw in model.PATHWAYS:
    r = model.run(params.default_params(), pw, 'M-D', 146, emit_events=True, inputs=inputs)
    r['request'] = {'params': params.default_params(), 'pathway': pw, 'mechanism': 'M-D', 'seed': 146}
    json.dump(r, open(out / f'{pw}.json', 'w'), separators=(',', ':'))
    print(pw, len(r['events']), r['summary']['installed_5y'])
