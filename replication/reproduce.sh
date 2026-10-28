#!/usr/bin/env bash
# Reproduce the APS agent-based model results from this package.
#
#   ./reproduce.sh --quick          environment, file hashes, self-tests, E0 baseline, one Morris cell (~5 min)
#   ./reproduce.sh                  everything in --quick, then E1, E2/E3, approval variant, secondary analyses (posthoc.py),
#                                   figures, web export, one Morris cell and one Sobol cell (~2.5 h on 8 processes)
#   ./reproduce.sh --e4-full        as the default, but reruns all of E4a and E4b instead of one cell each (~+5.5 h)
#   ./reproduce.sh --make-sums      (re)write SHA256SUMS for every file in the package, then exit
#
# Options: --work DIR (default: ./_work)  --python EXE (default: python3.14, else python3)  --reuse-venv
#
# Nothing in code/ or results/ is modified. Code is copied to WORK/run/code and every experiment writes
# to WORK/run/results; each regenerated summary is then compared field by field with results/.
# The runner uses (CPU count - 2) worker processes; results do not depend on the number of workers.
set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE=full; WORK="$PKG/_work"; PY=""; REUSE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --quick) MODE=quick ;;
    --e4-full) MODE=e4full ;;
    --make-sums) MODE=sums ;;
    --work) WORK="$2"; shift ;;
    --python) PY="$2"; shift ;;
    --reuse-venv) REUSE=1 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

sha256() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$@"; else shasum -a 256 "$@"; fi; }

if [ "$MODE" = sums ]; then
  # Every regular file except SHA256SUMS itself, working files (_*) and caches; paths relative to the package.
  (cd "$PKG" && find . -type f ! -name SHA256SUMS ! -path './_*' ! -name '_*' ! -path '*/__pycache__/*' ! -name '.DS_Store' \
     | sed 's|^\./||' | LC_ALL=C sort | while IFS= read -r f; do sha256 "$f"; done) > "$PKG/SHA256SUMS"
  echo "wrote $PKG/SHA256SUMS ($(wc -l < "$PKG/SHA256SUMS" | tr -d ' ') files)"
  exit 0
fi

REF="$PKG/results"
LOG="$WORK/logs"; mkdir -p "$LOG"
STATUS="$WORK/status.tsv"; : > "$STATUS"
step() {  # step NAME COMMAND...  -> runs, times, logs, records PASS/FAIL; stops on failure
  local name="$1"; shift
  local t0; t0=$(date +%s)
  echo "== $name"
  if "$@" > "$LOG/$name.log" 2>&1; then
    local dt=$(( $(date +%s) - t0 )); printf '%s\tPASS\t%ss\n' "$name" "$dt" >> "$STATUS"
    tail -n 3 "$LOG/$name.log" | sed 's/^/   /'; echo "   PASS (${dt}s)"
  else
    local dt=$(( $(date +%s) - t0 )); printf '%s\tFAIL\t%ss\n' "$name" "$dt" >> "$STATUS"
    tail -n 20 "$LOG/$name.log" | sed 's/^/   /'; echo "   FAIL (${dt}s) - see $LOG/$name.log"; exit 1
  fi
}

# ---------------------------------------------------------------- 1. environment
if [ -z "$PY" ]; then PY=$(command -v python3.14 || command -v python3); fi
WANT=$(tr -d '\n' < "$PKG/environment/python-version.txt")
HAVE=$("$PY" --version 2>&1)
[ "$HAVE" = "$WANT" ] || echo "warning: $HAVE found, package was produced with $WANT; results may differ in the last digits"
VENV="$WORK/venv"
if [ "$REUSE" = 0 ] || [ ! -x "$VENV/bin/python" ]; then
  rm -rf "$VENV"
  step env-create "$PY" -m venv "$VENV"
  step env-install "$VENV/bin/python" -m pip install --no-deps -r "$PKG/environment/requirements-lock.txt"
fi
VPY="$VENV/bin/python"
step env-check bash -c "'$VPY' -m pip check && '$VPY' -m pip freeze | diff - '$PKG/environment/requirements-lock.txt' && '$VPY' --version && uname -a"

# ---------------------------------------------------------------- 2. file integrity
if [ -f "$PKG/SHA256SUMS" ]; then
  step sha256 bash -c "cd '$PKG' && grep -E '  (code|environment|results)/' SHA256SUMS | $(command -v sha256sum >/dev/null && echo 'sha256sum -c' || echo 'shasum -a 256 -c') --quiet - && echo 'all listed files match'"
else
  echo "warning: SHA256SUMS not found; skipping file integrity check"
fi

# ---------------------------------------------------------------- 3. working copy
RUN="$WORK/run"
rm -rf "$RUN"; mkdir -p "$RUN/results"
cp -R "$PKG/code" "$RUN/code"
rm -rf "$RUN/code/__pycache__"
TOOLS="$WORK/tools"; mkdir -p "$TOOLS"

# Comparison tool: exact equality of parsed JSON; reports differing leaves and the largest numeric difference.
cat > "$TOOLS/compare_json.py" <<'PYEOF'
import json, math, sys
new, ref = sys.argv[1], sys.argv[2]
ignore = set(sys.argv[3].split(',')) if len(sys.argv) > 3 and sys.argv[3] else set()
diffs, maxabs = [], 0.0
def walk(a, b, path):
    global maxabs
    if path and path.split('.')[-1] in ignore:
        return
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                diffs.append(f'{path}.{k}: key present in only one file')
            else:
                walk(a[k], b[k], f'{path}.{k}' if path else str(k))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append(f'{path}: list length {len(a)} vs {len(b)}')
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f'{path}[{i}]')
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        if not (a == b or (isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b))):
            diffs.append(f'{path}: {a} vs {b}')
            maxabs = max(maxabs, abs(a - b))
    elif a != b:
        diffs.append(f'{path}: {str(a)[:60]!r} vs {str(b)[:60]!r}')
A, B = json.load(open(new)), json.load(open(ref))
walk(A, B, '')
same_bytes = open(new, 'rb').read() == open(ref, 'rb').read()
print(f'{ref}: {len(diffs)} differing fields; max abs numeric difference {maxabs:g}; byte-identical {same_bytes}'
      + (f'; ignored keys {sorted(ignore)}' if ignore else ''))
for d in diffs[:20]:
    print('  ', d)
sys.exit(1 if diffs else 0)
PYEOF
cmpj() { "$VPY" -I "$TOOLS/compare_json.py" "$@"; }

# One E4 cell, rebuilt exactly as experiments.e4a / e4b build it (same unit-cube sample, same replicate seeds).
cat > "$TOOLS/e4_cell.py" <<'PYEOF'
import json, sys
from pathlib import Path


def main():
    code, kind, cell, ref, out = Path(sys.argv[1]), sys.argv[2], sys.argv[3], Path(sys.argv[4]), Path(sys.argv[5])
    sys.path.insert(0, str(code))
    import numpy as np
    import experiments as ex, params, runner
    rows, prob = ex.problem()
    if kind == 'morris':
        from SALib.sample import morris as ms
        from SALib.analyze import morris as ma
        pw, mech = cell.split('|')
        X = ms.sample(prob, 20, num_levels=4, seed=ex.MASTER_SEED + 1)                     # pass 1
        tasks = [{'task_id': i, 'params': ex.decode(u, rows), 'pathway': pw, 'mechanism': mech,
                  'seeds': ex.seeds_for(f'e4a-1-{i}', ex.REPS), 'meta': {'i': i}} for i, u in enumerate(X)]
        rr = runner.run_tasks(tasks, out / '_shards')
        Y = np.array([np.mean([x['summary']['coverage_10y'] for x in r['reps']]) for r in rr])
        Si = ma.analyze(prob, X, Y, num_levels=4, seed=ex.MASTER_SEED)
        new = {'mu_star': dict(zip(prob['names'], map(float, Si['mu_star']))), 'sigma': dict(zip(prob['names'], map(float, Si['sigma'])))}
        old = json.loads(ref.read_text())['cells'][cell]['pass1']
    else:
        from SALib.sample import sobol as ss
        from SALib.analyze import sobol as sa
        pw, mech, bg = cell.split('|')
        assert bg == 'default'
        chosen = json.loads((ref.parent / 'morris.json').read_text())['chosen_for_sobol']
        sub = [r for r in rows if r['name'] in chosen]
        p2 = {'num_vars': len(sub), 'names': [r['name'] for r in sub], 'bounds': [[0.0, 1.0]] * len(sub)}
        X = ss.sample(p2, 256, calc_second_order=False, seed=ex.MASTER_SEED)
        tasks = []
        for i, u in enumerate(X):
            base = dict(params.default_params())
            base.update({k: v for k, v in ex.decode(u, sub).items() if k in p2['names']})
            tasks.append({'task_id': i, 'params': base, 'pathway': pw, 'mechanism': mech,
                          'seeds': ex.seeds_for(f'e4b-{i}', ex.REPS), 'meta': {'i': i, 'bg': bg}})
        rr = runner.run_tasks(tasks, out / '_shards')
        Y = np.array([np.mean([x['summary']['coverage_10y'] for x in r['reps']]) for r in rr])
        Si = sa.analyze(p2, Y, calc_second_order=False, seed=ex.MASTER_SEED)
        new = {k: dict(zip(p2['names'], map(float, Si[k]))) for k in ('S1', 'S1_conf', 'ST', 'ST_conf')}
        old = json.loads(ref.read_text())['cells'][cell]['N256']
    out.mkdir(parents=True, exist_ok=True)
    (out / 'new.json').write_text(json.dumps(new, indent=1, sort_keys=True))
    (out / 'ref.json').write_text(json.dumps(old, indent=1, sort_keys=True))
    print(kind, cell, len(tasks), 'tasks x', ex.REPS, 'replicates')


if __name__ == '__main__':   # required: worker processes re-import this module
    main()
PYEOF

# ---------------------------------------------------------------- 4. self-tests (always)
step selftest-runner bash -c "cd '$RUN/code' && '$VPY' -I runner.py --selftest"
step selftest-replay bash -c "cd '$RUN/code' && '$VPY' -I replay_check.py && ! grep -qE 'MISMATCH|RECON ' '$LOG/selftest-replay.log'"

# E0: baseline.py reads raw/history-long.csv and raw/baseline-simulation-results.json at the package root.
# These raw inputs are optional; without them the check is skipped and results/e0-baseline-check.json is used as distributed.
if [ -f "$PKG/raw/history-long.csv" ] && [ -f "$PKG/raw/baseline-simulation-results.json" ]; then
  mkdir -p "$RUN/raw"
  cp "$PKG/raw/history-long.csv" "$PKG/raw/baseline-simulation-results.json" "$RUN/raw/"
  step e0-baseline bash -c "cd '$RUN' && '$VPY' -I code/baseline.py"
  step e0-compare cmpj "$RUN/results/e0-baseline-check.json" "$REF/e0-baseline-check.json"
else
  echo "== e0-baseline: skipped (raw/history-long.csv and raw/baseline-simulation-results.json not present)"
  printf 'e0-baseline\tSKIP\t0s\n' >> "$STATUS"
fi

# E4a, one cell (PW0 x M-A, first pass): 1,980 tasks.
step e4a-cell "$VPY" -I "$TOOLS/e4_cell.py" "$RUN/code" morris 'PW0|M-A' "$REF/e4-sensitivity/morris.json" "$WORK/e4a-cell"
step e4a-cell-compare cmpj "$WORK/e4a-cell/new.json" "$WORK/e4a-cell/ref.json"

if [ "$MODE" = quick ]; then
  echo; echo "quick mode finished:"; column -t "$STATUS"; exit 0
fi

# ---------------------------------------------------------------- 5. main experiments
R="$RUN/results"
step e1 bash -c "cd '$RUN/code' && '$VPY' -I experiments.py e1"
step e1-compare cmpj "$R/e1-fit/fit-table.json" "$REF/e1-fit/fit-table.json"
step e23 bash -c "cd '$RUN/code' && '$VPY' -I experiments.py e23"
step e3-compare cmpj "$R/e3-pathways/robustness.json" "$REF/e3-pathways/robustness.json"
step e2-compare cmpj "$R/e2-prim/prim.json" "$REF/e2-prim/prim.json"
step e3-variant bash -c "cd '$RUN/code' && '$VPY' -I e3_variant.py --verify"
step e3-variant-compare cmpj "$R/e3-variant/summary.json" "$REF/e3-variant/summary.json" seconds
step posthoc bash -c "cd '$RUN/code' && '$VPY' -I posthoc.py"
step posthoc-compare cmpj "$R/e3-pathways/posthoc.json" "$REF/e3-pathways/posthoc.json"
step figures bash -c "cd '$RUN/code' && '$VPY' -I figures.py"
step figures-compare bash -c "cd '$R/figures' && for f in *.png; do if cmp -s \"\$f\" '$REF/figures/'\"\$f\"; then echo \"\$f identical\"; else echo \"\$f differs (inspect visually; PNG bytes depend on the matplotlib/freetype build)\"; fi; done"
step web-export bash -c "cd '$RUN/code' && '$VPY' -I final_export.py"
step web-compare bash -c "for f in meta params pathways prim quantiles robustness; do '$VPY' -I '$TOOLS/compare_json.py' '$R/web/'\$f.json '$REF/web/'\$f.json run_date || exit 1; done"

# ---------------------------------------------------------------- 6. sensitivity
if [ "$MODE" = e4full ]; then
  step e4a bash -c "cd '$RUN/code' && '$VPY' -I experiments.py e4a"
  step e4a-compare cmpj "$R/e4-sensitivity/morris.json" "$REF/e4-sensitivity/morris.json"
  step e4b bash -c "cd '$RUN/code' && '$VPY' -I experiments.py e4b"
  step e4b-compare cmpj "$R/e4-sensitivity/sobol.json" "$REF/e4-sensitivity/sobol.json"
else
  step e4b-cell "$VPY" -I "$TOOLS/e4_cell.py" "$RUN/code" sobol 'PW0|M-A|default' "$REF/e4-sensitivity/sobol.json" "$WORK/e4b-cell"
  step e4b-cell-compare cmpj "$WORK/e4b-cell/new.json" "$WORK/e4b-cell/ref.json"
fi

echo; echo "finished ($MODE):"; column -t "$STATUS"
