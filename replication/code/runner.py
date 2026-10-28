"""Parallel batch runner for E1-E4 (and the preliminary set).

Each task = (task_id, params dict, pathway, mechanism, seeds, start, horizon). A task's
replicate seeds are fixed before dispatch, so results do not depend on which worker
runs it or in what order. Workers write shard files (one gzip JSON-lines file per shard);
merge() reads all shards and orders rows by task_id, so the merged output is identical
to a single-process run. Default workers = CPU count - 2 (leave two cores for other sessions).

    from runner import run_tasks, make_tasks
    rows = run_tasks(tasks, out_dir, workers=None)

Self-test: python -I runner.py --selftest   (compares 1 process vs N processes byte for byte)
"""
import gzip, json, os, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import model  # noqa: E402

_INPUTS = None


def _init():
    global _INPUTS
    _INPUTS = model.load_inputs(HERE / 'data' / 'inputs.json')


def _summ(res):
    """Replicate-level summaries kept for analysis (no event streams)."""
    return [{'summary': r['summary'], 'path_nodes_reached': r['path_nodes_reached'],
             'I_cum': r['stocks']['I_cum'], **({'snapshot_stocks': r['snapshot_stocks']} if 'snapshot_stocks' in r else {})}
            for r in res]


def _run_shard(args):
    shard_id, tasks, out_dir = args
    if _INPUTS is None:
        _init()
    path = Path(out_dir) / f'shard-{shard_id:05d}.jsonl.gz'
    with gzip.open(path, 'wt') as f:
        for t in tasks:
            model.SG105_END = t.get('sg105_end', '2024-06')   # E1 breakpoint scan; default as in model.py
            res = [model.run(t['params'], t['pathway'], t['mechanism'], sd, start=t.get('start', '2026-07'),
                             horizon_months=t.get('horizon', 120), inputs=_INPUTS) for sd in t['seeds']]
            f.write(json.dumps({'task_id': t['task_id'], 'meta': t.get('meta', {}), 'reps': _summ(res)},
                               sort_keys=True) + '\n')
    return str(path)


def run_tasks(tasks, out_dir, workers=None, shard_size=50):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob('shard-*.jsonl.gz'):
        old.unlink()
    workers = workers or max(1, (os.cpu_count() or 2) - 2)
    shards = [(i, tasks[k:k + shard_size], str(out_dir)) for i, k in enumerate(range(0, len(tasks), shard_size))]
    if workers == 1:
        _init()
        for sh in shards:
            _run_shard(sh)
    else:
        with ProcessPoolExecutor(max_workers=workers, initializer=_init) as ex:
            list(ex.map(_run_shard, shards))
    return merge(out_dir)


def merge(out_dir):
    rows = []
    for p in sorted(Path(out_dir).glob('shard-*.jsonl.gz')):
        with gzip.open(p, 'rt') as f:
            rows.extend(json.loads(line) for line in f)
    rows.sort(key=lambda r: r['task_id'])
    return rows


def make_tasks(psets, pathways, mechanisms, seeds, start='2026-07', horizon=120):
    """Common random numbers: the same parameter sets and the same seed list in every cell."""
    tasks, tid = [], 0
    for pw in pathways:
        for mech in mechanisms:
            for i, ps in enumerate(psets):
                tasks.append({'task_id': tid, 'params': ps, 'pathway': pw, 'mechanism': mech, 'seeds': list(seeds),
                              'start': start, 'horizon': horizon, 'meta': {'set': i}})
                tid += 1
    return tasks


def _selftest():
    import numpy as np
    import params
    import tempfile
    rng = np.random.default_rng(146)
    ps = params.sample(12, rng)
    seeds = [int(x) for x in rng.integers(0, 2 ** 31 - 1, size=3)]
    tasks = make_tasks(ps, model.PATHWAYS, ['M-A', 'M-D'], seeds)
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        one = run_tasks(tasks, a, workers=1, shard_size=7)
        many = run_tasks(tasks, b, workers=max(2, (os.cpu_count() or 2) - 2), shard_size=7)
    same = json.dumps(one, sort_keys=True) == json.dumps(many, sort_keys=True)
    print(f'selftest: {len(tasks)} tasks x {len(seeds)} reps; 1 process vs parallel identical: {same}')
    sys.exit(0 if same else 1)


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        _selftest()
