"""Copy the ABM's exported result set (<abm>/results/web/) into results/,
unchanged, plus one derived file the page needs: runs-lite.json (pathway, mechanism, the three
outcomes per parameter set) so the browser does not have to unzip 3 MB of CSV.
Run: python3 -I scripts/sync_results.py"""
import csv, gzip, io, json, os, re, shutil, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
# Source: $ABM_RESULTS, or <model folder from .abm-path>/../results/web (.abm-path is not committed)
_abm = os.environ.get('ABM_DIR') or (ROOT / '.abm-path').read_text().splitlines()[0]
SRC = Path(os.environ.get('ABM_RESULTS') or Path(_abm).parent / 'results' / 'web')
DST = ROOT / 'results'; DST.mkdir(exist_ok=True)
_tf = ROOT / '.private-terms'
TERMS = re.compile('|'.join(re.escape(w) for w in _tf.read_text().split()), re.I) if _tf.exists() else None
_meta = json.loads((SRC / 'meta.json').read_text(encoding='utf-8'))
if _meta.get('n_param_sets', 0) < int(os.environ.get('MIN_SETS', 100)):   # guard against test batches
    sys.exit(f"meta.json has only {_meta.get('n_param_sets')} parameter sets; not syncing (set MIN_SETS to override)")
for f in ('meta.json', 'params.json', 'quantiles.json', 'pathways.json', 'robustness.json', 'prim.json'):
    txt = (SRC / f).read_text(encoding='utf-8')
    if TERMS and TERMS.search(txt):   # local term list (.private-terms, not committed) must not appear in public files
        sys.exit(f'{f}: contains a term from .private-terms; fix at the source')
    shutil.copy2(SRC / f, DST / f)
shutil.copy2(SRC / 'runs.csv.gz', DST / 'runs.csv.gz')
rows = list(csv.DictReader(io.TextIOWrapper(gzip.open(SRC / 'runs.csv.gz'), 'utf-8')))
num = lambda v: None if v in ('', 'None', 'nan') else round(float(v), 3)
lite = {'columns': ['pathway', 'mechanism', 'set', 'installed_5y', 'coverage_10y', 'P_money_flows_5y'],
        'rows': [[r['pathway'], r['mechanism'], int(r['set']), num(r['installed_5y']), num(r['coverage_10y']), num(r['P_money_flows_5y'])] for r in rows]}
json.dump(lite, open(DST / 'runs-lite.json', 'w'), separators=(',', ':'))
print('results synced:', json.load(open(DST / 'meta.json'))['label'], '|', len(rows), 'rows')
