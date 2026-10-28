# TRACE document

This document records how the model was developed, tested and analysed, following the TRACE format ("TRAnsparent and Comprehensive model Evaludation"; Grimm et al., 2014). It has the eight TRACE elements: problem formulation, model description, data evaluation, conceptual model evaluation, implementation verification, model output verification, model analysis and model output corroboration. Each element ends with its limitations.

Companion documents: `docs/ODD+D.md` (model description), `docs/parameters.md` and `data/parameters.csv` (parameters), `docs/data-dictionary.md` (input files), `docs/actors-and-evidence.md` (evidence base), `docs/experiment-protocol.md` (experimental protocol and changes to the model), `docs/results.md` (all results), `docs/reproducibility.md` (how to rerun), `docs/references.md` (references).

All results are uncalibrated scenario projections, not forecasts.

## 1. Problem formulation

### 1.1 Context

The San Francisco Municipal Transportation Agency (SFMTA) keeps a public list of crossings at which residents have requested accessible pedestrian signals (APS) (SFMTA, 2020–2026, 2022a). Each listed request has one of five states: candidate (C), funding-needed (N), funded for installation by agency crews (Fi), funded through a signal project (Fs), or installed (I). Between July 2022 and February 2025 the stock of requests funded for installation by the agency's own crews from 22 to 1 and was not replenished, while unfunded candidate requests rose from 8 to 28 (`code/data/inputs.json`, `history.observed_stocks`). By June 2026, 76 requests were pending. The agency's APS policy assigns no owner to the step that turns the request list into a funding application (SFMTA, 2022a).

### 1.2 Purpose and questions

The model is built to compare arrangements for funding and coordinating APS installation, not to predict installations. It addresses three questions:

1. Which of six alternative explanations of the stall can reproduce the 2022–2026 request-list stocks, and with which parameter values?
2. Under which conditions does money reach the request channel within five years?
3. Which of seven pathways outperforms current practice across more of the sampled uncertainty?

Question 1 is answered by historical screening (E1), question 2 by scenario discovery (E2), question 3 by pathway comparison (E3); E4 is a global sensitivity analysis of the model itself.

### 1.3 Why a rule-based simulation

The request lists record only a handful of funding events over about six years: two batches entering agency-crew funding before mid-2024 and one after. Regression on such data cannot estimate effects reliably. By contrast, the rules that govern applications, eligibility, approval and delivery are documented in grant instructions, capital plans and policy (Caltrans, 2026c, 2026d; SFCTA, 2023b; SFMTA, 2026c). The model therefore encodes those rules and explores their consequences over ranges of undocumented quantities. The pathways are written as adaptive pathways: an initial action, a signpost that indicates failure, and a switch to another action (Haasnoot et al., 2013).

### 1.4 Intended users and outputs

The model informs the accompanying policy analysis of the APS request channel. The outputs used are shares of parameter combinations, not counts: the share in which a pathway outperforms current practice in ten-year installations, the share of runs with funding within five years, the conditions under which funding flows (boxes found by the Patient Rule Induction Method, PRIM), and sensitivity indices.

### 1.5 Scope

The model covers only the request channel: the 76 pending requests and new arrivals. It does not model citywide APS coverage, peer cities, external accessibility standards, or installed equipment that does not work.

### 1.6 Limitations

- The questions are posed for one agency and one request channel; conclusions do not transfer to other cities without re-specifying the rules.
- Question 1 cannot be answered with a verdict, because the rules and screening data do not discriminate between explanations (Section 6). The model can show only which explanations are compatible with the data.
- The outputs are shares across assumed ranges; they are not probabilities of real outcomes.

## 2. Model description

The model is described in full in `docs/ODD+D.md`, following the ODD protocol, second update (Grimm et al., 2020), with the ODD+D extension for human decisions (Müller et al., 2013). In brief: monthly time steps; a historical segment from July 2022 used for screening and a 120-month projection from July 2026; crossings with individual crash histories, cost classes and funding routes; one decision-making agent, SFMTA capital-budget and grant staff, whose monthly probability of starting a funding application follows a logistic function of a named owner, a specified deadline, oversight, decaying advocacy pressure, external enforcement, staffing strain and cost pressure; funding venues represented by rules (the federal Highway Safety Improvement Program, HSIP, administered by Caltrans; the local Prop L sales-tax programme; the city's General Fund; and existing signal projects); thirteen explicit failure events; and seven adaptive pathways.

The description was written from the code and is the model's specification: every rule cites the function that implements it.

### Limitations

- Only one actor makes decisions. Funding bodies, the board and advocates act by rule or by probability.
- The model contains no learning and no direct network between actors.

## 3. Data evaluation

### 3.1 Data sources and their use

Each data source was assigned to exactly one use, to avoid using the same information both to build the model and to test it. The allocation is:

| Use | Data | Source |
|---|---|---|
| Initial state | Request-list stocks on 29 July 2022 (C 8, N 17, Fi 22, Fs 27, I 30) | SFMTA (2020–2026) |
| Input, historical segment | Arrival month and initial state of each request first listed after July 2022 (replayed) | SFMTA (2020–2026) |
| Input, projection | Arrival rate of new requests, 6–17 per year | SFMTA (2020–2026) |
| Input, projection | Crash counts within 50 m of each pending crossing, by severity (fatal or severe, visible injury, complaint of pain) and window (3 and 5 years), separately for crashes involving a pedestrian or cyclist and all others | CCSF (n.d.) |
| Input, projection | Crash costs, crash modification factors and service lives of countermeasures | Caltrans (2026g) |
| Input, projection | HSIP eligibility, minimum benefit–cost ratio, agency ceiling, set-aside limits, milestones | Caltrans (2026c, 2026d, 2021a) |
| Input, projection | Unit costs of APS, conduit and curb-ramp work, signal-head upgrades, full signal modernisation | SFMTA (2026a, 2026c) |
| Input, both segments | Installation rate of funded agency-crew crossings `h_in` (0.59–1.41 per year) and of signal-project crossings `h_fs` (0.08–0.31 per year), estimated from transitions between 29 July 2022 and 21 February 2025 | SFMTA (2020–2026) |
| Screening | Stocks at five snapshots, January 2023 to February 2025 | SFMTA (2020–2026) |
| Retrospective check | Stocks at three snapshots, August 2025 to June 2026 | SFMTA (2020–2026) |
| Not used in rules or screening (Section 8) | Traffic-signal electrician positions and eligible lists; HSIP applications by SF in Cycle 12; installation rate around 2008–2010 | CCSF (2022, 2024, 2026); SF DHR (2022, 2023, 2025); Caltrans (2024a); SFMTA (2010) |

The full list of sources for every parameter is in `docs/parameters.md`, and the evidence base for actors and rules in `docs/actors-and-evidence.md`.

### 3.2 Evaluation of the request lists

The request lists are the only time series. Their evaluation produced four design decisions:

1. **Start date.** An early design started the historical segment in 2020 by assigning states to requests from later lists. The design was revised to start on 29 July 2022, the first list that records each request's status, so that no state is inferred from the future.
2. **Funding as batches.** Transitions from candidate to agency-crew funding occurred twice before the 2024 slowdown and once after it, too few for a stable rate. The design was revised to model funding as discrete batches (one award moves a group of crossings into funded status), so that the occurrence of a batch, rather than a smooth rate, is what the model must explain.
3. **Installation rates.** The agency-crew installation rate before the stop was estimated from 23 transitions over 289 crossing-months (about 0.96 per year; Gamma 95% interval 0.61–1.44). After the stop only 22 crossing-months of exposure with no installations exist, so a later rate cannot be estimated. The model therefore applies `h_in` only while funded agency-crew crossings exist.
4. **Separation of estimation and retrospective periods.** All rates were re-estimated from the period up to 21 February 2025 only, so that the three later snapshots do not inform any parameter.

### 3.3 Evaluation of the crash data

Crash points were matched to the pending crossings using a 50 m radius around each crossing; 75 of 76 crossings matched. The matching was implemented twice, in an earlier exploratory analysis of the same data by the author (not distributed) and in `code/data_prep.py`; the pedestrian crash counts for 2015–2025 of the two implementations agree for every crossing. Property-damage-only crashes are not in the data; they are counted as zero, which biases benefits downward. Only crashes before the decision month are used for any benefit–cost calculation. The unmatched crossing is handled by the scenario parameter `crash_impute` (excluded, median, or 90th percentile).

### 3.4 Undocumented quantities

Many behavioural and budgetary quantities have no documentary value: the probability of deflecting a request with a reply that no funds exist, the effects of an owner, deadline, oversight and pressure on initiation, advocacy frequency, crew capacity, the size and APS share of a standing local line, hardware-replacement frequency and the APS allowance under design standards, and the approval probabilities of a Prop L amendment and of a General Fund request. Each is sampled over a range (`docs/parameters.md`, source category "range, no documentary value"). One element, the one-time reallocation at the end of PW1, is a hypothetical fallback without documentary support (Section 4.4).

### Limitations

- The lists are short and contain few funding events, so screening constrains parameters only weakly (Section 6).
- The same transition records set the priors of `h_in` and `h_fs` and inform the screening stocks. This double use was tested with independent wide priors (Section 6.2).
- The exhaustion date of the earlier dedicated APS capital programme (project SG105, the source of the agency-crew funding batches before 2024) is not documented; it was scanned at five dates.
- The usable count of signal hardware that could carry APS under HSIP rests on an interview with SFMTA staff (personal communication, 2026); no public Caltrans determination was found, so a branch in which the carrier is unavailable (`sw_si02` = 0) is retained throughout.
- Unit costs at the level of individual crossings (which crossings need conduit or curb-ramp work) are not documented; they are sampled. E4 identifies them as one of the two most influential groups of inputs (Section 7), so crossing-level data on conduit and curb-ramp needs would reduce output uncertainty more than any other undocumented input in the model.

## 4. Conceptual model evaluation

### 4.1 Theoretical basis

The step "turn the request list into an application" is treated as a choice opportunity that may have no owner, following the garbage-can model of organisational choice (Cohen et al., 1972) and its formal treatment of buck-passing (Fioretti & Lomi, 2010). Actors' resources are classified by the dependence relations of policy-network theory (Bevir, 2009). Venue windows are exogenous calendars. Pathways follow dynamic adaptive policy pathways (Haasnoot et al., 2013).

### 4.2 Alternative explanations as parallel settings

Four explanations of the stall were derived from the evidence: unassigned responsibility (M-A), a staffing constraint (M-B), rising costs or technical constraints (M-C), and their combination (M-D). The design was revised twice to avoid narrowing them prematurely: the staffing explanation was split by start date (M-B1 from 2024, M-B2 from 2023), and the cost explanation was split into rising costs (M-C1) and a share of crossings that cannot technically be equipped (M-C2). All six settings share every rule except those listed in the switch matrix of `docs/ODD+D.md`, and share the same priors. The design was also revised so that no setting pre-assigns the combined explanation to particular phases; each mechanism can act before and after funding.

### 4.3 Main revisions of the conceptual model before the freeze

The design specification went through fourteen versions before the protocol was fixed. The principal revisions were:

1. **Decision layer.** An early additive probability of submission was replaced by a logistic start probability and an explicit task state machine (idle, preparing, submitted, missed, deflected), so that probabilities remain in [0, 1] and preparation time, deflection and missed deadlines are defined.
2. **Delivery.** A single transfer rate was replaced by a per-crossing installation hazard and a separate crew capacity, so that throughput is limited by the smaller of the two.
3. **HSIP rules.** The submission minimum benefit–cost ratio of 5.0, the cycle-specific selection threshold, the $10 million agency ceiling shared with other SF applications, the separate pedestrian-crossing set-aside (at most $400,000, with APS at most 20% of the project), the limit of three signal-related countermeasure types per application, the delivery milestones and the five-year eligibility rule (separate from project retention) were added from the Cycle 13 instructions and questions and answers (Caltrans, 2026c, 2026d). Benefits were revised to combine countermeasures separately for crashes involving pedestrians or cyclists and for all other crashes, and to apply hardware countermeasures only to crashes in the influence area of the upgraded signal (`f_aff`).
4. **Failure paths.** Thirteen failure events (F-a to F-m), each with trigger, consequence and recovery, were written explicitly instead of a single aggregate delay, and terminated projects were defined to cancel all future delivery events.
5. **Pathways.** Static interventions were rewritten as adaptive pathways with signposts and switches. PW6 (existing hardware programme) was added when the scope text of the existing signal-hardware line in the capital plan was found to allow new APS where poles and conduit are usable (SFMTA, 2026c), while the Prop L programme text refers only to replacement (SFCTA, 2023b).
6. **Design standards (PW5).** An early implementation assigned all corridor and fold-in crossings to signal projects in the first projection month, which made PW5 lead by construction. The design was revised so that APS is added only when a hardware-replacement event occurs at a candidate crossing (rate `lam_hw`), paid from a capped annual allowance (`b_hw`).
7. **Controls.** The "zero effect" control was redefined as "direct initiation effects zero" (the four direct terms set to 0, all processes unchanged), and it was stated that the comparison of PW3 with PW0 is the total-effect contrast.
8. **Removed elements.** Peer-city trajectories were removed as validation targets, because reproducing them would require generating output from court-ordered quotas and would pass by construction. Two switches without rules that read them, and one unused timing parameter, were removed.

### 4.4 Revisions after the design specification was fixed

1. **Hypothetical reallocation in PW1.** The final step of PW1 was designed on a reading of the capital-budget resolution under which up to 10% of the capital budget could be reallocated without board approval. Re-reading the resolution showed that 10% is the threshold above which cumulative technical or clerical corrections must return to the board (SFMTA Board of Directors, 2026), not a reallocation allowance. The rule was kept and is reported as a hypothetical fallback whose probability (`q_dir`) and amount (`a_line`) are assumptions; a subset of combinations that approximately disables it is reported (`docs/results.md` §4.6).
2. **Standing line in current practice.** The switch `sw_line`, which gives a combination a standing local line from the start, is sampled 0 or 1 in every pathway, including PW0. Since no standing local APS line exists today (SFCTA, 2023b), the main comparison uses `sw_line` = 0, and the other group is reported separately (`docs/experiment-protocol.md` §8.3).
3. **Asymmetric approval.** In the base design PW4 and PW5 receive a standing line without approval, whereas PW2 must pass a Prop L amendment. A variant was added in which their line passes the same approval chain (`docs/experiment-protocol.md` §9.3).

### 4.5 Adversarial search for omitted behaviour

To probe what the rules leave out, a red team of large-language-model runs (Anthropic Claude Sonnet) was asked, in five stakeholder roles and six situations, to propose decision behaviour missing from the model; a further LLM run per role–situation cell removed proposals already covered or unsupported by the cited evidence. LLMs were restricted to this role, and not used as simulated decision-makers, because the validity of LLM agents as stand-ins for human actors is not established (Larooij & Törnberg, 2025). None of the 146 retained proposals was incorporated into the model or used in any result; they are reported as hypotheses (`docs/results.md` §8). The themes most relevant to the conclusions are additional local funding routes (district-level Prop L funds, shifting curb-ramp costs) and mechanisms that would weaken a restored line (fault repairs displacing it).

### Limitations

- The rules are assembled by the author from documents and an interview. Different readings of the same documents could produce different rules; the reallocation fallback is an example of a reading that was later corrected.
- The pathways are proposed designs, not observed policies. The automatic line in PW5 and the line from the start in PW4 are specification choices; their influence is quantified by the approval variant.
- Pressure, ownership and enforcement act only on the start probability. Court orders, quotas, monitors, per-crossing deadlines, cost-sharing with the curb-ramp programme and district-level funds are not modelled (Section 7.5 and `docs/results.md` §8).
- Political processes (board decisions, supervisors' priorities) are represented only as probabilities.

## 5. Implementation verification

### 5.1 Implementation

The model core (`code/model.py`, `code/params.py`) uses the Python standard library and numpy only. Batch execution (`code/runner.py`), experiments (`code/experiments.py`), the approval variant (`code/e3_variant.py`) and secondary analyses (`code/posthoc.py`) use SALib, EMA Workbench, pandas and scikit-learn (versions in `environment/`). Each run draws from one random generator seeded by the replicate seed.

### 5.2 Assertions in the model code

The model raises an error if any of the following occurs during a run: a crossing is installed twice; a terminated project delivers an installation; a crossing funded locally is installed before its design is complete; an HSIP application, including contingency, exceeds the remaining agency ceiling; APS work in a set-aside application exceeds 20% of the project total or the set-aside total exceeds $400,000; a retained multi-crossing bundle has a benefit–cost ratio below 5.0. All experiments ran to completion, so none of these conditions occurred in any reported run.

### 5.3 Test suite

`python -I code/replay_check.py` runs the following tests and exits with an error if any fails:

1. **Event replay.** For every pathway and setting, five seeds, and both segments (projection from 2026-07 for 120 months; history from 2022-07 for 48 months), the initial states plus the recorded state changes must reproduce the stocks of states C, N, Fi, Fs and Fh (funded through HSIP) in every month.
2. **Installation reconciliation.** For every pathway in M-A and M-D, ten seeds: ten-year installations in the summary must equal the growth of cumulative installations.
3. **Rerouting.** PW4 must reroute a fold-in crossing whose parent project is delayed.
4. **Ceiling.** 800 runs with other SF HSIP requests of $5–9.9 million must never exceed the remaining ceiling.
5. **Dilution.** With one high-crash and one low-crash candidate, the bundle must either exclude the low-crash crossing or keep a benefit–cost ratio of at least 5.0.
6. **Red-flag boundary.** A flag cleared in the review month leaves the agency eligible; a flag cleared one month later does not.
7. **Influence area.** With signal-hardware countermeasures only and `f_aff` = 0.5, the benefit must be exactly half of that at `f_aff` = 1; with a pedestrian countermeasure added, more than half.
8. **Local road safety plan.** An expired plan makes the agency ineligible until a successful update.
9. **Local deadline.** Preparation finished in the deadline month is submitted; one month later it is missed.
10. **Set-aside.** 100 runs without violation of the 20% rule.
11. **Fractional capacity.** With capacity 0.5 per month and maximum staffing strain, installations still occur within ten years. This test was added after a defect was found and corrected before the freeze: the capacity account was capped at three months of capacity, which for capacities below 1/3 per month could never accumulate one installation; the cap is now max(3 × capacity, 1).
12. **Termination.** 1,050 runs (150 combinations × 7 pathways) in M-D, exercising overrun reversions, removals with refund of funds and partner-project delays; no terminated project delivers.

### 5.4 Reproducibility of execution

- Replicate seeds depend only on the master seed and a task label (`docs/experiment-protocol.md` §3).
- `python -I code/runner.py --selftest` runs 168 tasks × 3 replicates on one process and in parallel and requires byte-identical output.
- **E0.** The Markov baseline was re-implemented (`code/baseline.py`) and reproduces an earlier implementation within tolerance (median 20 in both; 10th–90th percentiles 13–28 and 13–27; `results/e0-baseline-check.json`).
- **Consistency of the variant switch.** `code/e3_variant.py --verify` rebuilds 108 E3 tasks with the approval switch off and requires their three stored outputs to equal the E3 output. The full rerun of the experiments is described in `docs/reproducibility.md`.

### 5.5 Independent reading of code against documentation

The code was read line by line against the design specification to write `docs/ODD+D.md`. Each difference between the design specification and the implementation was classified. Where the code was a deliberate simplification or the specification was out of date, the code's rule was adopted and `docs/ODD+D.md` describes it. Where the code failed to implement the intended rule, the difference was classified as a defect and corrected before the reported runs (Section 5.6).

### 5.6 Defects found during documentation and their correction

**Discovery.** The defects below were found while the code was read line by line against the design specification to write `docs/ODD+D.md` (Section 5.5). A difference was classified as a defect when the code did not implement the documented rule and the documented rule was the intended one. None had been detected by the tests in Section 5.3. All were corrected in `code/model.py` before the reported runs. No parameter was added, renamed or re-ranged.

**Table 1.** Implementation defects and their corrections. Line numbers refer to the distributed `code/model.py`.

| ID | Defect | Correction | Lines | Pathways affected |
|---|---|---|---|---|
| B1 | After a failed Prop L amendment, the month of the General Fund decision was computed as `t + (18 - t % 12) % 12 or 12`. Because addition binds more tightly than `or`, the clause `or 12` never applied, and a failure in July scheduled the decision for the same month. In PW6 and in the approval variant the check was then skipped (PW6 read the pathway node at the start of the step; the variant used an `elif` branch), so the request was never decided and PW6 never reached its HSIP repackaging step; in PW2 the decision came one year early. | The decision is taken in the next July strictly after the failure: `t + ((18 - t % 12) % 12 or 12)`. | 799, 860, 900 | PW2, PW6, approval variant |
| B2 | Crossings that cannot technically be equipped (settings M-C2, M-D) were excluded from local batches and crew installation but not from HSIP bundles or the set-aside, so a blocked crossing could be funded through HSIP and then installed by contract. | Blocked crossings are excluded from HSIP candidate bundles and from the set-aside. | 497, 563 | PW1, PW2, PW4, PW6 in M-C2 and M-D |
| B3 | When an HSIP project was removed at the five-year check, or its extension expired, all its crossings returned to candidate status, including crossings that needed a full signal upgrade. | Crossings return to the state they had before the award. | 752, 762 | Pathways that repackage HSIP applications |
| B4 | The probability `rho_flag` that another SF project carries a red flag was drawn once per application, so that applications reviewed in the same month could receive different eligibility decisions for the same agency. | One draw per review month, shared by all applications reviewed that month. | 614–616 | PW1, PW2, PW6 |
| B5 | Once any project passed five years without construction authorisation, the agency was ineligible in every later review, even after the project was authorised or terminated. | The agency is ineligible only while a project is past five years and not yet authorised; a terminated project stops counting from its termination month. | 619–623, 700 | PW1, PW2, PW4, PW6 |
| B6 | The first signpost of PW1 checked only whether any HSIP award had been made by May 2027, although the design also switches when the awarded bundle covers fewer than two crossings. | Switch to repackaging if there is no award or the awards cover fewer than two crossings; the May 2029 signpost checks for awards since the repackaging. | 656, 787, 791 | PW1 |
| B7 | When a committed HSIP application was not submitted (missed deadline, deflection or abandonment), the commitment was dropped instead of carried to the next cycle as the design requires. | The commitment moves to the next HSIP cycle with the same bundling mode. | 384–387 | PW1, PW2, PW4, PW6, approval variant |
| B8 | APS added under design standards was recorded as a funding award, although funding within five years is defined as a request-channel batch award. | Design-standard installations are recorded separately and do not enter funding within five years or recovery time. | 89, 930 | PW5 (funding within five years only) |
| B9 | One-time money (the hypothetical reallocation in PW1, an SG017 allocation in PW6) also released the current-practice local amount `a_local`, without a local application. | `a_local` is allocated only when staff submit a local application; one-time money is added on its own. | 392–401; one line each in PW1 and PW6 | PW1, PW6 |
| B10 | The denominator of the auxiliary output `high_priority_5y` included crossings that were not on the list during the five-year window. | The denominator counts high-priority crossings listed before month 60 and not installed before the projection start. | 1026–1028 | That output only; it is not reported |

**Design revision (P3).** One further change revises the design rather than correcting the code. Under the original design a committed HSIP application could start preparation only when the application window opened in July. With a rounded preparation time of five months or more it could never meet the November deadline, so that the first HSIP step of PW1 and PW4 never occurred in those combinations. The design was revised: a committed task may start up to ceil(`d_prep` + (m − 1)·`d_split`) months before the deadline, where m is the number of application instances in the committed mode (1 for the corridor bundle, 3 for repackaging), and otherwise starts in July as before (lines 361–366). Where that lead time is at most four months, behaviour is unchanged. No parameter was added; `d_split` now also sets the lead time.

**Checks of the corrections.** The corrected model passes every test of `code/replay_check.py`. Each correction was also checked with a single run at fixed parameters: PW6 and the PW4 variant decide the General Fund request in the following July (B1); no blocked crossing enters an HSIP bundle when all candidates are blocked (B2); a long preparation starts before July and meets the November deadline (P3); design-standard installations no longer count as funding (B8); an SG017 allocation releases only the one-time amount (B9). These single-run checks used one-off scripts that are not distributed. Because the corrections act only in the projection segment, the historical segment is unchanged: for 30 combinations in each of the six settings, the corrected and uncorrected code produce identical stocks, snapshots and event streams over the 48 historical months.

**Random numbers.** B2, B4, B7 and P3 change the number or order of random draws in the projection. Within a parameter combination, pathways therefore share the random stream only up to the first such draw (`docs/experiment-protocol.md` §3).

### Limitations

- The tests are scenario tests and assertions, not a unit-test suite with coverage measurement. Most run at default parameter values; the ceiling, set-aside and termination tests use sampled parameters.
- The defects in Section 5.6 were not caught by any test; B1, for example, required a Prop L failure decided in July, which no test exercised. They were found by reading the code against its documentation. Tests that fix the month of each scheduled event, and tests per documented rule, would have caught most of them.
- The 1,848-run identity comparison used a one-off script that is not distributed; the two compared files are distributed.
- The model core was written to run also in a browser (Pyodide). This has not been verified for the distributed version.

## 6. Model output verification

Model output verification asks whether the model, with its parameters, reproduces observed patterns that were not built into its rules. Here it is the historical screening E1 and the retrospective check H1 (`docs/experiment-protocol.md` §5.2; results in `docs/results.md` §3).

### 6.1 Screening against the request lists

Under the base priors, 15.4–26.2% of 2,000 combinations per setting reproduce all five stocks at all five screening snapshots within the tolerances, and 64.7–69.1% of accepted combinations also reproduce the three later snapshots (`docs/results.md`, Table 2). The binding pattern is the drain of the funded agency-crew stock from 22 to 1 with no new batch: only 381–630 of 2,000 combinations per setting meet the Fi tolerance, against 1,467–2,000 for the other stocks (Table 3). Any setting that stops new local funding batches reproduces it.

### 6.2 Robustness of the screening

- **Exhaustion date.** Acceptance changes by at most 1.8 percentage points (M-A, from 24.9% to 23.1%) across five assumed exhaustion dates of the earlier dedicated programme (`docs/results.md`, Table 4).
- **Prior width.** Narrow priors give acceptance of 24.3–26.6% and H1 pass rates of 89.6–91.2%; wide priors give 5.1–8.1% and 44.3–49.5% (`docs/results.md`, Table 5). The ordering of settings is not stable across widths: M-B2 has the lowest acceptance under base and wide priors but the highest under narrow priors.
- **Double use of the installation records.** With independent wide priors for `h_in` and `h_fs`, acceptance falls to 7.8–12.5% and the H1 pass rate to 46.0–56.5%; M-B2 again has the lowest acceptance (Table 5).
- **Constraint on parameters.** The 10th–90th percentiles of accepted combinations cover most of each prior range (`docs/results.md`, Table 6). The screening is a weak filter, not a calibration.

### 6.3 Use of the screened combinations

Projection runs resample the historically active parameters as whole accepted combinations, preserving their joint constraints (`docs/experiment-protocol.md` §5.3). The screening induces one strong correlation that matters for interpretation: crew capacity `k0` and the agency-crew installation rate `h_in` are correlated at −0.704 among accepted combinations, because the lists constrain only their joint output (`docs/results.md` §5).

### Limitations

- Tolerances were set by judgement, and the criterion applies to the replicate mean, not to the distribution of replicates.
- The retrospective snapshots were not used for estimation or screening, but their shape was known when the rules were designed; H1 is therefore not independent validation.
- The patterns are stocks, not flows; two different flow histories can produce the same stocks.
- Independent validation requires data published after the freeze: the next SFMTA request list, whether the agency's APS capital project restarts, and whether an SF application containing APS appears in the HSIP Cycle 13 award list. None is available yet.

## 7. Model analysis

### 7.1 Design of the analysis

Five experiments were specified in the protocol (`docs/experiment-protocol.md`): E0 (code check), E1 (screening), E2 (scenario discovery with PRIM, cross-checked with classification and regression trees, CART; Friedman & Fisher, 1999; Bryant & Lempert, 2010; Breiman et al., 1984/2017; Kwakkel, 2017), E3 (pathway comparison with common random numbers) and E4 (Morris screening followed by Sobol analysis; Morris, 1991; Sobol′, 2001; Saltelli et al., 2010; Herman & Usher, 2017). Latin hypercube sampling (McKay et al., 1979) covers the projection-only parameters. Every combination runs 20 replicates.

### 7.2 Pathway comparison (E3)

In the main comparison (no standing local line at the start), PW5 and PW4 under the base design outperform current practice in 92.4–97.3% of combinations, PW6 in 91.5–95.0%, PW1 in 89.4–95.0%, PW2 in 87.4–92.1%, and PW3, lowest in every setting, in 66.9–88.6% (`docs/results.md`, Tables 7–9). Under the approval variant, PW4 and PW5 outperform current practice in 91.2–95.2% of combinations, while their funding within five years falls to 51.3–66.5% (PW4) and 46.9–63.1% (PW5); the line received without approval accounts for a substantial part, but not all, of their advantage (`docs/results.md` §4.2). Setting the direct initiation effects to zero reduces PW3 from 66.9–88.6% to 44.5–80.5%. Because the measure counts only strict improvements in mean installations, a pathway with no systematic effect but a divergent random stream would score just below 50%; shares are read against that reference (`docs/results.md` §1). The output pooled over both values of `sw_line`, the `sw_line` = 1 group and the PW1 subset without the hypothetical reallocation are reported for comparison (`docs/results.md` §§4.3–4.6).

### 7.3 Scenario discovery (E2)

The primary PRIM boxes have test density 0.939–0.995, and CART reaches test accuracy 0.748–0.966 (`docs/results.md`, Table 18); the base rate of success is not stored, so these values cannot be compared with it. The rule lists stored by `prim_all` are defective (`docs/experiment-protocol.md` §8.2). Corrected rules, re-fitted as a secondary analysis, require a standing local line and an APS share of at least about 4–9% of it for PW0–PW3, and an APS share of at least about 5–13% for PW4–PW6; the size of the line does not enter any box (`docs/results.md` §6.2).

### 7.4 Sensitivity analysis (E4)

[Pending: Morris overlap and list, leading Sobol indices and their sums, and the fixed-background check, from `results/e4-sensitivity/`.]

### 7.5 Channels for accountability, pressure and capacity

Pressure, ownership, deadlines, oversight, enforcement and crew capacity are not among the leading twelve in Morris screening (`docs/results.md`, Table 20), and marginal splits of the E3 runs show no trend in pressure (`docs/results.md`, Tables 15–16). These results describe the model structure: these factors act only on the monthly probability of starting an application, or as a monthly ceiling, and supply no money. Mechanisms through which they act elsewhere, such as court-ordered quotas and funds, per-crossing deadlines or a monitor, are not modelled.

### 7.6 Secondary analyses

The main comparison restricted to `sw_line` = 0, the `q_dir` < 0.08 subset, the one-parameter splits and correlations, the corrected PRIM rules and the approval variant are secondary analyses (`docs/experiment-protocol.md` §§8.3, 9.3). The reasons for each are given in Section 4.4.

### Limitations

- E4 samples the full priors without screening, whereas E3 uses screened combinations; the two agree only in direction.
- E4b is conditional on 86 parameters fixed at their defaults; the fixed-background check covered four cells and only the leading parameter.
- The corrected PRIM boxes were re-fitted on a different candidate set from the primary boxes and are not identical to them. PRIM was not run for the approval variant.
- The convergence check with R = 40 and moment-independent indices on the screened sample, described in the design specification, were not performed.
- With 461–528 combinations per setting, differences of a few percentage points between pathways are within sampling error; results are read as tiers.
- Common random numbers make pathway results within a setting dependent samples.

## 8. Model output corroboration

Model output corroboration compares model outputs with independent evidence that was used neither to build the rules nor to screen parameters. Evidence was classified accordingly before the freeze: evidence that defines rules (for example the 2024 hiring slowdown, which defines the start of M-B1) cannot also support them, and screening data cannot corroborate the screening result. Only the third class, evidence used for neither, is used here. All comparisons are directional.

### 8.1 Staffing

The agency's traffic-signal electrician classification (9145) has 21 budgeted positions in each fiscal year from 2023–24 to 2027–28 (20.58 in 2022–23) (CCSF, 2022, 2024, 2026), and the eligible list for the classification grew from 7 (2022) to 25 (2023) to 41 candidates (May 2025) (SF DHR, 2022, 2023, 2025). This evidence weighs against a strong version of the staffing explanation in which the agency could not hire. In E1 the setting with an early staffing constraint (M-B2) has the lowest acceptance under base priors, and its accepted combinations require a smaller capacity reduction than other settings (median `phi` 0.304 against 0.444–0.464; `docs/results.md`, Tables 2 and 6). The two are directionally consistent. Neither shows that staffing played no role, and the ordering of M-B2 reverses under narrow priors (Section 6.2).

### 8.2 Capacity to apply

In HSIP Cycle 12, the agency submitted an application in the same window in which no APS application was made (Caltrans, 2024a). This weighs against an explanation in which the agency lacked the capacity to prepare HSIP applications at all, and is consistent with the model's representation of the stall as an unowned application step rather than an inability to apply.

### 8.3 Installation capacity

A 2010 press release reported 116 APS installations over the preceding two and a half years, about 46 per year (SFMTA, 2010). The scope differs from the post-2010 request channel, so the comparison is qualitative: it weighs against an explanation in which the crews could never install quickly, and is consistent with the E4 result that crew capacity is not among the influential inputs when funding is the binding constraint.

### 8.4 Peer cities

New York and Chicago increased installation rates under court orders that set quotas, appointed monitors and named officials responsible for seeking funds (S.D.N.Y., 2021, 2022; N.D. Ill., 2025). The model contains no such mechanism, so these cases cannot corroborate its outputs. They are compatible with the model's main condition for funding, a standing source of money with a share reserved for APS, but the effect of the orders cannot be separated from other changes in those cities.

### Limitations

- All corroboration is qualitative and directional; no corroborating quantity is predicted by the model in the same units.
- The independent evidence bears on the explanations of the stall (question 1), which the model does not adjudicate, more than on the pathway comparison (question 3), for which no independent evidence exists yet.
- The pathway comparison can be corroborated only by future events: whether a standing local line with an APS share is created, and what follows.
