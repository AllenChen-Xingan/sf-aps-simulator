"""The animation moves dots only from the event stream. Check that replaying the events
(initial states + `classify` for new requests + `state_changes`) reproduces the model's own
monthly stocks exactly, for many random cases. Same logic as replay() in assets/app.js."""
import json, sys
from collections import Counter
from pathlib import Path
import numpy as np
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parent / 'model/abm'))
import model, params  # noqa: E402

inputs = json.load(open(H.parent / 'model/abm/inputs.json'))
bad = 0; n = 0
for i, p in enumerate(params.sample(120, np.random.default_rng(99))):
    pw, mech = model.PATHWAYS[i % len(model.PATHWAYS)], model.MECHANISMS[i % len(model.MECHANISMS)]
    r = model.run(p, pw, mech, i, emit_events=True, inputs=inputs)
    state = dict(r.get('initial_states') or {s['key']: s['state'] for s in inputs['pending76']})
    ev = r['events']; j = 0
    for t, mo in enumerate(r['months']):
        while j < len(ev) and ev[j]['month'] == mo:
            e = ev[j]; j += 1
            if e['action'] == 'classify':
                for k in e['intersections']: state[k] = e['detail']
            for c in e.get('state_changes', []):
                assert state.get(c['key']) == c['from'], (i, mo, e, state.get(c['key']))
                state[c['key']] = c['to']
        cnt = Counter(state.values())
        got = {'C': cnt['C'], 'N': cnt['N'], 'Fi': cnt['Fi'], 'Fs': cnt['Fs'], 'Fh': cnt['Fh'], 'I_cum': cnt['I']}
        want = {k: r['stocks'][k][t] for k in got}
        n += 1
        if got != want:
            bad += 1
            if bad <= 5: print('mismatch', i, pw, mech, mo, got, want)
print(f'months checked {n}, mismatches {bad}')
sys.exit(1 if bad else 0)
