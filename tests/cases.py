"""Fixed test cases for the CPython vs Pyodide consistency test (shared by both sides).
Imports the ABM exactly as synced into model/abm/ (model.py + params.py)."""
import numpy as np
import model, params


def cases():
    out = []
    for pw in model.PATHWAYS:
        for mech in model.MECHANISMS:
            out.append({'params': params.default_params(), 'pathway': pw, 'mechanism': mech, 'seed': 146})
    draws = params.sample(24, np.random.default_rng(20261026))   # switches/discrete also sampled
    for i, p in enumerate(draws):
        out.append({'params': p, 'pathway': model.PATHWAYS[i % len(model.PATHWAYS)], 'mechanism': model.MECHANISMS[i % len(model.MECHANISMS)],
                    'seed': 1000 + i})
    out.append({'params': params.default_params(), 'pathway': 'PW0', 'mechanism': 'M-D', 'seed': 7,
                'start': '2022-07'})                                  # history mode
    return out


def run_all(inputs):
    return [model.run(c['params'], c['pathway'], c['mechanism'], c['seed'], start=c.get('start', '2026-07'),
                      emit_events=True, inputs=inputs) for c in cases()]
