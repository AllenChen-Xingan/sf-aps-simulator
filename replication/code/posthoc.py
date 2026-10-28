"""Secondary analyses computed from the E3 runs without new simulation.

They re-read results/e3-pathways/runs.csv.gz and write
results/e3-pathways/posthoc.json:
  1. robustness split by the sw_line switch (the design reports switch scenarios as separate groups);
     sw_line = 0 is the case that matches today's status quo (no standing local APS line);
  2. PRIM boxes re-described with the FULL rule list (experiments.prim_all stores rules[:3] in column
     order, which can drop a binding rule such as sw_line while keeping near-full-range ones; coverage
     and density there were computed on all rules, so those numbers stand);
  3. one-parameter splits used in the summaries (q_dir, lam_press, b_pr, k0, h_in).

    python -I posthoc.py
"""
import gzip, csv, json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
RES = HERE.parent / 'results'
MASTER_SEED = 146
PWS = ['PW0', 'PW1', 'PW2', 'PW3', 'PW4', 'PW5', 'PW6']


def load():
    with gzip.open(RES / 'e3-pathways' / 'runs.csv.gz', 'rt') as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k, v in r.items():
            if k not in ('pathway', 'mechanism', 'control', 'nodes'):
                try:
                    r[k] = float(v)
                except ValueError:
                    pass
    base = {(r['mechanism'], r['control'], r['set']): r['coverage_10y'] for r in rows if r['pathway'] == 'PW0'}
    for r in rows:
        r['better'] = r['coverage_10y'] > base[(r['mechanism'], r['control'], r['set'])]
    return rows


def table(rows, keep):
    """Per pathway x control: min-max over mechanisms of share better, P_money mean, median coverage."""
    out = {}
    for ctl in ('positive', 'zero_direct'):
        for pw in PWS:
            per = []
            for mech in sorted({r['mechanism'] for r in rows}):
                s = [r for r in rows if r['pathway'] == pw and r['control'] == ctl and r['mechanism'] == mech and keep(r)]
                if s:
                    per.append((np.mean([r['better'] for r in s]), np.mean([r['P_money'] for r in s]),
                                np.median([r['coverage_10y'] for r in s]), len(s), mech))
            out[f'{pw}|{ctl}'] = {
                'share_better': [float(min(p[0] for p in per)), float(max(p[0] for p in per))],
                'P_money': [float(min(p[1] for p in per)), float(max(p[1] for p in per))],
                'median_cov10': [float(min(p[2] for p in per)), float(max(p[2] for p in per))],
                'n_sets_per_mech': int(min(p[3] for p in per)),
                'by_mech': {p[4]: round(float(p[0]), 4) for p in per}}
    return out


def prim_full(rows):
    import pandas as pd
    from ema_workbench.analysis import prim
    names = ['sw_line', 'a_line', 'aps_share', 'c_final', 'r_other', 'q_dir', 'q_gf', 'q_veto', 'p_deflect', 'b0',
             'b_own', 'k0', 'a_local', 'lam_press', 'q_pipe', 'q_ramp', 'u0', 'h_fs', 'lam_arr']
    res = {}
    for pw in PWS:
        rr = [r for r in rows if r['pathway'] == pw and r['control'] == 'positive']
        cols = [c for c in names if c in rr[0]]
        X = pd.DataFrame([{c: r[c] for c in cols} for r in rr])
        y = np.array([r['P_money'] >= 0.5 for r in rr])
        out = []
        for split in range(5):
            idx = np.random.default_rng([MASTER_SEED, split]).permutation(len(rr))
            tr, te = idx[: len(rr) // 2], idx[len(rr) // 2:]
            pr = prim.Prim(X.iloc[tr].reset_index(drop=True), y[tr])
            box = pr.find_box()
            traj = box.peeling_trajectory
            ok = traj[(traj['res_dim'] <= 3) & (traj['coverage'] >= 0.3)]
            if not len(ok):
                out.append({'split': split, 'note': 'no box'})
                continue
            box.select(int(ok['density'].idxmax()))
            lim = box.box_lim
            rules, inside = [], np.ones(len(te), bool)
            init = pr.box_init                      # training-set bounds = 'unrestricted' for this box
            for c in X.columns:
                lo, hi = float(lim[c].iloc[0]), float(lim[c].iloc[1])
                ilo, ihi = float(init[c].iloc[0]), float(init[c].iloc[1])
                if lo > ilo + 1e-9 or hi < ihi - 1e-9:
                    span = (ihi - ilo) or 1.0
                    rules.append({'param': c, 'low': lo, 'high': hi,
                                  'trimmed_share_of_range': round(1 - (hi - lo) / span, 3)})
                    v = X[c].values[te]
                    inside &= (v >= lo) & (v <= hi)
            yt = y[te]
            out.append({'split': split, 'rules': rules,
                        'coverage_test': float((inside & yt).sum() / max(1, yt.sum())),
                        'density_test': float((inside & yt).sum() / max(1, inside.sum()))})
        res[pw] = out
    return res


def splits(rows):
    pos = [r for r in rows if r['control'] == 'positive']
    spec = {'q_dir': [0, 0.08, 0.4, 0.8001], 'lam_press': [0, 0.1, 0.25, 0.4, 0.5001], 'b_pr': [0, 0.5, 1.5, 2.0001],
            'k0': [0.5, 1.0, 2.0, 3.0001], 'h_in': [0.59, 0.85, 1.15, 1.4101]}
    out = {}
    for var, edges in spec.items():
        for lo, hi in zip(edges[:-1], edges[1:]):
            sub = [r for r in pos if lo <= r[var] < hi]
            key = f'{var}[{lo},{min(hi, edges[-1])})'
            out[key] = {}
            for pw in PWS:
                per = {}
                for mech in sorted({r['mechanism'] for r in sub}):
                    s = [r for r in sub if r['pathway'] == pw and r['mechanism'] == mech]
                    per[mech] = (np.mean([r['better'] for r in s]), np.mean([r['P_money'] for r in s]),
                                 np.median([r['coverage_10y'] for r in s]))
                out[key][pw] = {'share_better': [float(min(v[0] for v in per.values())), float(max(v[0] for v in per.values()))],
                                'P_money': [float(min(v[1] for v in per.values())), float(max(v[1] for v in per.values()))],
                                'median_cov10': [float(min(v[2] for v in per.values())), float(max(v[2] for v in per.values()))],
                                'share_better_by_mech': {m: round(float(v[0]), 4) for m, v in per.items()}}
    return out


def screened_corr():
    """Correlations among history-screened parameters (E1 accepted sets, all mechanisms pooled)."""
    acc = json.loads((RES / 'e1-fit' / 'accepted-sets.json').read_text())
    sets = [ps for v in acc.values() for ps in v]
    pairs = [('lam_press', 'b0'), ('lam_press', 'b_pr'), ('b_pr', 'b0'), ('k0', 'h_in'), ('k0', 'b0'), ('k0', 'phi'),
             ('h_in', 'b0'), ('p_deflect', 'b0')]
    out = {}
    for a, b in pairs:
        if a in sets[0] and b in sets[0]:
            out[f'{a}~{b}'] = round(float(np.corrcoef([s[a] for s in sets], [s[b] for s in sets])[0, 1]), 3)
    out['n_sets'] = len(sets)
    return out


if __name__ == '__main__':
    rows = load()
    res = {'note': 'secondary analyses computed from the E3 runs without new simulation; see module docstring',
           'by_sw_line': {'line0_status_quo': table(rows, lambda r: r['sw_line'] == 0),
                          'line1': table(rows, lambda r: r['sw_line'] == 1),
                          'pooled': table(rows, lambda r: True)},
           'line0_q_dir_lt_0.08': table([r for r in rows if r['sw_line'] == 0 and r['q_dir'] < 0.08], lambda r: True),
           'splits': splits(rows),
           'screened_param_correlations': screened_corr(),
           'prim_full_rules_thr0.5': prim_full(rows)}
    (RES / 'e3-pathways' / 'posthoc.json').write_text(json.dumps(res, indent=1, sort_keys=True))
    print('wrote', RES / 'e3-pathways' / 'posthoc.json')
