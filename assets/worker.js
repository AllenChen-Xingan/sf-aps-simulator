// Runs the project's Python ABM (model/abm/model.py, unchanged) in the browser with Pyodide.
// Same code and same seed as the Python runs, so results match (see tests/run_consistency.sh).
// Module worker. Self-hosted Pyodide (vendor/pyodide, see scripts/vendor_pyodide.sh): no CDN at run time.
import { loadPyodide } from '../vendor/pyodide/pyodide.mjs';
const PYODIDE = new URL('../vendor/pyodide/', import.meta.url).href;

let ready = null;
let fingerprint = null;

async function init() {
  const py = await loadPyodide({ indexURL: PYODIDE });
  await py.loadPackage('numpy');
  const base = new URL('../model/abm/', import.meta.url);
  const bufs = await Promise.all(
    ['model.py', 'params.py', 'inputs.json'].map(f => fetch(new URL(f, base)).then(r => {
      if (!r.ok) throw new Error('Could not load ' + f);
      return r.arrayBuffer();
    })));
  // Fingerprint of the bytes actually loaded (same formula as scripts/fingerprint.py).
  const hex = async b => [...new Uint8Array(await crypto.subtle.digest('SHA-256', b))].map(x => x.toString(16).padStart(2, '0')).join('');
  const parts = await Promise.all(bufs.map(hex));
  fingerprint = await hex(new TextEncoder().encode(parts.join('\n')));
  const [m, p, inp] = bufs.map(b => new TextDecoder().decode(b));
  py.FS.mkdirTree('/abm');
  py.FS.writeFile('/abm/model.py', m);
  py.FS.writeFile('/abm/params.py', p);
  py.FS.writeFile('/abm/inputs.json', inp);
  py.runPython(`
import sys, json
sys.path.insert(0, '/abm')
import model, params
INPUTS = json.load(open('/abm/inputs.json'))
def _run(req):
    q = json.loads(req)
    p = params.default_params(); p.update(q['params'])
    r = model.run(p, q['pathway'], q['mechanism'], int(q['seed']), emit_events=True, inputs=INPUTS)
    r['request'] = {**q, 'params': p}
    return json.dumps(r)
`);
  return py;
}

self.onmessage = async (ev) => {
  const { id, type, request } = ev.data;
  try {
    if (!ready) ready = init();
    const py = await ready;
    if (type === 'init') { self.postMessage({ id, ok: true, fingerprint }); return; }
    const t0 = performance.now();
    const out = py.globals.get('_run')(JSON.stringify(request));
    self.postMessage({ id, ok: true, result: JSON.parse(out), ms: performance.now() - t0 });
  } catch (err) {
    self.postMessage({ id, ok: false, error: String(err && err.message || err) });
  }
};
