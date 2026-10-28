"""Per-intersection crash counts by severity and window for the 76 pending requests.

Same 50 m planar rule as the intersection spatial snapshot (docs/data-dictionary.md).
Severity map (LRSM App. D classes): Fatal + Injury (Severe) -> KA; Injury (Other
Visible) -> B; Injury (Complaint of Pain) -> C. The DataSF file is injury crashes
only, so property-damage-only (O) crashes are absent and counted as 0 (this
understates benefits). Pedestrian file = DataSF ped collision groups (as in the
earlier snapshot; used only for the reconciliation check). All-mode file is
split into two mutually exclusive groups by dph_col_grp: 'pb' = any pedestrian
or bicycle involvement (BB, CC, DD, EE, FF, GG, HH, 'BB CC'; LRSM SI18PB/SI22PB
are 'Pedestrian and Bicycle'), and 'nonpb' = the complement (AA vehicles only,
II unknown, blank). Code meanings from the DataSF dph_col_grp_description field.

Check: the 2015-2025 pedestrian 50 m count must reproduce crashes_50m_2015_2025
in the spatial snapshot for every matched row, otherwise the script stops.
Raw inputs are not distributed with the package; place them in raw/ (package root):
  raw/datasf-ubvf-ztfx-ped-crash-points-2015-2025.csv  DataSF "Traffic Crashes Resulting in Injury"
  raw/datasf-ubvf-ztfx-all-crash-points-2015-2025.csv  (dataset ubvf-ztfx): pedestrian and all-mode extracts
  raw/intersections-spatial-20261022.csv               intersection coordinates and 50 m pedestrian counts,
                                                       compiled by the author (reconciliation check)
  raw/countdown-lpi-pending76.csv                      countdown / LPI check table for the 76 pending
                                                       sites, compiled by the author
Retrieval dates and field definitions are in docs/data-dictionary.md.

Run: python -I code/data_prep.py
"""
import csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]                 # package root (code/..)
PED = ROOT / 'raw' / 'datasf-ubvf-ztfx-ped-crash-points-2015-2025.csv'
ALL = ROOT / 'raw' / 'datasf-ubvf-ztfx-all-crash-points-2015-2025.csv'
SP = ROOT / 'raw' / 'intersections-spatial-20261022.csv'
P76 = ROOT / 'raw' / 'countdown-lpi-pending76.csv'
OUT = Path(__file__).resolve().parent / 'data' / 'pending76-crashes.csv'
SEV = {'Fatal': 'KA', 'Injury (Severe)': 'KA', 'Injury (Other Visible)': 'B', 'Injury (Complaint of Pain)': 'C'}
WINDOWS = {'w3': ('2023-01-01', '2025-12-31'), 'w5': ('2021-01-01', '2025-12-31'), 'w11': ('2015-01-01', '2025-12-31')}
from math import cos, pi


def load(path):
    pts = []
    for r in csv.DictReader(open(path)):
        try:
            lon, lat = float(r['tb_longitude']), float(r['tb_latitude'])
        except ValueError:
            continue
        g = r.get('dph_col_grp', '').strip()
        pts.append((lon, lat, r['collision_date'][:10], SEV.get(r['collision_severity'], 'C'),
                    'nonpb' if g in ('AA', 'II', '') else 'pb'))
    return pts


def near(lon0, lat0, pts):
    c = cos(lat0 * pi / 180)
    return [p for p in pts if ((p[0] - lon0) * 111320 * c) ** 2 + ((p[1] - lat0) * 110540) ** 2 <= 2500]


def main():
    ped, allm = load(PED), load(ALL)
    sp = {r['location']: r for r in csv.DictReader(open(SP)) if r['group'] == 'c'}
    p76 = list(csv.DictReader(open(P76)))
    rows, bad = [], []
    for r in p76:
        s = sp.get(r['location'])
        out = {'location': r['location'], 'status_2026': r['status_2026']}
        if not s or not s['lon']:
            out['matched'] = 0
            rows.append(out)
            continue
        lon, lat = float(s['lon']), float(s['lat'])
        np_, na = near(lon, lat, ped), near(lon, lat, allm)
        out['matched'] = 1
        for w, (a, b) in WINDOWS.items():
            sets = (('ped', np_), ('pb', [p for p in na if p[4] == 'pb']), ('nonpb', [p for p in na if p[4] == 'nonpb']))
            for tag, pts in sets:
                sel = [p for p in pts if a <= p[2] <= b]
                for k in ('KA', 'B', 'C'):
                    out[f'{tag}_{k}_{w}'] = sum(p[3] == k for p in sel)
        if s['crashes_50m_2015_2025'] and int(s['crashes_50m_2015_2025']) != sum(out[f'ped_{k}_w11'] for k in ('KA', 'B', 'C')):
            bad.append(r['location'])
        rows.append(out)
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys, restval='')
        w.writeheader(); w.writerows(rows)
    print(f'{len(rows)} rows, {sum(r["matched"] for r in rows)} matched; reconciliation mismatches: {len(bad)}')
    if bad:
        print('MISMATCH', bad[:10]); sys.exit(1)


if __name__ == '__main__':
    main()
