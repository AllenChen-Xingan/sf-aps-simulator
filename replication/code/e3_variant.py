"""Approval variant: PW4/PW5 standing line requires the same Prop L approval as PW2 (reported separately).

PW4 and PW5 get their standing local line only through the same approval chain as PW2
(Prop L amendment: q_veto, t_defer, th_defer; on failure one General Fund request: q_gf).
Runs only the sw_line = 0 sets (today's status quo: no standing line; with sw_line = 1 the
line already exists and the variant changes nothing). Parameter sets, replicate seeds and
the PW0 comparison are those of the main E3 runs (common random numbers).

    python -I e3_variant.py --limit 5 --verify --out <_tmp dir>   # pilot + reconstruction check
    python -I e3_variant.py                                          # full run -> results/e3-variant/
"""
import argparse, csv, gzip, json, os, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import model, params, runner  # noqa: E402
from experiments import MASTER_SEED, REPS, seeds_for  # noqa: E402

RES = HERE.parent / 'results'
VARIANT_PWS = ['PW4', 'PW5']
KEEP = ('P_money', 'coverage_10y', 'installed_5y')
SRC = {'P_money': 'money_flows_5y'}                     # summary key behind each column, as in e23


def frozen_sets():
    """Rebuild the E3 parameter sets exactly as experiments.e23 does (scale 1)."""
    acc = json.loads((RES / 'e1-fit' / 'accepted-sets.json').read_text())
    proj = [r['name'] for r in params.param_schema() if r['phase'] == 'projection']
    out = {}
    for mech in model.MECHANISMS:
        pool = acc.get(mech, [])
        rng = np.random.default_rng([MASTER_SEED, 23, model.MECHANISMS.index(mech)])
        fresh = params.sample(1000, rng, names=set(proj))
        sets = []
        for i in range(1000):
            base = dict(pool[int(rng.integers(len(pool)))])
            base.update({k: fresh[i][k] for k in proj})
            sets.append(base)
        out[mech] = sets
    return out


def frozen_rows():
    with gzip.open(RES / 'e3-pathways' / 'runs.csv.gz', 'rt') as f:
        return {(r['pathway'], r['mechanism'], r['control'], int(r['set'])): r for r in csv.DictReader(f)}


def _init(flag):
    runner._init()
    model.LINE_APPROVAL = flag


def run(tasks, out_dir, flag, workers=None, shard_size=25):
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob('shard-*.jsonl.gz'):
        old.unlink()
    workers = workers or max(1, (os.cpu_count() or 2) - 2)
    shards = [(i, tasks[k:k + shard_size], str(out_dir)) for i, k in enumerate(range(0, len(tasks), shard_size))]
    with ProcessPoolExecutor(max_workers=workers, initializer=_init, initargs=(flag,)) as ex:
        for n, _ in enumerate(ex.map(runner._run_shard, shards), 1):
            if n % 20 == 0 or n == len(shards):
                print(f'{time.strftime("%H:%M:%S")} shards {n}/{len(shards)}', flush=True)
    return runner.merge(out_dir)


def make_tasks(sets, limit, pws):
    tasks, tid = [], 0
    for mech in model.MECHANISMS:
        idx = [i for i, s in enumerate(sets[mech]) if int(s['sw_line']) == 0][:limit]
        for control in ('positive', 'zero_direct'):
            for pw in pws:
                for i in idx:
                    q = dict(sets[mech][i])
                    if control == 'zero_direct':
                        q.update(b_own=0.0, b_spec=0.0, b_ov=0.0, b_pr=0.0)
                    tasks.append({'task_id': tid, 'params': q, 'pathway': pw, 'mechanism': mech,
                                  'seeds': seeds_for(f'e23-{mech}-{i}', REPS), 'meta': {'set': i, 'control': control}})
                    tid += 1
    return tasks


def records(tasks, rows):
    recs = []
    for t, r in zip(tasks, rows):
        sm = [x['summary'] for x in r['reps']]
        recs.append({'pathway': t['pathway'], 'mechanism': t['mechanism'], 'control': t['meta']['control'],
                     'set': t['meta']['set'], **{k: float(np.mean([x[SRC.get(k, k)] for x in sm])) for k in KEEP},
                     'nodes': ';'.join(sorted({nd for x in r['reps'] for nd in x['path_nodes_reached']}))})
    return recs


def verify(sets, frozen, out):
    """With the switch off, rebuilt tasks must reproduce the frozen E3 rows exactly."""
    tasks = [t for t in make_tasks(sets, 3, ['PW4', 'PW5', 'PW0'])]
    recs = records(tasks, run(tasks, out / '_shards-verify', False))
    bad = 0
    for r in recs:
        f = frozen[(r['pathway'], r['mechanism'], r['control'], r['set'])]
        for k in KEEP:
            if float(f[k]) != r[k]:
                bad += 1
                print('VERIFY DIFF', r['pathway'], r['mechanism'], r['control'], r['set'], k, f[k], r[k])
    print(f'verify: {len(recs)} rebuilt tasks vs frozen E3 rows, {bad} field differences')
    return bad == 0


def summarise(recs, frozen):
    out = {}
    for ctl in ('positive', 'zero_direct'):
        for pw in VARIANT_PWS:
            per = {}
            for mech in model.MECHANISMS:
                rr = [r for r in recs if r['pathway'] == pw and r['control'] == ctl and r['mechanism'] == mech]
                if not rr:
                    continue
                base = [float(frozen[('PW0', mech, ctl, r['set'])]['coverage_10y']) for r in rr]
                orig = [frozen[(pw, mech, ctl, r['set'])] for r in rr]
                per[mech] = {
                    'n_sets': len(rr),
                    'share_better_than_PW0': float(np.mean([r['coverage_10y'] > b for r, b in zip(rr, base)])),
                    'P_money': float(np.mean([r['P_money'] for r in rr])),
                    'median_cov10': float(np.median([r['coverage_10y'] for r in rr])),
                    'frozen_share_better': float(np.mean([float(o['coverage_10y']) > b for o, b in zip(orig, base)])),
                    'frozen_P_money': float(np.mean([float(o['P_money']) for o in orig]))}
            if per:
                rng = lambda k: [min(v[k] for v in per.values()), max(v[k] for v in per.values())]
                out[f'{pw}|{ctl}'] = {'by_mech': per, **{k: rng(k) for k in
                                      ('share_better_than_PW0', 'P_money', 'frozen_share_better', 'frozen_P_money')}}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=None, help='sets per mechanism (pilot)')
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--out', default=str(RES / 'e3-variant'))
    a = ap.parse_args()
    out = Path(a.out)
    sets, frozen = frozen_sets(), frozen_rows()
    if a.verify and not verify(sets, frozen, out):
        sys.exit(1)
    model.LINE_APPROVAL = True
    tasks = make_tasks(sets, a.limit, VARIANT_PWS)
    t0 = time.time()
    shard_dir = RES / '_shards' / 'e3-variant' if out == RES / 'e3-variant' else out / '_shards'
    recs = records(tasks, run(tasks, shard_dir, True))
    dt = time.time() - t0
    print(f'variant: {len(tasks)} tasks x {REPS} reps in {dt:.0f} s ({dt / len(tasks):.2f} s/task)')
    with gzip.open(out / 'runs.csv.gz', 'wt', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(recs[0].keys()))
        w.writeheader()
        w.writerows(recs)
    h = lambda f: __import__('hashlib').sha256((HERE / f).read_bytes()).hexdigest()
    fp = __import__('hashlib').sha256('\n'.join([h('model.py'), h('params.py'), h('data/inputs.json')]).encode()).hexdigest()
    (out / 'summary.json').write_text(json.dumps({
        'note': 'Approval variant: PW4/PW5 standing line must pass Prop L amendment, then one GF request. '
                'sw_line = 0 sets only; PW0 and main-run PW4/PW5 from results/e3-pathways/runs.csv.gz (same sets and seeds).',
        'model_fingerprint': fp, 'n_tasks': len(tasks), 'replicates': REPS, 'seconds': round(dt),
        'table': summarise(recs, frozen)}, indent=1))


if __name__ == '__main__':
    main()
