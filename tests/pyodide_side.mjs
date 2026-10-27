// Pyodide side: run the same cases with the SAME self-hosted runtime the page publishes (vendor/pyodide),
// write tests/out-pyodide.json.
import { loadPyodide } from '../vendor/pyodide/pyodide.mjs';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(here, '..');
const py = await loadPyodide({ indexURL: path.join(root, 'vendor/pyodide') + '/' });
await py.loadPackage('numpy');
py.FS.mkdirTree('/w');
for (const f of ['model.py', 'params.py'])
  py.FS.writeFile('/w/' + f, readFileSync(path.join(root, 'model/abm', f), 'utf8'));
py.FS.writeFile('/w/cases.py', readFileSync(path.join(here, 'cases.py'), 'utf8'));
py.FS.writeFile('/w/inputs.json', readFileSync(path.join(root, 'model/abm/inputs.json'), 'utf8'));
const out = py.runPython(`
import sys, json, platform, numpy
sys.path.insert(0, '/w')
from cases import run_all
res = run_all(json.load(open('/w/inputs.json')))
import pyodide
json.dumps({'runtime': f'Pyodide {pyodide.__version__} (Python {platform.python_version()}) numpy {numpy.__version__}', 'runtime_id': {'pyodide': pyodide.__version__, 'python': platform.python_version(), 'numpy': numpy.__version__}, 'results': res})
`);
writeFileSync(path.join(here, 'out-pyodide.json'), out);
console.log('pyodide cases:', JSON.parse(out).results.length);
