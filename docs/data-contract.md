# Data contract: ABM ↔ web simulator (v1, agreed with abm 2026-10-26)

Owner of the model: `abm` session. Owner of the site: `web` session.
The site never edits model files; it copies them in at build time (`scripts/sync_model.sh`).

## 1. Live mode (browser runs the model)

Choice: **run the same Python model in the browser via Pyodide**, not a JS port.
Reason: the model is still changing; a port drifts. Same code + same seed gives the same output up to
floating-point library differences, so the consistency test uses one rule (see §3): integers and text
equal; decimals within 1e-12 relative or 1e-9 absolute. A pass is not a claim of bit-for-bit identity.

What the site needs from `abm/model/`:

| Need | Why |
|---|---|
| Single-run path imports only stdlib + `numpy` (no Mesa, ema_workbench, SALib, pandas, scipy) | Pyodide ships numpy; the others are slow or unavailable. Mesa may stay for the batch runner. |
| No file reads at import; inputs passed as Python objects (`load_inputs(dir)` separate from `run(...)`) | Browser feeds data from JSON it fetched |
| One entry point: `run(params, pathway, mechanism, seed, start="2026-07", horizon_months=120, emit_events=False, inputs=None) -> dict` (`inputs` from `load_inputs(dir)` or fed from JSON) | Site calls it per click |
| RNG: `numpy.random.default_rng(seed)` only, created inside `run` | Determinism across Python and Pyodide |
| `default_params()` and `param_schema()` returning the D10 table: name, label_en, unit, low, high, default, kind (`uniform`/`switch`/`level`/`discrete`), applies_to (mechanisms), phase (`fit`/`projection`/`all`) | Builds the control panel; one source of truth |

`run` returns (JSON-serialisable):

```json
{
  "months": ["2026-07", "..."],
  "stocks": {"C": [..], "N": [..], "Fi": [..], "Fs": [..], "I_cum": [..]},
  "events": [{"month": "2027-04", "actor": "A2", "target": "HSIP", "action": "submit", "intersections": ["03rd Street / 16th Street", "..."], "detail": "C13 bundle with SG015, BCR 7.2"}],
  "path_nodes_reached": ["PW1:start", "PW1:C14", "..."],
  "summary": {"money_flows_5y": 0/1, "installed_5y": int, "high_priority_5y": float, "coverage_10y": int,
              "recovery_time": int|null, "cost_by_actor": {"SFMTA": $, "SFCTA": $, "Caltrans/HSIP": $}}
}
```

### 1a. Event stream (drives the network animation — added 2026-10-26)

Every interaction the model executes is one event, emitted in the month it happens, in execution order:

| field | values |
|---|---|
| `month` | `YYYY-MM` |
| `actor` | node id of who acts (table below) |
| `target` | node id of who/what receives it (actor or venue) |
| `action` | `request` (new resident request) · `classify` · `press` (advocacy pressure) · `deflect` (buck-passing reply: cost / no money / ask SFCTA) · `start_prep` · `submit` · `miss_deadline` · `eligibility_fail` · `approve` · `reject` · `allocate` (local money) · `veto` / `defer` · `red_flag` · `extend` / `return_funds` · `contract_out` · `install` · `owner_quit` / `owner_filled` · `enforce_up` · `pathway_switch` · `failure:F-a`…`F-m` |
| `intersections` | list of intersection keys touched (empty if none) |
| `state_changes` | optional `[{"key", "from", "to"}]` so the swimlane view moves dots without re-deriving rules |
| `detail` | short English fragment, no names of people |

Node ids (agreed with abm, = 02 design):

| id | kind | label |
|---|---|---|
| `C3` | actor | Residents who request APS |
| `C2` | actor | Advocates (incl. Mayor's Office on Disability channel) |
| `A1` | actor | SFMTA APS engineering |
| `A2` | actor | SFMTA capital budget & grants |
| `A3` | actor | SFMTA Signal Shop crews |
| `DIR` | actor | SFMTA Director (only in F-k reallocation events) |
| `SFCTA` | actor | SFCTA Board |
| `CT` | actor | Caltrans (HSIP) |
| `D1` | actor | External enforcement |
| `HSIP` `PROPL` `GF` `SS4A` `PARENT` `MDC` | venue | HSIP call · Prop L EP17 · General Fund/CIP · SS4A · parent signal project · Mayor's Disability Council |

Extra actions (abm): `prep_abort`, `topup`, `partner_delay`, `batch_fund` (right after `approve`/`allocate`).
Floats: PCG64 stream is stable across numpy versions; libm may differ in the last bit, so decimals compare within 1e-12 relative or 1e-9 absolute (`math.isclose`), integers and text exactly.
`meta.json` also carries `design_version` (02 version) and `mechanisms`.

A switch `emit_events=True` (default False for batch speed) is fine.

## 2. Batch mode (pre-computed results the site browses)

Please write to `abm/results/web/` (any of these may be marked preliminary):

| File | Content |
|---|---|
| `meta.json` | `model_version` (git short hash or date), `status`: `"preliminary"`/`"final"`, run date, N param sets, R replicates, seed set |
| `params.json` | `param_schema()` output (same as live mode) |
| `runs.csv` (or `.json`) | one row per (param set × pathway × mechanism): sampled params + replicate-mean outputs (`installed_5y`, `coverage_10y`, `P_money_flows_5y`, `recovery_time` median, censored share). Keep ≤ ~20 MB total; drop to a sample if bigger |
| `quantiles.json` | per pathway (× switch 2×2): monthly p10/p50/p90 of `I_cum` and stocks |
| `prim.json` | per pathway: boxes `[{"rules":[{"param","low","high"}], "coverage_test", "density_test", "split": k}]`, threshold 0.25/0.5/0.75, plus CART cross-check summary |
| `pathways.json` | per pathway: nodes, transitions, share of runs reaching each node (`path_reach`) — for the metro map |
| `robustness.json` | ranking table: positive-effect vs zero-effect columns, share better than PW0, max regret |
| `fit.json` (optional) | E1 acceptance rate per mechanism × prior width; H1 holdout pass/fail |

## 3. Consistency test (updated after codex round 2)

Entry point: `tests/run_consistency.sh` (CPython side `tests/py_side.py`, Pyodide side `tests/pyodide_side.mjs`,
comparison `tests/compare.py`, shared cases `tests/cases.py`). 67 fixed cases: every pathway × mechanism at
default parameters (7 × 6), 24 random parameter draws, one history-mode run. Every output and every event
compared: integers and strings equal, decimals within 1e-12 relative or 1e-9 absolute (`math.isclose`). The Pyodide side loads the self-hosted runtime in `vendor/pyodide/` — the same files the page publishes — and the report records its Pyodide, Python and numpy versions; the page shows a pass only if both the model fingerprint and these runtime versions equal what its worker loaded. The report `results/consistency.json` carries
`model_fingerprint` (see `scripts/fingerprint.py`) and both runtime versions. `tests/test_replay.py` checks
that replaying events reproduces the model's monthly stocks; `tests/e2e.mjs` runs 20 browser and
accessibility checks.

`meta.json` of the result set must carry the same `model_fingerprint`, computed when the set is run;
the page hides many-run comparisons when it differs from the loaded model.

## 4. Wording limits (from writing brief / stats report)

Site text says "scenario exploration", "under these rules", "conditional on"; never "predict", "prove", "forecast".
