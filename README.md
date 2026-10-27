# SF APS ABM Model

An interactive page for exploring **under which conditions money flows** to install Accessible
Pedestrian Signals (APS) on San Francisco's request list. It runs an agent-based model month by month
in the browser, animates who acts on whom, and compares policy pathways against a pre-computed result set.

**Status: preliminary · uncalibrated · scenario projections, not forecasts.** Scenario exploration under stated rules — not a forecast,
not proof of cause. Parameters were screened against the 2022–2025 request lists (a weak rejection
filter; ranges stay close to the priors; not a calibration). The result set is the formal one (design
v14, frozen). Its main view starts with no standing local APS line, as today. It also includes a variant in which
PW4/PW5's local line must pass the same approval chain as PW2 (view only; not runnable in the page) and
the rule-finding (PRIM) conditions. None of the shares are probabilities of real outcomes: "money within
5 years" and "steps reached" are shares of runs; "did better than the status quo" is the share of
parameter sets that installed more within ten years than the status quo with the same set. Pathway PW5 (design rule) runs, but its rule is inferred: the hardware-change rate and the
APS add-on budget are assumptions (shown as a note via `config.json`). PW1's last step (Director
reallocation) is a hypothetical fallback. Many-run comparisons appear only when the result set's model fingerprint equals the
fingerprint of the model files the browser actually loaded (`scripts/fingerprint.py`).

## Run locally

**Only to view the page:** any static file server, no other dependency.

```sh
python3 -m http.server 8000      # from this folder, then open http://127.0.0.1:8000/
```

Static files only; GitHub Pages can host the folder as is. No CDN is needed at run time: Pyodide
(Python in WebAssembly) and numpy are self-hosted in `vendor/pyodide/` (about 16 MB, loaded once and
then cached by the browser). Until the model has loaded, Run plays a recorded run with default settings
and the result says so.

**To run the tests or rebuild:** Python 3.14 with a venv holding numpy 2.4.6, Node.js 20 or newer, and
Playwright's Chromium.

```sh
python3 -m venv .venv && .venv/bin/pip install numpy==2.4.6
(cd tests && npm install && npx playwright install chromium)
./tests/run_consistency.sh            # CPython vs the self-hosted Pyodide runtime
.venv/bin/python -I tests/test_replay.py
node tests/e2e.mjs                    # headless browser + accessibility
```

## What is where

| Path | What |
|---|---|
| `index.html`, `assets/` | Page, styles, player and charts (`app.js`), actor cards, relationships and plain-English event text (`story.js`), model worker (`worker.js`) |
| `model/abm/` | The ABM, copied **unchanged** from the research repository (`model.py`, `params.py`, `inputs.json`); `SOURCE.txt` has sha256 checksums |
| `results/` | Result set exported by the ABM (`meta.json` … `runs.csv.gz`, copied unchanged), plus `runs-lite.json` (derived), `demo/` (one recorded run per pathway, played before the model loads) and `consistency.json` |
| `config.json` | Display flags, e.g. pathways whose results are withheld |
| `scripts/` | `rebuild.sh` (sync model and results → tests → demos), `vendor_pyodide.sh` |
| `tests/` | Consistency, replay and browser tests (below) |
| `docs/data-contract.md` | Interface agreed between the model and the page |

After any model change: `./scripts/rebuild.sh` (needs `ABM_DIR` or a local `.abm-path` file naming the
model folder; a Python venv with numpy 2.4.6 in `.venv`; Node with `npm install` in `tests/`).

## Tests

| Test | Command | Last result (2026-10-27) |
|---|---|---|
| **Consistency** — the browser runs the same Python files as the offline analysis. The report records the model fingerprint (model.py + params.py + inputs.json) and both runtimes; the page shows a pass only if that fingerprint equals the one the browser worker computes from the bytes it loaded. 67 fixed cases (every pathway × mechanism at defaults, 24 random parameter draws, one history-mode run) run in CPython and in Pyodide; every output and every event compared. Integers and strings equal; decimals within 1e-12 relative or 1e-9 absolute (a pass is not a bit-for-bit claim). The Pyodide side uses the same self-hosted runtime the page publishes, and the page also checks the runtime versions its worker loaded | `tests/run_consistency.sh` | CPython 3.14.8 vs Pyodide 314.0.7 (Python 3.14.2), numpy 2.4.6 both: **0 differences** over 19,857 events |
| **Replay** — the animation moves dots only from the event stream; replaying initial states + events must equal the model's own monthly stocks | `.venv/bin/python -I tests/test_replay.py` | 120 random runs, 14,400 months: **0 differences** |
| **Browser + accessibility** — headless Chromium: model loads, animation plays, log and live announcements, compare mode by keyboard, pause/step, no console errors, phone width without horizontal scroll, axe-core WCAG 2.1 A/AA in light, dark and reduced-motion phone views | `node tests/e2e.mjs` | 32/32 checks pass (incl. actor cards by keyboard, a run started while the model loads, and the pathway table checked against the result file); axe: **0 violations** (light, dark, mobile). One item axe could not decide automatically (colour contrast of text over the chart band, in light and dark mode) — needs a manual check |

## Accessibility

The project is about blind and low-vision pedestrians, so the page is built to be used without sight:

- Semantic headings and landmarks, skip link, every control labelled; range sliders announce values with units.
- Every actor box is a button (Enter/Space opens a card; Escape closes it and returns focus); all relationships are also given as a text list; legend items highlight their links on focus.
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
very few funding events. Pressure, a named owner and crew capacity act in the model only through the
chance of starting an application or a monthly cap, so their small sensitivity reflects the model, not
their real-world importance. The live model and the result set share one fingerprint (the result set was produced by the frozen
model; the current `model.py` adds the approval switch, off by default and bit-identical when off) —
the About section shows both. Many-run comparisons cover runs with no standing line at the start; with
that switch on, the page hides them.

## AI assistance

Built with AI assistance (Anthropic's Claude): model code, simulations, tests and page; reviewed by a second AI model.

## Licences

Pyodide: MPL-2.0. numpy: BSD-3-Clause. See `vendor/pyodide/README.md`.
