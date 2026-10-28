"""E0 check: reproduce the author's earlier Markov baseline (request-list transition model).

Same states, same person-period rate estimate, same Gamma(count + 0.5, exposure)
uncertainty, same backtest (fit 2022-07..2024-02, predict 2024-02..2026-06).
Uses numpy's Generator with a fixed seed, so draws differ from the original
`random` module run; the check is that medians and p10-p90 bands agree.

Both inputs are distributed with the package in raw/ (package root):
  raw/history-long.csv                 request-list snapshots in long form, compiled by the author from
                                       the published SFMTA APS request lists (see docs/data-dictionary.md)
  raw/baseline-simulation-results.json results of the author's earlier Markov baseline analysis

Run: python -I code/baseline.py
"""
import csv, json, math
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]                 # package root (code/..)
SRC = ROOT / 'raw' / 'history-long.csv'
REF = ROOT / 'raw' / 'baseline-simulation-results.json'
OUT = Path(__file__).resolve().parents[1] / 'results' / 'e0-baseline-check.json'
MAP = {'C-candidate': 'C', 'N-funding': 'N', 'F-inhouse': 'Fi', 'F-signal': 'Fs', 'INSTALLED': 'I'}
STATES = ['C', 'N', 'Fi', 'Fs']
ALLOWED_ZERO = {('C', 'I'), ('N', 'I'), ('C', 'Fi'), ('C', 'Fs'), ('N', 'Fs'), ('Fs', 'I'), ('Fi', 'I')}
MO = 30.4375


def load():
    rows = list(csv.DictReader(open(SRC)))
    snaps = sorted({r['snapshot'] for r in rows})
    seq = defaultdict(dict)
    for r in rows:
        seq[r['key']][r['snapshot']] = MAP.get(r['state'], r['state'])
    return snaps, seq


def months(a, b):
    return (date.fromisoformat(b) - date.fromisoformat(a)).days / MO


def estimate(seq, era, lo, hi):
    cnt, exp = defaultdict(int), defaultdict(float)
    for s in seq.values():
        for a, b in zip(era, era[1:]):
            if a < lo or b > hi:
                continue
            x, y = s.get(a), s.get(b)
            if x not in STATES or y not in STATES + ['I']:
                continue
            m = months(a, b)
            if x == y:
                exp[x] += m
            else:
                exp[x] += m / 2
                cnt[(x, y)] += 1
    return cnt, exp


def draw_rates(cnt, exp, rng):
    q = {}
    for a in STATES:
        for b in STATES + ['I']:
            if a == b:
                continue
            c = cnt.get((a, b), 0)
            if c == 0 and (a, b) not in ALLOWED_ZERO:
                continue
            q[(a, b)] = rng.gamma(c + 0.5, 1 / (exp.get(a, 0) or 1e-9))
    return q


def step(state, q, rng):
    out = [(b, r) for (a, b), r in q.items() if a == state]
    tot = sum(r for _, r in out)
    if tot <= 0 or rng.random() > 1 - math.exp(-tot):
        return state
    u, acc = rng.random() * tot, 0.0
    for b, r in out:
        acc += r
        if u <= acc:
            return b
    return out[-1][0]


def backtest(seq, snaps, era, fit, window, rng, sims=2000):
    cnt, exp = estimate(seq, era, *fit)
    start, end = window
    arr = defaultdict(list)
    for s in seq.values():
        first = next((x for x in snaps if s.get(x) not in (None, '-')), None)
        if first and first > '2022-07-29' and s[first] in STATES:
            arr[first].append(s[first])
    pts = [x for x in era if start < x <= end]
    res = []
    for _ in range(sims):
        q = draw_rates(cnt, exp, rng)
        pop = [s[start] for s in seq.values() if s.get(start) in STATES]
        prev = start
        for p in pts:
            for _m in range(round(months(prev, p))):
                pop = [step(x, q, rng) for x in pop]
            pop += arr.get(p, [])
            prev = p
        res.append(sum(x == 'I' for x in pop))
    v = sorted(res)
    return {'median': float(np.median(v)), 'p10': v[int(.1 * len(v))], 'p90': v[int(.9 * len(v)) - 1]}


def main(seed=146):
    rng = np.random.default_rng(seed)
    snaps, seq = load()
    era = [s for s in snaps if s >= '2022-07-29']
    ours = backtest(seq, snaps, era, ('2022-07-29', '2024-02-20'), ('2024-02-20', '2026-06-30'), rng)
    ref = json.load(open(REF))['backtest']['out_of_sample: fit 2022-07..2024-02, predict 2024-02..2026-06']['simulated']['installed']
    ok = abs(ours['median'] - ref['median']) <= 1 and abs(ours['p10'] - ref['p10']) <= 2 and abs(ours['p90'] - ref['p90']) <= 2
    out = {'seed': seed, 'ours': ours, 'reference_simulate_py': ref, 'observed': 13, 'match_within_tolerance': ok}
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out))


if __name__ == '__main__':
    main()
