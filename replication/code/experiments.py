"""Experiments E1-E4 (model design: see docs/ODD+D.md). Scenario exploration, not forecasts.

    python -I experiments.py e1  [--scale 1.0] [--out DIR]
    python -I experiments.py e23 [--scale 1.0] [--out DIR]
    python -I experiments.py e4a [--scale 1.0] [--out DIR]
    python -I experiments.py e4b [--scale 1.0] [--out DIR]

--scale < 1 shrinks every sample size for self-tests (always with --out under _tmp).
All runs go through runner.py (CPU count - 2 processes, fixed seeds, shard-then-merge).
model.py is not modified: the SG105 breakpoint scan sets model.SG105_END inside each task.
"""
import argparse, csv, gzip, json, sys, warnings, zlib
warnings.filterwarnings('ignore')
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import model, params, runner  # noqa: E402

RES = HERE.parent / 'results'
MASTER_SEED = 146
BREAKPOINTS = ['2023-06', '2023-12', '2024-02', '2024-06', '2024-12']
WIDTHS = {'base': 1.0, 'narrow': 0.5, 'wide': 2.0}
REPS = 20

# Observed request-list stocks (fit F1-F4: <= 2025-02-21; H1 retrospective check: the three later lists)
FIT_SNAPS = ['2023-01-03', '2023-06-30', '2024-02-20', '2024-08-21', '2025-02-21']
H1_SNAPS = ['2025-08-08', '2026-01-29', '2026-06-30']
TOL = {'C': 6, 'N': 4, 'Fi': 5, 'Fs': 6, 'I': 8}          # absolute tolerance per stock (fixed before the runs)


# ---------------------------------------------------------------- helpers
def seeds_for(tag, n=REPS):
    ss = np.random.SeedSequence([MASTER_SEED, zlib.crc32(tag.encode())])   # stable across processes
    return [int(x) for x in ss.generate_state(n)]


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, default=float))


def mean_stock(reps, snap, key):
    vals = []
    for r in reps:
        st = r['snapshot_stocks'][snap]
        vals.append(st['I_cum'] if key == 'I' else st[key])
    return float(np.mean(vals))


def fits(reps, observed, snaps):
    """Pattern check on the replicate mean; returns (all_ok, per-pattern dict)."""
    ok = {}
    for key in ('C', 'N', 'Fi', 'Fs', 'I'):
        ok[key] = all(abs(mean_stock(reps, s, key) - observed[s][key]) <= TOL[key] for s in snaps)
    return all(ok.values()), ok


# ---------------------------------------------------------------- E1: mechanism fit
def e1(scale, out):
    inp = model.load_inputs(HERE / 'data' / 'inputs.json')
    obs = inp['history']['observed_stocks']
    n = max(4, int(2000 * scale))
    reps = max(2, int(REPS * scale)) if scale < 1 else REPS
    tasks, tid = [], 0
    for width_name, width in list(WIDTHS.items()) + [('wide_rates', 1.0)]:
        rng = np.random.default_rng([MASTER_SEED, zlib.crc32(width_name.encode())])
        psets = params.sample(n if width_name != 'wide_rates' else max(4, n // 5), rng, width=width)
        if width_name == 'wide_rates':                 # independent wide priors for the reused rates
            for ps in psets:
                ps['h_in'] = float(rng.uniform(0.3, 2.0))
                ps['h_fs'] = float(rng.uniform(0.03, 0.5))
        for bp in (BREAKPOINTS if width_name == 'base' else ['2024-06']):
            for mech in model.MECHANISMS:
                for i, ps in enumerate(psets):
                    tasks.append({'task_id': tid, 'params': ps, 'pathway': 'PW0', 'mechanism': mech,
                                  'seeds': seeds_for(f'e1-{width_name}-{i}', reps), 'start': '2022-07',
                                  'horizon': 48, 'sg105_end': bp,
                                  'meta': {'width': width_name, 'breakpoint': bp, 'set': i}})
                    tid += 1
    rows = runner.run_tasks(tasks, out / '_shards' / 'e1')
    table, accepted = {}, {}
    for t, r in zip(tasks, rows):
        m = t['meta']
        ok_fit, per = fits(r['reps'], obs, FIT_SNAPS)
        ok_h1, per_h1 = fits(r['reps'], obs, H1_SNAPS)
        key = f"{t['mechanism']}|{m['width']}|{m['breakpoint']}"
        cell = table.setdefault(key, {'n': 0, 'accepted': 0, 'h1_pass_among_accepted': 0,
                                      'pattern_pass': {k: 0 for k in TOL}})
        cell['n'] += 1
        for k, v in per.items():
            cell['pattern_pass'][k] += int(v)
        if ok_fit:
            cell['accepted'] += 1
            cell['h1_pass_among_accepted'] += int(ok_h1)
            if m['width'] == 'base':
                accepted.setdefault(t['mechanism'], []).append(t['params'])
    for cell in table.values():
        cell['accept_rate'] = cell['accepted'] / cell['n']
        cell['h1_pass_rate'] = (cell['h1_pass_among_accepted'] / cell['accepted']) if cell['accepted'] else None
    # parameter values the accepted sets need (median and 10-90%), base prior
    need = {}
    for mech, sets in accepted.items():
        need[mech] = {k: [float(np.percentile([s[k] for s in sets], q)) for q in (10, 50, 90)]
                      for k in ('b0', 'b_own', 'p_deflect', 'k0', 'phi', 'm_b', 'm_c', 'g_cost', 'tau', 'a_local', 'h_in', 'h_fs')}
    write_json(out / 'e1-fit' / 'fit-table.json', {'tolerance': TOL, 'fit_snapshots': FIT_SNAPS, 'h1_snapshots': H1_SNAPS,
                                                   'reps': reps, 'cells': table, 'needed_parameter_values': need})
    write_json(out / 'e1-fit' / 'accepted-sets.json', accepted)
    print('E1 done:', len(tasks), 'tasks;', {k: v['accept_rate'] for k, v in table.items() if '|base|2024-06' in k})


# ---------------------------------------------------------------- E2 + E3: pathways and conditions
def e23(scale, out):
    acc = json.loads((out / 'e1-fit' / 'accepted-sets.json').read_text())
    n = max(4, int(1000 * scale))
    reps = max(2, int(REPS * scale)) if scale < 1 else REPS
    proj = [r['name'] for r in params.param_schema() if r['phase'] == 'projection']
    tasks, tid = [], 0
    for mech in model.MECHANISMS:
        pool = acc.get(mech, [])
        if not pool:
            print('E2/E3: no accepted sets for', mech, '- skipped')
            continue
        rng = np.random.default_rng([MASTER_SEED, 23, model.MECHANISMS.index(mech)])
        fresh = params.sample(n, rng, names=set(proj))
        sets = []
        for i in range(n):
            base = dict(pool[int(rng.integers(len(pool)))])   # joint resample of fitted parameters
            base.update({k: fresh[i][k] for k in proj})          # independent projection-only parameters
            sets.append(base)
        for control in ('positive', 'zero_direct'):
            for pw in model.PATHWAYS:
                for i, ps in enumerate(sets):
                    q = dict(ps)
                    if control == 'zero_direct':
                        q.update(b_own=0.0, b_spec=0.0, b_ov=0.0, b_pr=0.0)
                    tasks.append({'task_id': tid, 'params': q, 'pathway': pw, 'mechanism': mech,
                                  'seeds': seeds_for(f'e23-{mech}-{i}', reps), 'meta': {'set': i, 'control': control}})
                    tid += 1
    rows = runner.run_tasks(tasks, out / '_shards' / 'e23')
    recs = []
    for t, r in zip(tasks, rows):
        sm = [x['summary'] for x in r['reps']]
        rec = [x['recovery_time'] for x in sm]
        recs.append({'pathway': t['pathway'], 'mechanism': t['mechanism'], 'control': t['meta']['control'], 'set': t['meta']['set'],
                     'P_money': float(np.mean([x['money_flows_5y'] for x in sm])),
                     'installed_5y': float(np.mean([x['installed_5y'] for x in sm])),
                     'coverage_10y': float(np.mean([x['coverage_10y'] for x in sm])),
                     'recovery_median': float(np.median([x for x in rec if x is not None])) if any(x is not None for x in rec) else None,
                     'recovery_censored': float(np.mean([x is None for x in rec])),
                     'nodes': sorted({nd for x in r['reps'] for nd in x['path_nodes_reached']}),
                     **{k: t['params'][k] for k in t['params']}})
    (out / 'e3-pathways').mkdir(parents=True, exist_ok=True)
    with gzip.open(out / 'e3-pathways' / 'runs.csv.gz', 'wt', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(recs[0].keys()))
        w.writeheader()
        w.writerows({**r, 'nodes': ';'.join(r['nodes'])} for r in recs)
    write_json(out / 'e3-pathways' / 'robustness.json', robustness(recs))
    write_json(out / 'e2-prim' / 'prim.json', prim_all(recs, proj))
    print('E2/E3 done:', len(tasks), 'tasks')


def robustness(recs):
    out = []
    base = {(r['mechanism'], r['control'], r['set']): r['coverage_10y'] for r in recs if r['pathway'] == 'PW0'}
    best = {}
    for r in recs:
        k = (r['mechanism'], r['control'], r['set'])
        best[k] = max(best.get(k, -1), r['coverage_10y'])
    for mech in model.MECHANISMS:
        for control in ('positive', 'zero_direct'):
            for pw in model.PATHWAYS:
                rr = [r for r in recs if r['mechanism'] == mech and r['control'] == control and r['pathway'] == pw]
                if not rr:
                    continue
                cov = np.array([r['coverage_10y'] for r in rr])
                item = {'mechanism': mech, 'control': control, 'pathway': pw, 'n_sets': len(rr),
                        'coverage_10y_p10_p50_p90': [float(np.percentile(cov, q)) for q in (10, 50, 90)],
                        'P_money_mean': float(np.mean([r['P_money'] for r in rr])),
                        'share_better_than_PW0': None if pw == 'PW0' else float(np.mean(
                            [r['coverage_10y'] > base[(mech, control, r['set'])] for r in rr])),
                        'max_regret': float(max(best[(mech, control, r['set'])] - r['coverage_10y'] for r in rr)),
                        'recovery_median_of_medians': float(np.median([r['recovery_median'] for r in rr if r['recovery_median'] is not None]))
                        if any(r['recovery_median'] is not None for r in rr) else None}
                for a in (0, 1):
                    for b in (0, 1):
                        sub = [r['coverage_10y'] for r in rr if int(r['sw_si02']) == a and int(r['sw_line']) == b]
                        item[f'median_cov_si02{a}_line{b}'] = float(np.median(sub)) if sub else None
                out.append(item)
    return out


def prim_all(recs, names):
    import pandas as pd
    from ema_workbench.analysis import prim
    from sklearn.tree import DecisionTreeClassifier, export_text
    res = {}
    for pw in model.PATHWAYS:
        rr = [r for r in recs if r['pathway'] == pw and r['control'] == 'positive']
        if len(rr) < 20:
            continue
        cols = [c for c in names if c in rr[0]] + ['p_deflect', 'b0', 'b_own', 'k0', 'a_local', 'lam_press']
        cols = list(dict.fromkeys(cols))
        X = pd.DataFrame([{c: float(r[c]) for c in cols} for r in rr])
        out = []
        for thr in (0.25, 0.5, 0.75):
            y = np.array([r['P_money'] >= thr for r in rr])
            for split in range(5):
                rng = np.random.default_rng([MASTER_SEED, split])
                idx = rng.permutation(len(rr))
                tr, te = idx[: len(rr) // 2], idx[len(rr) // 2:]
                if y[tr].sum() < 3 or (~y[tr]).sum() < 3:
                    out.append({'threshold': thr, 'split': split, 'note': 'too few positives or negatives'})
                    continue
                pr = prim.Prim(X.iloc[tr].reset_index(drop=True), y[tr])
                box = pr.find_box()
                traj = box.peeling_trajectory
                ok = traj[(traj['res_dim'] <= 3) & (traj['coverage'] >= 0.3)]
                if len(ok):
                    box.select(int(ok['density'].idxmax()))   # densest box with <= 3 dimensions, coverage >= 0.3
                    lim = box.box_lim
                else:
                    lim = None
                rules, inside = [], np.ones(len(te), bool)
                if lim is not None:
                    for c in X.columns:
                        lo, hi = float(lim[c].iloc[0]), float(lim[c].iloc[1])
                        if lo > X[c].min() + 1e-9 or hi < X[c].max() - 1e-9:
                            rules.append({'param': c, 'low': lo, 'high': hi})
                            v = X[c].values[te]
                            inside &= (v >= lo) & (v <= hi)
                    rules = rules[:3]
                yt = y[te]
                cov = float((inside & yt).sum() / max(1, yt.sum()))
                dens = float((inside & yt).sum() / max(1, inside.sum()))
                tree = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X.iloc[tr], y[tr])
                out.append({'threshold': thr, 'split': split, 'rules': rules, 'coverage_test': cov, 'density_test': dens,
                            'cart_test_accuracy': float(tree.score(X.iloc[te], yt)),
                            'cart_rules': export_text(tree, feature_names=list(X.columns))})
        res[pw] = out
    return res


# ---------------------------------------------------------------- E4: Morris then Sobol (conditional)
def problem():
    rows = params.param_schema()
    return rows, {'num_vars': len(rows), 'names': [r['name'] for r in rows], 'bounds': [[0.0, 1.0]] * len(rows)}


def decode(u, rows):
    """Map a unit-cube row to parameter values: uniform -> range; switch/discrete -> equal slices."""
    out = dict(params.default_params())
    for x, r in zip(u, rows):
        if r['kind'] == 'uniform':
            out[r['name']] = r['low'] + float(x) * (r['high'] - r['low'])
        else:
            ch = params.CHOICES.get(r['name'], [r['low'], r['high']])
            out[r['name']] = ch[min(len(ch) - 1, int(float(x) * len(ch)))]
    return out


def e4a(scale, out):
    from SALib.sample import morris as ms
    from SALib.analyze import morris as ma
    rows, prob = problem()
    r_traj = max(2, int(20 * scale))
    reps = max(2, int(REPS * scale)) if scale < 1 else REPS
    result = {}
    for rep_seed in (1, 2):                                   # second pass checks screening stability
        X = ms.sample(prob, r_traj, num_levels=4, seed=MASTER_SEED + rep_seed)
        tasks, tid = [], 0
        for pw in model.PATHWAYS:
            for mech in model.MECHANISMS:
                for i, u in enumerate(X):
                    tasks.append({'task_id': tid, 'params': decode(u, rows), 'pathway': pw, 'mechanism': mech,
                                  'seeds': seeds_for(f'e4a-{rep_seed}-{i}', reps), 'meta': {'i': i}})
                    tid += 1
        rr = runner.run_tasks(tasks, out / '_shards' / f'e4a-{rep_seed}')
        for pw in model.PATHWAYS:
            for mech in model.MECHANISMS:
                Y = np.array([np.mean([x['summary']['coverage_10y'] for x in r['reps']])
                              for t, r in zip(tasks, rr) if t['pathway'] == pw and t['mechanism'] == mech])
                Si = ma.analyze(prob, X, Y, num_levels=4, seed=MASTER_SEED)
                result.setdefault(f'{pw}|{mech}', {})[f'pass{rep_seed}'] = {
                    'mu_star': dict(zip(prob['names'], map(float, Si['mu_star']))),
                    'sigma': dict(zip(prob['names'], map(float, Si['sigma'])))}
    # top-12 by mean mu* across cells, per pass; stability check
    def top(pass_key):
        agg = {n: np.mean([c[pass_key]['mu_star'][n] for c in result.values()]) for n in prob['names']}
        return sorted(agg, key=lambda n: -agg[n])[:12]
    t1, t2 = top('pass1'), top('pass2')
    overlap = len(set(t1) & set(t2))
    chosen = t1 if overlap >= 10 else sorted(set(t1) | set(t2))
    write_json(out / 'e4-sensitivity' / 'morris.json', {'cells': result, 'top12_pass1': t1, 'top12_pass2': t2,
                                                         'overlap': overlap, 'chosen_for_sobol': chosen})
    print('E4a done; top-12 overlap', overlap, 'chosen', len(chosen))


def e4b(scale, out):
    from SALib.sample import sobol as ss
    from SALib.analyze import sobol as sa
    rows, _ = problem()
    chosen = json.loads((out / 'e4-sensitivity' / 'morris.json').read_text())['chosen_for_sobol']
    sub = [r for r in rows if r['name'] in chosen]
    prob = {'num_vars': len(sub), 'names': [r['name'] for r in sub], 'bounds': [[0.0, 1.0]] * len(sub)}
    reps = max(2, int(REPS * scale)) if scale < 1 else REPS
    res = {}
    cells = [(pw, m, 'default') for pw in model.PATHWAYS for m in ('M-A', 'M-D')]
    cells += [(pw, m, bg) for pw in ('PW0', 'PW4') for m in ('M-A', 'M-D') for bg in ('p25', 'p75')]
    for N in (256, 512):
        N_eff = max(8, int(N * scale))
        X = ss.sample(prob, N_eff, calc_second_order=False, seed=MASTER_SEED)
        tasks, tid = [], 0
        for pw, mech, bg in cells:
            if bg != 'default' and N != 256:
                continue
            for i, u in enumerate(X):
                base = dict(params.default_params())
                if bg != 'default':                       # fixed background at the 25th / 75th percentile
                    q = 0.25 if bg == 'p25' else 0.75
                    base = decode([q] * len(rows), rows)
                base.update({k: v for k, v in decode(u, sub).items() if k in prob['names']})
                tasks.append({'task_id': tid, 'params': base, 'pathway': pw, 'mechanism': mech,
                              'seeds': seeds_for(f'e4b-{i}', reps), 'meta': {'i': i, 'bg': bg}})
                tid += 1
        rr = runner.run_tasks(tasks, out / '_shards' / f'e4b-{N}')
        for pw, mech, bg in cells:
            if bg != 'default' and N != 256:
                continue
            Y = np.array([np.mean([x['summary']['coverage_10y'] for x in r['reps']])
                          for t, r in zip(tasks, rr) if t['pathway'] == pw and t['mechanism'] == mech
                          and t['meta']['bg'] == bg])
            Si = sa.analyze(prob, Y, calc_second_order=False, seed=MASTER_SEED)
            res.setdefault(f'{pw}|{mech}|{bg}', {})[f'N{N}'] = {
                'S1': dict(zip(prob['names'], map(float, Si['S1']))), 'S1_conf': dict(zip(prob['names'], map(float, Si['S1_conf']))),
                'ST': dict(zip(prob['names'], map(float, Si['ST']))), 'ST_conf': dict(zip(prob['names'], map(float, Si['ST_conf'])))}
    write_json(out / 'e4-sensitivity' / 'sobol.json', {'inputs': prob['names'], 'note': 'conditional sensitivity: other parameters fixed at defaults (or at the 25th/75th percentile background)', 'cells': res})
    print('E4b done')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exp', choices=['e1', 'e23', 'e4a', 'e4b'])
    ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--out', default=str(RES))
    a = ap.parse_args()
    {'e1': e1, 'e23': e23, 'e4a': e4a, 'e4b': e4b}[a.exp](a.scale, Path(a.out))


if __name__ == '__main__':
    main()
