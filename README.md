# SF APS ABM Model

An interactive page for exploring **under which conditions money flows** to install Accessible
Pedestrian Signals (APS) on San Francisco's request list. It runs an agent-based model month by month
in the browser, animates who acts on whom, and compares policy pathways against a pre-computed result set.

**Status: preliminary · uncalibrated · scenario projections, not forecasts.** Scenario exploration under stated rules — not a forecast,
not proof of cause. Parameters come from prior ranges that have not been calibrated to the 2022–2026
list snapshots yet; model rules are still under review. Pathway PW5 is withheld (its rule is not yet
defined) via `config.json`.

## Run locally

```sh
python3 -m http.server 8000      # from this folder
# open http://127.0.0.1:8000/
```

Static files only; GitHub Pages can host the folder as is. No CDN is needed at run time: Pyodide
(Python in WebAssembly) and numpy are self-hosted in `vendor/pyodide/` (about 16 MB, loaded once and
then cached by the browser).

## What is where

| Path | What |
|---|---|
| `index.html`, `assets/` | Page, styles, player and charts (`app.js`), model worker (`worker.js`) |
| `model/abm/` | The ABM, copied **unchanged** from the research repository (`model.py`, `params.py`, `inputs.json`); `SOURCE.txt` has sha256 checksums |
| `results/` | Result set exported by the ABM (`meta.json` … `runs.csv.gz`, copied unchanged), plus `runs-lite.json` (derived), `demo/` (one recorded run per pathway, played before the model loads) and `consistency.json` |
| `config.json` | Display flags, e.g. pathways whose results are withheld |
| `scripts/` | `rebuild.sh` (sync model and results → tests → demos), `vendor_pyodide.sh` |
| `tests/` | Consistency, replay and browser tests (below) |
| `docs/data-contract.md` | Interface agreed between the model and the page |

After any model change: `./scripts/rebuild.sh` (needs `ABM_DIR` or a local `.abm-path` file naming the
model folder; a Python venv with numpy 2.4.6 in `.venv`; Node with `npm install` in `tests/`).

## Tests

| Test | Command | Last result (2026-10-26) |
|---|---|---|
| **Consistency** — the browser runs the same Python file as the offline analysis. 67 fixed cases (every pathway × mechanism at defaults, 24 random parameter draws, one history-mode run) run in CPython and in Pyodide; every output and every event compared. Integers and strings exact; floats 1e-12 relative | `tests/run_consistency.sh` | CPython 3.14.8 vs Pyodide 314.0.7 (Python 3.14.2), numpy 2.4.6 both: **0 differences** over 19,582 events |
| **Replay** — the animation moves dots only from the event stream; replaying initial states + events must equal the model's own monthly stocks | `.venv/bin/python -I tests/test_replay.py` | 120 random runs, 14,400 months: **0 differences** |
| **Browser + accessibility** — headless Chromium: model loads, animation plays, log and live announcements, compare mode by keyboard, pause/step, no console errors, phone width without horizontal scroll, axe-core WCAG 2.1 A/AA in light, dark and reduced-motion phone views | `node tests/e2e.mjs` | 15/15 checks pass; axe: **0 violations** (light, dark, mobile). One item axe could not decide automatically (colour contrast of text over the chart band, light mode) — needs a manual check |

## Accessibility

The project is about blind and low-vision pedestrians, so the page is built to be used without sight:

- Semantic headings and landmarks, skip link, every control labelled; range sliders announce values with units.
- The animation has a text twin: an event log (`aria-live="polite"`) announces key events each month
  ("Caltrans approve funding for 9 intersections …"); routine filings are grouped.
- Every chart has a text summary (`aria-label`) and a data table (in a disclosure); status counts are a screen-reader table next to the dot view.
- The page keeps the simulation in front; settings, the event log, many-run comparisons and the About text are collapsed disclosures (one line each, keyboard reachable).
- Keyboard: all controls, Run/Pause/Step/Replay, scrollable tables are focusable.
- `prefers-reduced-motion` turns off movement; counts and log still update. Light and dark themes.
- **Screen-reader testing by a human pending** (VoiceOver / NVDA). Automated checks above do not replace it.

## Data sources

Public only: SFMTA APS request list snapshots (2022–2026); DataSF injury crashes (ubvf-ztfx, 2015–2025);
Caltrans HSIP Cycle 13 call and Local Roadway Safety Manual (2026); SFMTA Capital Improvement Program and
budget documents; SFCTA Prop L Five-Year Prioritization Program (2023); Mayor's Disability Council minutes.
One rule draws on an interview with SFMTA staff.

## Limits

Scenario exploration, not prediction; rules are set by people; many ranges are informed guesses;
request list only, San Francisco only; injury crashes only (benefits understated); history fit rests on
very few funding events. The result set and the live model can be different versions while the model
is under review (now: result set from design v8, live model one revision newer) — the About section shows both.

## AI assistance

Built with AI assistance (Anthropic's Claude): model code, simulations, tests and page; reviewed by a second AI model.

## Licences

Pyodide: MPL-2.0. numpy: BSD-3-Clause. See `vendor/pyodide/README.md`.
