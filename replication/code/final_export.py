"""Export the formal E3 results (plus the approval variant) for the web page, in the file layout
the web page expects. No simulation: reads saved runs only.

Main view = sw_line 0 (no standing local APS line at the start, as today), positive-effect priors,
history-screened parameter sets (E1). Pooled and zero-direct-effect tables, the variant, and the
corrected PRIM boxes are added as extra keys / files.

    python -I final_export.py [--out DIR]      # default results/web/
"""
import argparse, csv, datetime, gzip, hashlib, io, json, shutil, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
RES = HERE.parent / 'results'
LABEL = 'uncalibrated · scenario projections, not forecasts'
PWS = ['PW0', 'PW1', 'PW2', 'PW3', 'PW4', 'PW5', 'PW6']
MECHS = ['M-A', 'M-B1', 'M-B2', 'M-C1', 'M-C2', 'M-D']
CTLS = ['positive', 'zero_direct']
PRODUCED_FP = 'e0f4869e2c32e15f2f3b905a242bcbaa09f7102cf6aaf151acf3e2ac11dff18f'   # model.py + params.py + inputs.json used for E3


def shard_rows(d):
    rows = []
    for p in sorted(d.glob('shard-*.jsonl.gz')):
        with gzip.open(p, 'rt') as f:
            rows.extend(json.loads(x) for x in f)
    rows.sort(key=lambda r: r['task_id'])
    return rows


def e3_keyed():
    """task_id order of experiments.e23: mechanism, control, pathway, set (1,000 sets each)."""
    out = {}
    for r in shard_rows(RES / '_shards' / 'e23'):
        tid = r['task_id']
        i, rest = tid % 1000, tid // 1000
        pw, rest = PWS[rest % 7], rest // 7
        ctl, mech = CTLS[rest % 2], MECHS[rest // 2]
        assert r['meta'] == {'set': i, 'control': ctl}, tid
        out[(pw, mech, ctl, i)] = r['reps']
    return out


def variant_keyed():
    import e3_variant as ev
    import model
    model.LINE_APPROVAL = True
    sets = ev.frozen_sets()
    tasks = ev.make_tasks(sets, None, ev.VARIANT_PWS)
    rows = shard_rows(RES / '_shards' / 'e3-variant')
    assert len(rows) == len(tasks)
    return {(t['pathway'], t['mechanism'], t['meta']['control'], t['meta']['set']): r['reps'] for t, r in zip(tasks, rows)}


def mean(reps, k):
    return float(np.mean([x['summary'][k] for x in reps]))


def rob_table(cells, base, keep):
    tab = []
    for ctl in CTLS:
        for pw in sorted({k[0] for k in cells}, key=lambda p: (p[:3], p)):
            for mech in MECHS:
                ks = [k for k in cells if k[0] == pw and k[1] == mech and k[2] == ctl and keep(k[3])]
                if not ks:
                    continue
                cov = np.array([mean(cells[k], 'coverage_10y') for k in ks])
                b = np.array([mean(base[('PW0', mech, ctl, k[3])], 'coverage_10y') for k in ks])
                tab.append({'pathway': pw, 'mechanism': mech, 'control': ctl, 'n_sets': len(ks),
                            'coverage_10y_p10': float(np.percentile(cov, 10)), 'coverage_10y_p50': float(np.percentile(cov, 50)),
                            'coverage_10y_p90': float(np.percentile(cov, 90)),
                            'P_money_flows_5y_mean': float(np.mean([mean(cells[k], 'money_flows_5y') for k in ks])),
                            'share_better_than_PW0': None if pw == 'PW0' else float(np.mean(cov > b))})
    return tab


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(RES / 'web'))
    a = ap.parse_args()
    out = Path(a.out)
    if out == RES / 'web' and (out / 'meta.json').exists() and json.loads((out / 'meta.json').read_text()).get('status') == 'preliminary':
        keep = RES / 'web-prelim'
        if keep.exists():
            raise SystemExit(f'{keep} exists; move it aside first')
        shutil.move(str(out), str(keep))                     # keep an earlier exploratory export aside
    out.mkdir(parents=True, exist_ok=True)

    with gzip.open(RES / 'e3-pathways' / 'runs.csv.gz', 'rt') as f:
        line = {(r['mechanism'], int(r['set'])): int(float(r['sw_line'])) for r in csv.DictReader(f)
                if r['pathway'] == 'PW0' and r['control'] == 'positive'}
    l0 = lambda m: (lambda i: line[(m, i)] == 0)
    e3, var = e3_keyed(), variant_keyed()
    for k, reps in var.items():
        assert line[(k[1], k[3])] == 0
    # check: shard means equal runs.csv (spot check every 997th row)
    with gzip.open(RES / 'e3-pathways' / 'runs.csv.gz', 'rt') as f:
        for j, r in enumerate(csv.DictReader(f)):
            if j % 997 == 0:
                k = (r['pathway'], r['mechanism'], r['control'], int(r['set']))
                assert abs(mean(e3[k], 'coverage_10y') - float(r['coverage_10y'])) < 1e-12, k

    keep0 = {m: l0(m) for m in MECHS}
    sel = lambda cells: {k: v for k, v in cells.items() if keep0[k[1]](k[3])}
    e3_l0, var_l0 = sel(e3), sel(var)
    var_named = {(k[0] + '-approval',) + k[1:]: v for k, v in var_l0.items()}

    main_tab = [r for r in rob_table(e3_l0, e3, lambda i: True) if r['control'] == 'positive']
    zero_tab = [r for r in rob_table(e3_l0, e3, lambda i: True) if r['control'] == 'zero_direct']
    pooled_tab = [r for r in rob_table(e3, e3, lambda i: True) if r['control'] == 'positive']
    var_tab = rob_table(var_named, e3, lambda i: True)

    # runs: main view only (sw_line 0, positive) so the site's histogram matches the main table
    rows = []
    for (pw, mech, ctl, i), reps in sorted(e3_l0.items(), key=lambda kv: (PWS.index(kv[0][0]), MECHS.index(kv[0][1]), kv[0][3])):
        if ctl != 'positive':
            continue
        rows.append({'pathway': pw, 'mechanism': mech, 'set': i, 'sw_line': 0,
                     'P_money_flows_5y': mean(reps, 'money_flows_5y'), 'installed_5y': mean(reps, 'installed_5y'),
                     'coverage_10y': mean(reps, 'coverage_10y')})
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
    with gzip.open(out / 'runs.csv.gz', 'wt', newline='') as f:
        f.write(buf.getvalue())

    import model, params
    inp = model.load_inputs(HERE / 'data' / 'inputs.json')
    months = model.run(params.default_params(), 'PW0', 'M-A', 1, inputs=inp)['months']

    def quant(cells):
        series = {}
        for (pw, mech, ctl, i), reps in cells.items():
            if ctl == 'positive':
                series.setdefault(f'{pw}|{mech}', []).extend(x['I_cum'] for x in reps)
        return {k: {'months': months, 'I_cum': {q: np.percentile(np.array(v), q, axis=0).round(2).tolist() for q in (10, 50, 90)}}
                for k, v in series.items()}

    def reach(cells):
        cnt, n = {}, {}
        for (pw, mech, ctl, i), reps in cells.items():
            if ctl != 'positive':
                continue
            n[pw] = n.get(pw, 0) + len(reps)
            for x in reps:
                for nd in x['path_nodes_reached']:
                    cnt.setdefault(pw, {}).setdefault(nd, 0)
                    cnt[pw][nd] += 1
        return {pw: {'runs': n[pw], 'nodes': {nd: c / n[pw] for nd, c in sorted(cnt.get(pw, {}).items())}} for pw in n}

    h = lambda f: hashlib.sha256((HERE / f).read_bytes()).hexdigest()
    fp = hashlib.sha256('\n'.join([h('model.py'), h('params.py'), h('data/inputs.json')]).encode()).hexdigest()
    n_by = {m: sum(1 for (mm, i), v in line.items() if mm == m and v == 0) for m in MECHS}
    meta = {'status': 'formal', 'label': LABEL, 'model_version': 'scenario model ' + PRODUCED_FP[:8],
            'model_fingerprint': fp, 'produced_by_fingerprint': PRODUCED_FP,
            'design_version': 'base design with approval variant', 'run_date': datetime.date.today().isoformat(),
            'n_param_sets': min(n_by.values()), 'n_param_sets_by_mechanism': n_by, 'replicates': 20,
            'seed': 146, 'horizon_months': 120, 'total_runs': len(rows) * 20,
            'pathways': PWS, 'mechanisms': MECHS, 'view': 'sw_line = 0 (no standing local APS line at the start, as today); positive-effect priors',
            'notes': [
                'Parameters were first screened against the 2022-2025 request lists (rejection filter; weak, ranges stay close to the priors; not a calibration).',
                'Scenario exploration under stated rules; scenario projections, not forecasts. Shares are shares of parameter sets, not probabilities of real outcomes.',
                'E3 runs were produced by the model identified by produced_by_fingerprint. Its approval switch is off for the base pathways and on only for the "-approval" variant runs.',
                'In the base pathways, PW4 has a standing local line from the start and PW5 adds one automatically after two years, with no approval step; PW2 must pass a Prop L amendment. The "-approval" variant puts PW4/PW5 through the same approval chain as PW2.',
                'PW1 ends in a hypothetical Director reallocation branch (probability and amount are assumptions).',
                'Pressure, a named owner and crew capacity act in the model only through the start probability or a cap; their small sensitivity reflects the model having no other channel for them, not their real-world importance.']}
    (out / 'meta.json').write_text(json.dumps(meta, indent=1))
    (out / 'params.json').write_text(json.dumps({'label': LABEL, 'schema': params.param_schema()}, indent=1))
    (out / 'quantiles.json').write_text(json.dumps({'label': LABEL, 'by_pathway_mechanism': quant(e3_l0),
                                                    'variant_by_pathway_mechanism': quant(var_named)}))
    (out / 'pathways.json').write_text(json.dumps({'label': LABEL, 'path_reach': reach(e3_l0), 'variant_path_reach': reach(var_named)}, indent=1))
    (out / 'robustness.json').write_text(json.dumps({
        'label': LABEL, 'columns_note': 'table = main view (sw_line 0, positive-effect priors); share_better_than_PW0 compares the same parameter set and seeds',
        'table': main_tab, 'table_zero_direct': zero_tab, 'table_pooled_sw_line': pooled_tab, 'table_variant_approval': var_tab}, indent=1))
    ph = json.loads((RES / 'e3-pathways' / 'posthoc.json').read_text())
    (out / 'prim.json').write_text(json.dumps({
        'label': LABEL, 'status': 'computed (all sw_line values, positive priors; corrected rule extraction, model/posthoc.py)',
        'outcome': 'money flows within 5 years in at least half of 20 replicates', 'boxes': ph['prim_full_rules_thr0.5']}, indent=1))
    for f in ('fig1-pathway-robustness.png', 'fig2-accountability-by-standing-line.png', 'fig3-sobol-total-effects.png'):
        if (RES / 'figures' / f).exists():
            shutil.copy2(RES / 'figures' / f, out / f)
    print('wrote', out, '| rows', len(rows), '| fingerprint', fp[:12])


if __name__ == '__main__':
    main()
