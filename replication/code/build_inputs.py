"""Build model/data/inputs.json: the only data file the model reads.

The model (model.py) never reads files at import; it takes this JSON as a dict,
so the browser (Pyodide) can fetch the same file. Sources:
  - request-list history: raw/history-long.csv
  - 76 pending sites: raw/pending-2026.csv (rank)
    + raw/countdown-lpi-pending76.csv (route, countdown)
    + code/data/pending76-crashes.csv (crashes by group, severity, window)
raw/history-long.csv is distributed with the package; pending-2026.csv and the countdown / LPI table
are not, and must be placed in raw/ (package root) to rerun this script. history-long.csv and
pending-2026.csv are compiled by the author from the published SFMTA APS request lists; the
countdown / LPI table is compiled by the author (see docs/data-dictionary.md).
Execution status of the 11 "fold into existing project" sites follows
the actor-evidence register (docs/actors-and-evidence.md; table typed in below, with its source).

Run: python3 -I code/build_inputs.py
"""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]                 # package root (code/..)
HERE = Path(__file__).resolve().parent
HIST = ROOT / 'raw' / 'history-long.csv'
PEND = ROOT / 'raw' / 'pending-2026.csv'
P76 = ROOT / 'raw' / 'countdown-lpi-pending76.csv'
CRASH = HERE / 'data' / 'pending76-crashes.csv'
OUT = HERE / 'data' / 'inputs.json'
MAP = {'C-candidate': 'C', 'N-funding': 'N', 'F-inhouse': 'Fi', 'F-signal': 'Fs', 'INSTALLED': 'I'}

# Nominal finish of the parent project for fold-in sites (docs/actors-and-evidence.md, E14):
# Contract 35 construction Fall 2026 - Winter 2027/28; WACSS Spring 2027 - Fall 2028;
# 13th St "Winter 2027"; Powell "Spring 2026" (already past); Tenderloin SS4A not dated.
PARENT_FINISH = {
    '06th Avenue / Irving': '2028-02',
    'Eddy / Fillmore': '2028-10',
    '13th Street / Duboce / Mission / Otis': '2027-12',
    '13th Street / Folsom': '2027-12',
    '13th Street / South Van Ness': '2027-12',
    'Ellis / Powell': '2026-06',
    'Golden Gate / Larkin': None,
}

# Ledger section 3.2, "execution status" of the 11 fold-in sites.
FOLD = {
    '06th Avenue / Irving': 'yes',
    'Eddy / Fillmore': 'likely',
    'Golden Gate / Larkin': 'likely',
    '13th Street / Duboce / Mission / Otis': 'unverified',
    '13th Street / Folsom': 'unverified',
    '13th Street / South Van Ness': 'unverified',
    'Ellis / Powell': 'unverified',
    '05th Street / Mission': 'no_unfunded',
    'Harrison / Main': 'no_parent_done',
    'Jones / Market / McAllister': 'no_parent_done',
    'Stockton / Sutter': 'no_parent_done',
}


def history():
    rows = list(csv.DictReader(open(HIST)))
    snaps = sorted({r['snapshot'] for r in rows})
    seq = {}
    rank = {}
    for r in rows:
        seq.setdefault(r['key'], {})[r['snapshot']] = MAP.get(r['state'], r['state'])
        if r['rank'] in ('high', 'medium', 'low'):
            rank[r['key']] = r['rank']
    era = [s for s in snaps if s >= '2022-07-29']
    start = era[0]
    init = [{'key': k, 'state': s[start], 'rank': rank.get(k, 'medium')}
            for k, s in seq.items() if s.get(start) in ('C', 'N', 'Fi', 'Fs')]
    arrivals = []
    for k, s in seq.items():
        first = next((x for x in snaps if s.get(x) not in (None, '-')), None)
        if first and first > start and s[first] in ('C', 'N', 'Fi', 'Fs'):
            arrivals.append({'snapshot': first, 'key': k, 'state': s[first], 'rank': rank.get(k, 'medium')})
    stocks = {}
    for x in era:
        c = {st: 0 for st in ('C', 'N', 'Fi', 'Fs', 'I')}
        for s in seq.values():
            if s.get(x) in c:
                c[s[x]] += 1
        stocks[x] = c
    return {'snapshots': era, 'initial_2022_07': init, 'arrivals': arrivals, 'observed_stocks': stocks}


def pending():
    rank = {r['location']: r['rank'] for r in csv.DictReader(open(PEND))}
    cr = {r['location']: r for r in csv.DictReader(open(CRASH))}
    out = []
    for r in csv.DictReader(open(P76)):
        loc = r['location']
        o = r['other_corridor_project']
        if loc in FOLD:
            route = 'fold'
        elif o.startswith('possible'):
            route = 'corridor'
        else:
            route = 'unidentified'
        c = cr.get(loc, {})
        crashes = {}
        for g in ('pb', 'nonpb'):
            for sev in ('KA', 'B', 'C'):
                for w in ('w3', 'w5'):
                    v = c.get(f'{g}_{sev}_{w}', '')
                    crashes[f'{g}_{sev}_{w}'] = int(v) if v not in ('', None) else 0
        out.append({'key': loc, 'state': MAP.get(r['status_2026'], r['status_2026']),
                    'rank': rank.get(loc, 'medium'), 'route': route, 'fold': FOLD.get(loc),
                    'sg015_corridor': 'SG015' in o,
                    'parent_finish': PARENT_FINISH.get(loc),
                    'missing_ped_heads': r['countdown_status'] == 'no',
                    'crash_matched': c.get('matched') == '1', 'crashes': crashes})
    return out


def main():
    data = {'version': 'dev', 'history': history(), 'pending76': pending()}
    OUT.write_text(json.dumps(data, indent=0))
    h = data['history']
    print(f"inputs.json: {len(h['initial_2022_07'])} initial sites, {len(h['arrivals'])} arrivals, "
          f"{len(data['pending76'])} pending; routes "
          f"{ {k: sum(p['route'] == k for p in data['pending76']) for k in ('fold', 'corridor', 'unidentified')} }")


if __name__ == '__main__':
    main()
