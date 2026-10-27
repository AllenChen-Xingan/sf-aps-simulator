"""Compare CPython and Pyodide outputs. Integers and strings: exact. Floats: 1e-12 relative."""
import json, math, sys
from pathlib import Path
H = Path(__file__).resolve().parent
A, B = json.load(open(H / 'out-cpython.json')), json.load(open(H / 'out-pyodide.json'))
bad = []

def cmp(x, y, where):
    if isinstance(x, float) or isinstance(y, float):
        if not math.isclose(float(x), float(y), rel_tol=1e-12, abs_tol=1e-9):
            bad.append((where, x, y))
    elif isinstance(x, dict):
        if set(x) != set(y): bad.append((where, 'keys', sorted(set(x) ^ set(y)))); return
        for k in x: cmp(x[k], y[k], f'{where}.{k}')
    elif isinstance(x, list):
        if len(x) != len(y): bad.append((where, 'len', (len(x), len(y)))); return
        for i, (u, v) in enumerate(zip(x, y)): cmp(u, v, f'{where}[{i}]')
    elif x != y:
        bad.append((where, x, y))

cmp(A['results'], B['results'], 'results')
n = len(A['results']); ev = sum(len(r.get('events', [])) for r in A['results'])
print(f"{A['runtime']}  vs  {B['runtime']}")
print(f'cases {n}, events compared {ev}, mismatches {len(bad)}')
for b in bad[:10]: print('  ', b)
import hashlib
sha = hashlib.sha256(open(H.parent / 'model/abm/model.py', 'rb').read()).hexdigest()[:12]
json.dump({'model_sha256_12': sha, 'cases': n, 'events': ev, 'mismatches': len(bad), 'runtimes': [A['runtime'], B['runtime']]}, open(H.parent / 'results/consistency.json', 'w'))
sys.exit(1 if bad else 0)
