"""Copy the ABM's exported result set (<abm>/results/web/) into results/,
unchanged, plus one derived file the page needs: runs-lite.json (pathway, mechanism, the three
outcomes per parameter set) so the browser does not have to unzip 3 MB of CSV.
Run: python3 -I scripts/sync_results.py"""
import csv, gzip, io, json, os, shutil, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
# Source: $ABM_RESULTS, or <model folder from .abm-path>/../results/web (.abm-path is not committed)
_abm = os.environ.get('ABM_DIR') or (ROOT / '.abm-path').read_text().splitlines()[0]
SRC = Path(os.environ.get('ABM_RESULTS') or Path(_abm).parent / 'results' / 'web')
DST = ROOT / 'results'; DST.mkdir(exist_ok=True)
for f in ('meta.json', 'params.json', 'quantiles.json', 'pathways.json', 'robustness.json', 'prim.json', 'runs.csv.gz'):
    shutil.copy2(SRC / f, DST / f)
rows = list(csv.DictReader(io.TextIOWrapper(gzip.open(SRC / 'runs.csv.gz'), 'utf-8')))
num = lambda v: None if v in ('', 'None', 'nan') else round(float(v), 3)
lite = {'columns': ['pathway', 'mechanism', 'set', 'installed_5y', 'coverage_10y', 'P_money_flows_5y'],
        'rows': [[r['pathway'], r['mechanism'], int(r['set']), num(r['installed_5y']), num(r['coverage_10y']), num(r['P_money_flows_5y'])] for r in rows]}
json.dump(lite, open(DST / 'runs-lite.json', 'w'), separators=(',', ':'))
print('results synced:', json.load(open(DST / 'meta.json'))['label'], '|', len(rows), 'rows')
