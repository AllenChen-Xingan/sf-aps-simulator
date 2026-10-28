# Model card: APS funding and coordination pathways (San Francisco)

## Model summary

| | |
|---|---|
| Type | Agent-based, rule-based scenario model; monthly time step; stochastic |
| Scope | The 76 accessible-pedestrian-signal (APS) requests pending at SFMTA in June 2026 and subsequent arrivals; 120-month projection from July 2026 |
| Decision-making agent | SFMTA capital-budget and grant staff (whether to start a funding application each month) |
| Rule-following actors | Engineering staff, Signal Shop crews, advocacy groups, external enforcement bodies; funding venues (HSIP, Prop L, General Fund, existing signal projects) |
| Implementation | Python; code and pinned environment in this package |
| Documentation | `docs/ODD+D.md` (description), `docs/TRACE.md` (development and testing), `docs/STRESS-ABS.md` (reporting checklist) |
| Author and licence | Allen Chen, 2026; code MIT, documentation and data CC BY 4.0 |

## Intended use

- Comparing, under stated rules and wide parameter uncertainty, which funding and coordination pathways are more robust than current practice for converting APS requests into funded installations.
- Identifying conditions under which funding flows (scenario discovery) and which uncertain inputs most influence outcomes (sensitivity analysis).
- Structuring discussion among the agency, advocates and budget bodies about where the request-to-application step breaks down.

## Uses the model is not suited to

- **Forecasting.** Outputs are shares of parameter combinations under specified rules, not probabilities of real-world outcomes or predicted installation counts.
- **Identifying the cause of the observed stall.** Six alternative explanations reproduce the 2022–2026 request lists about equally well; the model treats them as parallel settings.
- **Estimating the effect of any single component** of the accountability package (owner, deadlines, reporting, pressure). The package is tested as a whole.
- **Evaluating stronger forms of accountability.** Pressure, ownership and enforcement act in the model only by raising the monthly probability of starting an application; they supply no money, quotas or court remedies.
- **Other cities or other assets** without rebuilding the venue rules.

## Structure (XLRM)

| Element | Content |
|---|---|
| **X** — uncertainties | 98 parameters (`data/parameters.csv`), most without documentary values and sampled over ranges; six settings for why requests stall: unassigned responsibility, staffing constraints from 2024 or 2023, rising costs, technical constraints, combined |
| **L** — levers | Seven pathways: PW0 current practice; PW1 HSIP-first; PW2 local-first (Prop L line); PW3 accountability-first; PW4 crossing-specific allocation; PW5 design standards; PW6 existing hardware programme; plus an approval variant in which PW4 and PW5 lines require Prop L approval |
| **R** — relationships | Documented venue rules: HSIP eligibility, benefit–cost ratio and set-aside; Prop L amendment and allocation; General Fund windows; design, construction authorization, contracting and crew capacity (`docs/ODD+D.md` §8) |
| **M** — metrics | Robustness: share of combinations in which a pathway installs more crossings than current practice over ten years. Funding within five years: share of runs with at least one request-channel batch award. Conditions for funding flow (PRIM). Sensitivity indices (Morris, Sobol) |

## Evaluation

- Screening of parameter combinations against SFMTA request lists, July 2022 to February 2025, with a check against three later snapshots (`docs/TRACE.md` §6).
- Implementation verification: event replay, invariants, byte-identical results across serial and parallel execution, independent reading of the code against this documentation (`docs/TRACE.md` §5).
- Full reproduction from a clean environment (`docs/reproducibility.md`).

## Main results

Main comparison: parameter combinations starting without a standing local line (as at present), about 500 per setting; ranges span the six settings. Sampling error of the shares is about ±1.5 percentage points. Full tables are in `docs/results.md`.

| Pathway | Outperforms current practice (10-year installations) | Funding within five years |
|---|---|---|
| Design standards (PW5) | 95–97% | 84–91% |
| Crossing-specific allocation (PW4) | 92–97% | 87–91% |
| Existing hardware programme (PW6) | 92–95% | 68–79% |
| HSIP-first (PW1) | 89–95% | 65–78% |
| Local-first (PW2) | 87–92% | 59–73% |
| Accountability-first (PW3) | 67–89% | 36–68% |
| Current practice (PW0) | — | 3–31% |

- Pathways that provide or pursue continuing local money lead; accountability-first, which raises only the probability of starting an application, ranks lowest among the interventions in every setting.
- Without a standing line, accountability-first still outperforms current practice in 80% of combinations (pooled over settings), raising five-year funding from 18% to 56%; where a standing line already exists, the share falls to 46%.
- Scenario discovery (PRIM) finds that funding flows most reliably when a standing local line exists and reserves roughly 4–13% for APS; the size of the line is not itself a condition.
- When PW4 and PW5 lines must pass the same Prop L approval as PW2, their robustness is almost unchanged, but five-year funding falls to 51–66% and 47–63%.
- Sensitivity indices (Morris, Sobol) are in `docs/results.md`.

## Limitations

- The historical request lists constrain the parameters only weakly; most conclusions rest on documented rules and assumed ranges.
- Accountability measures have a single, narrow channel in the model (application initiation). Their low sensitivity ranking reflects that channel, not evidence that they are unimportant in practice.
- Whether signal-hardware upgrades can carry APS in an HSIP application rests on one interview; both possibilities are modelled.
- Costs per crossing for conduit and ramp work are not documented crossing by crossing.
- The model excludes citywide coverage beyond the request channel, peer-city systems, external accessibility standards and malfunctioning installed equipment.
- Mechanisms proposed by an adversarial language-model review (for example, district Prop L shares or shifting ramp costs to the curb-ramp programme) are unverified and not modelled.

## Ethical considerations

The model concerns a service for blind and low-vision pedestrians. Its outputs should not be read as a ranking of which residents deserve installations: crossing-level priorities come from SFMTA's own scoring rules, and the model inherits them. No personal data are used.
