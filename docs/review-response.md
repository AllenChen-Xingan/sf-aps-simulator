# Review response log (codex cross-model review)

Each finding: verdict after checking against the current files, what changed, where to verify.

## Round 1 (reviewed e1023ec; fixes in b51435c, 6fbf196)

| # | Finding | Verdict | Change | Verify |
|---|---|---|---|---|
| P1 #1 | `sw_relax`, `sw_ss4a` switches had no effect in the model | Valid | Removed from the model's parameter table by the model owner; the panel is generated from `model/abm/params-schema.json`, so the switches are gone | `params-schema.json` has only `sw_pe`, `sw_consult`, `sw_si02`, `sw_line` |
| P1 #2 | PW4 reroute could never trigger | Valid (model) | Fixed in the model (`parent_nominal`); synced | `model/abm/model.py`, consistency + replay tests |
| P1 #3 | "Differences are not luck of the draw" overstated | Valid | Text now: same parameter sets and seeds; pathways draw events in a different order, so outside shocks are not identical | `index.html` "All pathways compared" |
| P1 #4 | First-month installs missing from summary | Valid (model) | Fixed in the model; synced | model reconciliation test (model owner); replay test here |
| P2 #5 | PW5 status inconsistent; described steps not implemented | Valid | PW5 description rewritten to the model's two steps (design rule → local line after two years); caution note via `config.json`; README aligned (round 2 #3) | `assets/app.js` PATHWAYS.PW5; `config.json`; README Status |
| P2 #6 | Data tables closed and lost focus during playback | Valid | Tables are fixed nodes inside persistent disclosures; only `thead`/`tbody` content is replaced, at start and end of a run | `assets/app.js` `fillTimelineTable` |
| P2 #7 | Histogram had no data table | Valid | Bin/count table added | `#hist-data` |
| P2 #8 | Consistency claim shown without a report | Valid | Defaults to "not yet verified"; superseded by round 2 #5 | — |
| P2 #9 | Defaults called "middle of range" | Valid | Now "the model's default value" | `index.html` settings |

## Round 2 (reviewed between b51435c and 6fbf196; fixes in the commit after 6fbf196)

| # | Finding | Verdict | Change | Verify |
|---|---|---|---|---|
| P1 #1 | HSIP request could exceed remaining cap (contingency added after cap check) | Valid (model) | Fixed by the model owner (cap check includes contingency); synced | consistency + replay tests on fingerprint `2d4bf860ae8a` |
| P1 #2 | `t_lag` slider had no effect | Valid (model) | Parameter deleted by the model owner; slider disappears automatically | `params-schema.json` has no `t_lag` |
| P2 #3 | README still said PW5 withheld | Valid | README Status: PW5 runs, rule inferred, assumptions named | `README.md` Status |
| P2 #4 | Percentile and band compared across model versions | Valid | One fingerprint for model.py + params.py + inputs.json (`scripts/fingerprint.py`). Band, histogram, percentile and the pathway table note appear only when the result set's `meta.model_fingerprint` equals the loaded model's; otherwise the page says the comparison is hidden because the versions differ. The current result set predates the latest model fixes and has no fingerprint, so comparisons are hidden until the model owner re-runs it | `assets/app.js` `sameModel()`; `tests/e2e.mjs` "comparison hidden" check |
| P2 #5 | Consistency fingerprint covered model.py only and was not checked against what the worker loads | Valid | Report carries the full fingerprint and both runtimes; the worker hashes the bytes it actually fetched (SHA-256 via Web Crypto, same formula) and the page shows "passed" only if they are equal | `assets/worker.js`; `tests/compare.py`; e2e check "consistency verified against the loaded model files" |
| P2 #6 | Contract pointed to a non-existent test script; counts stale | Valid | `docs/data-contract.md` §3 rewritten (entry `tests/run_consistency.sh`, 67 cases, 17 browser checks); README counts updated | `docs/data-contract.md` §3 |

## Not verifiable by the reviewer

`results/` and `vendor/` were excluded from the review scan. Evidence instead: `results/consistency.json`
(fingerprint, cases, events, runtimes); `vendor/pyodide/README.md` and `scripts/vendor_pyodide.sh`
(numpy wheel sha256 checked against `pyodide-lock.json` at copy time).

## Status after round 2

Result set re-run by the model owner on design v10 with `model_fingerprint` = loaded model (`2d4bf860ae8a…`); comparisons are shown again. Consistency 67 cases / 19,689 events, 0 differences; replay 0 differences; browser 17/17; axe 0 violations.

## Round 3 (reviewed 2067e3c)

| # | Finding | Verdict | Change | Verify |
|---|---|---|---|---|
| P1 #1 | BCR package screen omitted contingency | Valid (model) | Model owner fixing; rebuild after | — |
| P2 #2 | Pass not bound to the runtime actually loaded | Valid | Both: the Pyodide test side now loads `vendor/pyodide/` (the published runtime) instead of the npm copy; the worker reports Pyodide / Python / numpy versions and the page shows a pass only if fingerprint **and** runtime equal the report's `browser_runtime` | `tests/pyodide_side.mjs`; `assets/worker.js` `RUNTIME`; `showConsistency()`; e2e "consistency verified against the loaded model files and runtime" |
| P2 #3 | `drawRobust` / `drawReach` not gated; version text not refreshed after load | Valid | `sameModel()` uses only the worker-computed fingerprint (no fallback). One `refreshComparisons()` redraws the pathway table, reach table, set description, version line, consistency text and any shown run comparison; it runs at start and again when the worker reports. Before load: "shown once the model has loaded and its version is checked" | `assets/app.js` `refreshComparisons`; e2e "comparisons hidden before load, shown after" |
| P2 #4 | Runs during loading silently ignore settings | Valid | Each result carries its source. A recorded run says "Recorded run (mechanism, seed, parameters) … your settings were not used", in the result block and the stage title, and stays until the next run | `sourceText()`; e2e "recorded run labelled while loading", "label persists after model is ready" (runtime download held back 6 s) |
| P2 #5 | Docs said exact / bit-for-bit | Valid | One rule everywhere: integers and text equal, decimals within 1e-12 relative or 1e-9 absolute (`math.isclose`); "a pass is not a bit-for-bit claim" | `docs/data-contract.md` §1, §1a, §3; README tests table; page "Checks" |
| P2 #6 | Clean-machine test prerequisites incomplete | Valid | README splits "only to view" (any static server) from "tests / rebuild" (Python 3.14 + numpy 2.4.6 venv, Node ≥ 20, `npx playwright install chromium`) with commands | README "Run locally" |

Tests after round 3 (model fingerprint 2d4bf860ae8a…, runtime Pyodide 314.0.7 / Python 3.14.2 / numpy 2.4.6 from `vendor/`): consistency 67 cases / 19,689 events, 0 differences; replay 0 differences; browser 20/20; axe 0 violations.
