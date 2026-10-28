# Actors and Evidence

## 1. Purpose and scope

This document records, for every actor, relationship and institutional rule in the model, the public document or data set on which it rests, and how the model uses it. It serves the "theoretical and empirical background" element of ODD+D (Müller et al., 2013) and the data-provenance items of STRESS-ABS (Monks et al., 2019). The ODD+D description states what the model does; this document states why each element takes the form it does and how firmly the evidence supports it.

The model covers the request channel for accessible pedestrian signals (APS) in San Francisco: the 76 requested intersections pending on 30 June 2026 and later requests, and the steps by which a request may obtain funding and be installed. Citywide APS coverage, signals outside the request list and the condition of installed devices are outside the model (Section 6).

Code is cited as `code/model.py` or `code/params.py` with the function or parameter name. Sources are cited author–date; full entries and the in-text forms are in `docs/references.md`. Page (p.), question (Q), slide and line (l.) locators refer to the cited public document.

## 2. Evidence types and confidence

Each claim in Section 4 carries one evidence type:

| Type | Meaning |
|---|---|
| Document | The rule, value or event is stated in a public document. Simple arithmetic on stated numbers (sums, ratios) is still "document" and is marked "computed". |
| Data | The value is computed from a public data set (request-list snapshots, crash records, signal inventory, project lists). |
| Interview | The author's interview with SFMTA staff (personal communication, 2026). Used in two places: the SI02 carrier switch (E42), reported in both positions, and the deflection pattern (E54), which informs sampled ranges. Never used as a point value. |
| Inference | An interpretation or assumption not stated in any document. Inferences enter the model only as sampled ranges or switches whose consequences are tested in the sensitivity analysis. |

Confidence is graded High (a rule or number stated in a primary document that governs the actor), Medium (a primary document supports the claim but with ambiguity, a small sample, or an indirect link to the model element), or Low (inference, a single statement, or evidence of absence within a bounded search).

"Used in model as" takes one of: **rule** (fixed logic in the code), **parameter** (sets the range or default of a sampled parameter in `code/params.py`), **initial value** (sets the state at the start of a run), **calibration target** (used only to screen parameter combinations against history), **switch** (a 0/1 parameter tested in both positions), or **not used** (context only; see Section 5).

## 3. Actors

The model contains one decision-making agent (capital-budget and grant staff), three rule-following actors that act each month (APS engineering, the Signal Shop, advocates), one exogenous process (external enforcement), and several funding venues represented as rule engines rather than agents. Actor codes in parentheses are those written to the event log by `Sim.ev` in `code/model.py`.

### 3.1 Residents requesting APS (C3)

- **Role.** Submit requests for APS at specific intersections.
- **Resources.** Knowledge of where crossings are difficult. A request adds a fixed six points to an intersection's priority score, independent of the number of requesters (SFMTA, 2007, p. 5; SFMTA, 2022a, pp. 1–2). Requests are made through 311, the web or by letter, and SFMTA commits to reply within 90 days with the score, relative priority and whether installation is likely within three years (SFMTA, 2022a, p. 2).
- **Interacts with.** APS engineering staff, who score and classify requests.
- **In the model.** New requests arrive as a Poisson count with monthly mean `lam_arr`/12 (`Sim._arrivals`), `lam_arr` ∈ [6, 17] per year, the range of intersections first appearing on the request list in each calendar year 2021–2026 (SFMTA, 2020–2026). In the historical segment the 41 observed arrivals between July 2022 and June 2026 are replayed at their snapshot months. Requesters take no further action in the model; a formal role for requesters in review is a reform proposal without a numerical effect and is not modelled.

### 3.2 SFMTA APS engineering staff (A1)

- **Role.** Score requests and classify each intersection as an in-house candidate (C), needing major funding for poles, conduit or full rebuild (N), funded for in-house installation (Fi), or funded through a signal project (Fs).
- **Resources.** The request list, the scoring worksheets and engineering records. Scoring uses crosswalk and intersection tables derived from the NCHRP 3-62 method and contains no cost or feasibility term (SFMTA, 2007, pp. 2–5). SFMTA policy installs APS at all new signals and major signal upgrades, "most cost effective" when combined with existing work (SFMTA, 2023, p. 6; SFMTA, 2026a, p. 7).
- **Interacts with.** Residents (receives requests); capital-budget and grant staff (supplies the list that "will be used to apply for funding", SFMTA, 2022a, p. 2); advocates and the Mayor's Disability Council (semiannual and occasional reports).
- **In the model.** A rule, not a decision. Each new request is assigned C, Fs or N with probabilities 32/41, 6/41 and 3/41, the observed split of the 41 new entries from July 2022 to June 2026 (`Sim._arrivals`; SFMTA, 2020–2026). Rank (high, medium, low) is copied from a randomly drawn pending intersection.

### 3.3 SFMTA capital-budget and grant staff (A2): the decision-making agent

- **Role.** Decide, for each funding venue and window, whether to start preparing an APS funding application; prepare it; submit it at the venue deadline.
- **Resources.** Applicant status: SFMTA is the only eligible sponsor of the Prop L Traffic Signs and Signals Maintenance programme (SFCTA, 2023b, p. 5) and the applicant for HSIP. A City precedent shows an HSIP application submitted by department staff and the resulting grant accepted retroactively by the Board of Supervisors (San Francisco Board of Supervisors, 2013, pp. 1–2); the model therefore treats the decision to apply as a staff decision (inference). Internal budget authority under the capital budget.
- **Constraints.** The policy clock (installation within 1.5 years in-house, 3 years by contract) starts only after funding is obtained; no document assigns an owner or a deadline for turning the request list into an application (SFMTA, 2022a, pp. 2–3). Capital revenue fell short of approved projects, and grant rules favour expansion over maintenance (SFMTA, 2026d, pp. 5, 11, 20).
- **Interacts with.** APS engineering (receives the list); funding venues (submits); advocates (receives pressure, responds); the Signal Shop (passes funded work); external enforcement (receives escalation).
- **In the model.** The monthly probability of starting preparation in an open window is logistic in owner, deadline, oversight, pressure and enforcement, reduced by staff strain and cost pressure (`Sim.p_start`). In the unassigned-responsibility settings (M-A, M-D) a pressure event is deflected with probability `p_deflect` ("cost / no money" response), which blocks restarts for `r_back` months (`Sim.step`). An owner can leave (`lam_quit`), leaving the post vacant for `t_vac` months and dropping preparation with probability `q_drop`. Preparation takes `d_prep` months; an application not ready at the deadline misses the window (`Sim._task_step`). Applications that a pathway commits to a given HSIP cycle start without the probabilistic decision, early enough for all their instances to be ready by the deadline (ceil(`d_prep` + (m − 1)·`d_split`) months before it, m = 1 for the SG015 bundle and 3 for a repackaged submission, and not later than July); a committed cycle that is not submitted carries over to the next cycle with the same bundle mode. The decision rule itself is not stated in any document; its form follows the garbage-can and buck-passing literature (Cohen et al., 1972; Fioretti & Lomi, 2010), and all coefficients are sampled ranges.

### 3.4 Signal Shop crews (A3)

- **Role.** Install APS at funded in-house sites and at sites reached by the design-standards rule.
- **Resources.** The traffic signal electrician class (9145) has 21 budgeted positions in each fiscal year from 2023–24 to 2027–28 (20.58 in 2022–23), 13 in the operating fund and 8 in project support, the latter expected to be recovered from capital projects (CCSF, 2022, pp. 26–27; CCSF, 2024; CCSF, 2026, pp. 122–123). Eligible lists for the class held 7 (2022), 25 (2023) and 41 (May 2025) candidates (SF DHR, 2022, 2023, 2025). Actual staffing on duty is not published.
- **Constraints.** SFCTA wrote in 2023 that Signal Shop staffing "is often the limiting factor" on delivery (SFCTA, 2023b, p. 9). SFMTA slowed hiring from July 2024 and froze non-essential hiring from October 2024 (SFMTA, 2025). Maintenance at 220 intersections was deferred in 2024 (SFMTA, 2024c, pp. 19, 22).
- **In the model.** A monthly capacity `k0` accumulates in a bank capped at three months of capacity; each funded in-house site leaves the queue with monthly hazard from `h_in` if capacity is available (`Sim._deliver`). In the staffing settings (M-B1, M-B2, M-D), capacity is reduced by `phi`·strain, where strain ramps from 0 to 1 over `strain_ramp` months from July 2024 (M-B1) or January 2023 (M-B2) and ends `strain_end` months after December 2026 (`Sim.strain`).

### 3.5 Advocacy groups, with the Mayor's Disability Council as a channel (C2; MDC)

- **Role.** Generate pressure on SFMTA to act on requests.
- **Resources.** Information, public legitimacy and the possibility of disability-law claims; no budget authority. The 2007 structured-negotiation agreement obliged SFMTA to seek funding from federal, state and local sources, to involve the claimant organisations in Prop K funding requests and to meet them twice a year (CCSF et al., 2007, §§ IV.A.1, IV.J.1–2). Semiannual reports continue (SFMTA, 2023, slide 10; SFMTA, 2026a, p. 11); they had lapsed and resumed in July 2022 after LightHouse raised them (Albers, 2022). The Mayor's Disability Council can pass resolutions, hold hearings and send letters of support; it urged APS at 25% of signalised intersections by 2010 (MDC, 2006), a target not reached (116 intersections equipped by March 2010, SFMTA, 2010).
- **Constraints.** The agreement expired on 30 June 2010 and provided only negotiated dispute resolution (CCSF et al., 2007, §§ VI–VII). At the July 2026 Council meeting the APS item was an information report with no public comment (MDC, 2026). An APS item at the SFMTA Board's Policy and Governance Committee in September 2018 drew public comment but no action (SFMTA, 2018b, p. 2).
- **In the model.** Pressure events occur at rate `lam_press` ∈ [0, 0.5] per year, interrupted by quiet spells (rate `lam_quiet`, length `t_quiet`). Each event that is not deflected adds a term exp(−Δt/`k_decay`) to pressure, which enters only the start probability of A2 (`Sim.pressure`, `Sim.p_start`). The accountability-first pathway doubles `lam_press` (`Sim._accountability_on`).

### 3.6 External enforcement (D1)

- **Role.** The possibility that negotiation, litigation or a court order raises the cost of not applying.
- **Resources.** Court orders elsewhere require cities to "pursue all funding sources" and to name an implementation lead and a funding lead (S.D.N.Y., 2022, p. 9; N.D. Ill., 2025, pp. 9–11). Liability in both cases was found at coverage of 5% or less, and the courts set no coverage threshold (S.D.N.Y., 2020, pp. 25–27; N.D. Ill., 2023, pp. 16–25). San Francisco's coverage was 611 of 1,305 signals in July 2026 (SFMTA, 2026a, p. 3).
- **Constraints.** No APS suit or settlement against San Francisco after 2010 was found. The 2023 public right-of-way guidelines require APS at new and altered pedestrian signals but bind cities only once adopted by the Department of Justice, which had not occurred for signals (Architectural and Transportation Barriers Compliance Board, 2023, pp. 53604, 53653).
- **In the model.** An ordinal level from 0 (none) to 4 (court order), starting at 1 ("credibility unknown"). The level steps up with annual probability `eps_enf` ∈ [0, 0.1], a pure assumption; the accountability-first pathway sets it to 2 (structured negotiation) and then 3 (suit) after idle periods (`Sim._pathway_signposts`). The level enters only the start probability through `b_enf`·max(0, level − 1). Enforcement supplies no money and no installation quota in the model.

### 3.7 Caltrans and the Highway Safety Improvement Program (CT)

- **Role.** Run the biennial HSIP call, review eligibility, approve awards and enforce delivery milestones.
- **Rules used.** APS-only projects are ineligible in every category and APS must form part of a broader safety improvement (Caltrans, 2026d, Q3). Benefit–cost (BCR) applications need a BCR of at least 5.0, and an agency may receive at most $10 million (Caltrans, 2026c, p. 4; Caltrans, 2026d, Q60–61). Each application may combine at most three countermeasure types per category (Caltrans, 2026d, Q28–29). Reimbursement is 90% (Caltrans, 2026d, Q14, Q59). The pedestrian-crossing set-aside caps each agency at $360,000, one application per set-aside, with other work at no more than 20% of project cost (Caltrans, 2026c, pp. 4–6). Delivery requires the preliminary-engineering milestone within 9 months and construction authorisation within 36 months (42 with consultant design), with projects not under construction after five years removed (Caltrans, 2021a, p. 8; Caltrans, 2026f, slide 23). Agencies need a local road safety plan updated or confirmed within five years (Caltrans, 2026c, p. 1; Caltrans, 2026d, Q45–54). Force-account work on federal-aid projects needs a public interest finding (Caltrans, 2026e, pp. 7–8). Crash-reduction factors, service lives and crash costs come from the Local Roadway Safety Manual (Caltrans, 2026g, Table 1 p. 31, pp. 46, 56, 58, Appendix D).
- **In the model.** A rule engine (`Sim._build_app`, `Sim._submit_hsip`, `Sim._setaside`, `Sim._hsip_events`, `Sim._new_project`, `Sim._project_step`). Section 4.4 lists each rule.

### 3.8 San Francisco County Transportation Authority (SFCTA) and Prop L

- **Role.** Program and allocate Prop L sales-tax funds; its Board approves five-year prioritisation programmes (5YPPs), amendments and allocations.
- **Rules used.** The Traffic Signs and Signals Maintenance programme covers maintaining and upgrading signals "including for pedestrians", with SFMTA as sole sponsor (SFCTA, 2022, p. 11; SFCTA, 2023b, p. 5). The FY2024–28 5YPP contains no APS installation line (SFCTA, 2023b, p. 14). Allocations are made only on applications prepared by eligible sponsors (SFCTA, 2025a, p. 22). The next strategic plan and 5YPP cycle starts in autumn 2027 (SFCTA, 2025a, pp. 8, 46). A district-level precedent: after November 2024, SFMTA requested and SFCTA approved on 25 February 2025 Neighbourhood Transportation Program funds for new signals whose scope includes APS (SFCTA, 2025c, pp. 15, 18).
- **In the model.** A rule engine. A Prop L amendment is rejected with probability `q_veto` or deferred by `t_defer` months after a fixed three-month lag (`Sim._propl_amendment`); when a standing local line is on, SFCTA is the payer of local batches (`Sim._local_decision`).

### 3.9 SFMTA Board of Directors

- **Role.** Approves the capital improvement programme, the capital budget and changes to the APS policy.
- **Rules.** The Director may make technical or clerical corrections and allocate new or discretionary revenue; cumulative corrections above 10% of the capital budget return to the Board (SFMTA Board of Directors, 2026, resolution text). Policy changes need at least 60 days' written notice to the claimant organisations and Board approval (SFMTA, 2022a, p. 3).
- **In the model.** Not an agent. The 10% figure is a threshold for Board review, not an allowance, and no document states that any amount would be reallocated to APS; the federal-safety-grant-first pathway's final fallback (`q_dir`, a probability that a one-time reallocation equal to `a_line` is made, `Sim._pathway_signposts`) is therefore a hypothetical assumption. Automatic Board review after repeated non-submission is a reform proposal and is not modelled.

### 3.10 Other funding venues

- **General Fund and capital budget (GF).** The only General Fund APS amounts in recent plans are estimates ($292,817 in FY2028 in SFMTA, 2024b; $570,000 in FY2031 in SFMTA, 2026c). In the model a local request is decided at the July budget (`Sim._local_decision`), with the status-quo amount `a_local` ∈ [$0, $570,000] per year.
- **Signal projects (PARENT).** APS installed with funded signal projects follows SFMTA's new-signal rule. Fs sites install with monthly hazard from `h_fs`; fold-in sites wait for the parent project's nominal finish (`Sim._deliver`, `Sim._init_sites`).
- **SS4A and ATP.** Recorded as context; the model does not simulate new applications to these programmes (Section 5).

### 3.11 Relationships

| From → to | Relationship | Evidence | In the model |
|---|---|---|---|
| Residents → APS engineering | Request; reply within 90 days | SFMTA (2022a, p. 2) | `Sim._arrivals` |
| APS engineering → capital-budget staff | List "will be used to apply for funding"; no owner or deadline | SFMTA (2022a, p. 2) | Owner indicator 0 in M-A/M-D (`Sim.owner`) |
| Capital-budget staff → HSIP, Prop L, General Fund | Application; the link with no assigned responsibility | SFMTA (2022a); Caltrans (2024a); SFCTA (2023b, p. 14) | `Sim._task_step` |
| Funding venues → capital-budget staff | Review, approval, allocation | Caltrans (2026c, 2026d); SFCTA (2025a, p. 22) | `Sim._hsip_events`, `Sim._local_decision` |
| Capital-budget staff → Signal Shop | Funded in-house work | SFMTA (2022a, p. 2); SFMTA (2026c), SG142 scope | `Sim._deliver` |
| Signal projects → intersections | APS with new or upgraded signals, without an application | SFMTA (2023, p. 6; 2026a, p. 7) | `Sim._deliver` (Fs) |
| Advocates → SFMTA | Pressure; semiannual meetings | CCSF et al. (2007, § IV.J.1); Albers (2022) | `Sim.step`, `Sim.pressure` |
| SFMTA → advocates and Council | Reports; "cost / no funding" responses | SFMTA (2026a, pp. 4–6, 8); SFMTA staff, personal communication, 2026 | `p_deflect` |
| External enforcement → capital-budget staff | Escalation raises start probability | S.D.N.Y. (2022); N.D. Ill. (2025) | `b_enf`, `eps_enf` |

Power dependence is asymmetric: advocates depend on SFMTA to apply, while SFMTA does not depend on advocates' approval (Bevir, 2009, p. 158). This motivates modelling advocacy as pressure on one probability rather than as a veto or a resource.

## 4. Evidence table

Columns: **ID**; **Claim**; **Source** (author–date, locator); **Type**; **Used in model as** (code element); **Confidence and caveat**.

### 4.1 Request list and initial state

| ID | Claim | Source | Type | Used in model as | Confidence and caveat |
|---|---|---|---|---|---|
| E01 | On 30 June 2026, 76 requested intersections were pending: 35 C, 21 Fs, 18 N, 2 Fi. | SFMTA (2020–2026), snapshot 2026-06-30 | Data | Initial value: `inputs.json` `pending76`; `Sim._init_sites` | High. Status codes are SFMTA's own classifications. |
| E02 | Stocks at nine snapshots, July 2022 – June 2026: e.g. Fi 22 → 1 between July 2022 and August 2024; C 8 → 35; cumulative installed from requests 30 → 69. | SFMTA (2020–2026) | Data | Calibration target: `inputs.json` `history.observed_stocks` | High for counts. Snapshot dates are list publication dates, not installation dates. |
| E03 | In-house installations from the request list were 4, 5, 11 and 3 in the four intervals to August 2024 (23 in total), then zero in the next four intervals. | SFMTA (2020–2026), computed | Data | Calibration target; motivates the batch-funding representation (`Sim._local_decision`) and `h_in` | High for counts. Installations outside the request list are not attributed. |
| E04 | Funded in-house sites installed at 0.96 per site-year before August 2024 (23 events in 289 site-months; 95% interval 0.61–1.44); no estimate is possible afterwards (Fi nearly empty). | SFMTA (2020–2026), computed | Data | Parameter: `h_in` ∈ [0.59, 1.41] per year | Medium. Rate is identified only before the funding break. |
| E05 | Sites funded through signal projects installed at about 0.20 per site-year both before and after August 2024 (95% intervals 0.09–0.38 and 0.08–0.42). | SFMTA (2020–2026), computed | Data | Parameter: `h_fs` ∈ [0.08, 0.31] per year | Medium. Direction of change cannot be determined. |
| E06 | Moves from C to funded in-house were 2 events in 316 site-months before August 2024 and 1 in 669 after; intervals overlap. | SFMTA (2020–2026), computed | Data | Not used as a rate; funding is modelled as discrete batch events | Medium. Too few events to estimate a stationary rate. |
| E07 | Of 41 intersections entering the list from July 2022 to June 2026, 32 entered as C, 6 as Fs and 3 as N. | SFMTA (2020–2026), computed | Data | Rule: classification probabilities in `Sim._arrivals` | High. |
| E08 | Intersections first appearing on the list per year: 16 (2021), 8 (2022), 6 (2023), 17 (2024), 9 (2025), 9 (to June 2026). | SFMTA (2020–2026), computed | Data | Parameter: `lam_arr` ∈ [6, 17] | Medium. First appearance on the list, not submission date. |
| E09 | Ten pending intersections lack pedestrian heads on some or all phases (all ten are N); the remaining 66 cannot be checked for countdown heads, and leading pedestrian intervals (LPI) cannot be checked at any of the 76. | SFMTA (2024d), field PED_SIGNAL; SFMTA (n.d.-c) | Data | Initial value: `missing_ped_heads`; parameters `s_cd`, `s_lpi` for unknown sites | Medium. Timing cards are available only by public-records request (SFMTA, n.d.-c). |
| E10 | Crash counts within 50 m of each pending intersection, by pedestrian/bicycle involvement and severity, for 2021–2025 and 2023–2025; 75 of 76 intersections matched. Property-damage-only crashes are absent from the data set. | CCSF (n.d.) | Data | Initial value: `inputs.json` `crashes`; `y_win`; `crash_impute` for the unmatched site | Medium. Absent property-damage crashes understate benefits; 50 m circles can overlap. |
| E11 | Of 38 pending intersections with signal inventory diagrams, 22 still show 8-inch heads; in the C group, 7 of 15. | SFMTA (n.d.-c), sample | Data | Parameter: `s_12in_C` ∈ [0.25, 0.7] | Low to medium. Small sample; diagrams may not match field conditions. |
| E12 | SFMTA reported that "nearly all" of 1,292 signals have countdown heads and 81% have an LPI at one or more crosswalks or no conflicts. | SFMTA (2024a) | Document | Parameter: `s_cd` ∈ [0, 0.2]; `s_lpi` ∈ [0, 0.5] | Low for site-level use. Citywide statement; "one or more crosswalks" does not imply every crossing. |

### 4.2 Fold-in sites and parent projects

| ID | Claim | Source | Type | Used in model as | Confidence and caveat |
|---|---|---|---|---|---|
| E13 | Eleven pending intersections were matched to an existing project. Execution status: 6th Ave/Irving in Contract 35 with APS in scope (yes); Eddy/Fillmore and Golden Gate/Larkin in SS4A signal projects (likely); three 13th Street intersections and Ellis/Powell (unverified); 5th/Mission (parent construction unfunded); Harrison/Main, Jones/Market/McAllister and Stockton/Sutter (parent signal work already complete). | SFMTA (n.d.-a, n.d.-b, n.d.-d, n.d.-e); SF Public Works (n.d.); SFMTA (n.d.-c) | Document | Initial value: `fold` in `inputs.json`; `pi_scope` for likely/unverified; `done3_real` switch for the three completed parents | Medium. Intersection-level scope is not listed on every project page. |
| E14 | Parent finish dates: Contract 35 construction autumn 2026 – winter 2027/28; Western Addition Community Safe Streets spring 2027 – autumn 2028; 13th Street "winter 2027"; Powell Street spring 2026. | SFMTA (n.d.-a, n.d.-e, n.d.-b); SF Public Works (n.d.) | Document | Initial value: `parent_finish` (2028-02, 2028-10, 2027-12, 2026-06) | Medium. Nominal dates; delays are sampled as `t_parent`. For Golden Gate/Larkin the code assumes a finish 18 months after the start; the Tenderloin project page gives construction from spring 2027 to summer 2029 (SFMTA, n.d.-d). The site starts as Fi, so the assumed date affects no rule in the frozen design. |
| E15 | Five Fs sites have no parent project found in public capital plans or project pages. | SFMTA (2026c); project pages as in E13 | Document (absence) | Switch: `fs5_parent` | Low. Absence within a bounded search. |
| E16 | Stockton/Sutter: a new signal entered service on 2 May 2025 and its equipment schedule shows no APS, while the request remains pending. | SFMTA (n.d.-c) | Document | Included in `done3_real` scenarios | Medium. A single case; installation logs were not available. |

### 4.3 Costs

| ID | Claim | Source | Type | Used in model as | Confidence and caveat |
|---|---|---|---|---|---|
| E17 | Minimum APS cost about $40,000 per intersection; upper bound $1.5 million; damaged conduit about $200,000 and new curb ramps about $200,000, each where needed. | SFMTA (2026a, pp. 4–5) | Document | Parameters: `q_pipe`, `q_ramp` (each adds $200,000, `Sim._site`); cap of $1.5 million on realised cost (`Sim._overruns`); upper end of `u0` | High for the stated amounts; the probabilities that conduit or ramp work is needed are not stated and are sampled over [0, 1]. |
| E18 | SG142 plans about 22 intersections without excavation for $488,144, all by the Signal Shop (about $22,000 per intersection). | SFMTA (2026c), SG142 | Document, computed | Parameter: lower end of `u0` ∈ [$22,000, $50,000] | Medium. Conflicts by a factor of two with E17's $40,000 minimum; the conflict is kept as a range. |
| E19 | The minimum cost rose from $20,000 (2018) to $30,000 (2023) and $40,000 (2026). | SFMTA (2018a, slide 6); SFMTA (2023, pp. 4–5); SFMTA (2026a, pp. 4–5) | Document | Rule: cost pressure = (unit cost − $20,000)/$20,000 (`Sim.costpress`); parameter `g_cost` ∈ [0, 0.15] | Medium. Growth rate of 9–10% a year is computed from three points. |
| E20 | The FY2024 SG015 visibility project budgeted $400,000 for 8 intersections receiving 12-inch heads and 20 receiving backplates, about $14,000 per intersection. | SFCTA (2023b, pp. 84–87) | Document, computed | Parameters: `c_12in` ∈ [$8,000, $20,000]; `c_bp` ∈ [$2,000, $8,000] | Medium for the total; the split between heads and backplates is an assumption. |
| E21 | Contract 35 (17 locations, APS included): Prop L construction request $5,345,363; total project cost $18,213,383. | SFCTA (2025b, pp. 3, 26–27) | Document | Parameter: `c_full` ∈ [$200,000, $600,000] per full-upgrade site | Low. Per-location amounts are about $0.31 million (Prop L share) and $1.07 million (all phases); the sampled range is an assumption between them. Design documentation differed: it gave about $554,000 per location as the upper end, a figure not reproduced from the memorandum. |

### 4.4 HSIP rules

| ID | Claim | Source | Type | Used in model as | Confidence and caveat |
|---|---|---|---|---|---|
| E22 | APS-only projects are ineligible in all categories; APS must be part of a broader safety project. | Caltrans (2026d, Q3); Caltrans (2025a, p. 3) | Document | Rule: an application submitted as planned (SG142 as written) fails (`Sim._submit_hsip`, failure F-a) | High for Cycle 13. The rule changed over time: Cycle 10 funded an APS-only set-aside project (24 intersections, $248,200; Caltrans, 2021b), and the exclusion first appears in writing in the December 2025 advisory-committee minutes. The model applies the current rule to all future cycles. |
| E23 | Upgrading existing pedestrian heads to APS alone is not funded; APS can accompany new countdown heads (SI18PB). | Caltrans (2026d, Q1–Q2, Q4) | Document | Rule: carriers listed in `Sim._site_bcr_parts` | High. |
| E24 | The Local Roadway Safety Manual contains no APS countermeasure or crash-reduction factor. | Caltrans (2026g, Table 1 p. 31) | Document | Rule: APS adds cost but no benefit | High. |
| E25 | Countermeasures and factors: SI02 signal hardware 15%, 10 years, all crashes; SI07 mast-arm conversion 30%, 20 years, all crashes; SI18PB pedestrian countdown 25%, 20 years, pedestrian and bicycle crashes; SI22PB LPI 60%, 10 years, pedestrian and bicycle crashes. SI07 replaces SI02 where mast arms are added. | Caltrans (2026g, Table 1 p. 31; pp. 46, 56, 58) | Document | Rule: constants in `Sim._site_bcr_parts` | High. |
| E26 | Crash costs for signalised intersections: fatal and severe injury $2,379,000; other visible injury $213,000; complaint of pain $121,000. | Caltrans (2026g, Appendix D) | Document | Rule: `CC` in `code/model.py` | High. |
| E27 | SI02 benefits apply to crashes on the upgraded approaches. | Caltrans (2026g, SI02 note) | Document | Parameter: `f_aff` ∈ [0.5, 1.0] | Medium. The share of 50 m crashes on upgraded approaches is an assumption. |
| E28 | Minimum BCR 5.0 to submit; $10 million cap per agency for BCR applications; no limit on the number of BCR applications. | Caltrans (2026c, p. 4); Caltrans (2026d, Q60–61) | Document | Rule: `Sim._build_app` | High. |
| E29 | At most three countermeasure types per category in one application. | Caltrans (2026d, Q28–29) | Document | Rule: union of countermeasures ≤ 3 (`Sim._build_app`) | High. |
| E30 | Final funding cutoffs in cycles 8–12 were 3.5, 7.5, 12.0, 18.0 and 7.0; Caltrans hopes to fund all eligible BCR applications in Cycle 13. Caltrans uses BCR to prioritise. | Caltrans (2026d, Q65, Q68–69); Caltrans (2026f, slide 22) | Document | Parameter: `c_final` ∈ [3.5, 18.0]; effective cutoff max(5.0, `c_final`) (`Sim._hsip_events`) | High for history; the Cycle 13 cutoff is unknown. |
| E31 | Selection ratios (applications to selected) in cycles 8–12 were 91%, 63%, 62%, 66% and 87%. | Caltrans (2026f, slide 22) | Document | Not used as a multiplier (it already includes competition at the cutoff); `q_fail` covers only residual random failure | Medium. |
| E32 | San Francisco submitted one Cycle 12 application (signs, BCR, $3.97 million), which was funded; none concerned APS. | Caltrans (2024a); Caltrans (2025b) | Document | Parameter: `r_other` ∈ [$0, $10 million] (other SF applications sharing the cap) | Medium. Earlier cycles list only funded projects. |
| E33 | The FY2025–29 capital plan expected $1.0 million for SG136 "APS FY25" from HSIP Cycle 12; no SF APS application appears among the 330 Cycle 12 applications. | SFMTA (2024b, p. 48); Caltrans (2024a) | Document | Initial value: status-quo local amount; supports the M-A setting | High for both facts; the link between them is an inference. |
| E34 | Reimbursement 90%; local match 10%. ADA ramps are eligible items within a broader project. | Caltrans (2026d, Q4, Q14, Q59) | Document | Rule: cost split in `Sim._hsip_events` | High. |
| E35 | Pedestrian-crossing set-aside: $360,000 per agency (at 90%), one application, other work ≤ 20% of cost; APS is not on the eligible list. | Caltrans (2026c, pp. 4–6) | Document | Rule: `Sim._setaside` (total ≤ $400,000, APS ≤ 20%); parameter `p_sa` | High for the rules; `p_sa` is uncalibrated. |
| E36 | Cycle 13: call 1 July 2026, deadline 2 November 2026, approval March–April 2027; cycles are biennial. | Caltrans (2026c); Caltrans (2026f, slides 21, 28) | Document | Rule: `HSIP_CYCLES`, July–October window for discretionary starts (committed applications may start earlier, `Sim._task_step`), November deadline, approval in March or April of the next year (`Sim.window`, `Sim._submit_hsip`) | High for Cycle 13; later cycles are assumed to keep the same calendar. |
| E37 | Delivery: preliminary engineering within 9 months; construction authorisation within 36 months (42 with consultant design); removal and refund if not under construction after five years. On removal, sites return to their status before the award; the agency counts as red-flagged only while a project is past five years and not yet construction-authorised, and not after the project ends. | Caltrans (2021a, p. 8); Caltrans (2026f, slide 23); Caltrans (2026a), notes | Document | Rule: `Sim._new_project`, `Sim._project_step`; switches `sw_pe`, `sw_consult`; extension parameters `e_ext`, `t_ext` | High for the milestones; the extension probability and length are assumptions. |
| E38 | San Francisco's past awards reached construction authorisation 15–28 months after award. | Caltrans (2026a), computed for SF projects in cycles 6, 10 and 11 | Data | Parameter: `t_con_med` ∈ [8, 16] months from the January after award (award-based durations minus 8–10 months from cycle start to award) | Medium. Few projects; the conversion is described in the parameter documentation. |
| E39 | Federal-aid work by the agency's own forces needs a public interest finding with a cost comparison. | Caltrans (2026e, pp. 7–8) | Document | Parameters: `t_pif`, `q_pif_deny`; denial routes work to a contractor (`k_contract`, `t_contract`) | High for the requirement; durations are not published. |
| E40 | Agencies need a local road safety plan or equivalent updated or confirmed within five years; an update need not be final at submission. | Caltrans (2026c, p. 1); Caltrans (2026d, Q45–54, Q48) | Document | Rule: `Sim._lrsp_valid` (60-month validity); parameters `lrsp_until`, `q_lrsp`, `t_lrsp` | High for the rule. San Francisco's plan date was not verified, so validity is sampled. |
| E41 | San Francisco is not on the Q4 2026 list of delayed HSIP projects. | Caltrans (2026b) | Data | Initial value: no agency red flag at start; `rho_flag` covers other projects | High. |
| E42 | The signal-hardware countermeasure SI02 can carry APS in a BCR application. | SFMTA staff, personal communication, 2026 | Interview | Switch: `sw_si02` (main setting 1; robustness runs with 0) | Low. No public Caltrans determination was found. Both positions are reported. |
| E43 | SG015 visibility upgrades and SG142 APS are listed as separate lines, both from HSIP Cycle 13 (estimate) in FY2028; SG015 covers five named corridors. | SFMTA (2026c), SG015, SG142 | Document | Rule: federal-safety-grant-first starts with an SG015 corridor bundle (`mode = 'sg015'`) | High for the plan; whether SFMTA intends one combined application is not stated. |

### 4.5 Local funding

| ID | Claim | Source | Type | Used in model as | Confidence and caveat |
|---|---|---|---|---|---|
| E44 | The Traffic Signs and Signals Maintenance 5YPP for FY2024–28 programmes about $2.8 million a year with no APS installation line; SFMTA is the sole sponsor. | SFCTA (2023b, pp. 5, 10–14) | Document | Rule: no standing local line at start (`sw_line` default 0); Prop L amendment path | High. |
| E45 | SG017 Traffic Signal Hardware Replacement (Prop L, $500,000 in FY2027 and FY2028) lists new APS where poles and conduit are adequate; its FY2025–26 allocation went to about 98 controllers with a firewall vulnerability. | SFMTA (2026c), SG017; SFCTA (2025b, p. 7) | Document | Rule: existing-hardware pathway requests SG017 in July 2026 and July 2027; parameters `q_sg017_block`, `a_sg017` | Medium. Use of FY2027–28 funds is unknown. |
| E46 | A district Neighbourhood Transportation Program allocation including APS was approved about three and a half months after the November 2024 election. | SFCTA (2025c); SFCTA (2023a, pp. 7–8) | Document | Parameter: `t_defer` and the fixed three-month lag in `Sim._propl_amendment` | Medium. One precedent. |
| E47 | Allocations are made on applications prepared and submitted by eligible sponsors; SFCTA staff review, then the Community Advisory Committee and the Board. | SFCTA (2025a, p. 22) | Document | Rule: no allocation without an A2 submission | High. |
| E48 | The only General Fund APS lines in recent plans are estimates: $292,817 (FY2028) and $570,000 (FY2031). | SFMTA (2024b); SFMTA (2026c), SG143 | Document | Parameter: `a_local` ∈ [$0, $570,000] | High for the amounts; they are plan estimates, not appropriations. |
| E49 | The FY2023–27 plan funded an APS line of about $2.0 million (SG105, about 50 intersections) from the City's share of the ride-hail (TNC) tax; later plans have no such line. | SFMTA (2022b, pp. 45, 96–97); SFMTA (2024b); SFMTA (2026c) | Document | Rule: owner = 1 in the historical segment until `SG105_END` (June 2024) in M-A and M-D (`Sim.owner`) | Medium. No document dates the exhaustion of SG105; June 2024 is inferred from the request-list break and was tested as a breakpoint in the historical screening. |
| E50 | The Director's authority covers technical corrections and allocation of new or discretionary revenue; cumulative corrections above 10% of the capital budget return to the Board. | SFMTA Board of Directors (2026) | Document | Parameter: `q_dir` ∈ [0, 0.8], federal-safety-grant-first final fallback | Low. The document gives a review threshold, not an amount for APS; the fallback is hypothetical. |
| E51 | Capital revenue in the FY2027–31 plan is about $246 million below the previous plan and insufficient for all approved projects; the operating gap is $307 million in FY2027. | SFMTA (2026d, pp. 5, 20, 26); SFMTA (2026b, p. 2) | Document | Not used directly; context for M-C1 and for `q_gf`, `q_topup` ranges | High for the figures. |

### 4.6 Behaviour of the decision-making agent, advocates and enforcement

| ID | Claim | Source | Type | Used in model as | Confidence and caveat |
|---|---|---|---|---|---|
| E52 | The policy assigns no owner or deadline to applying for funding; its clock starts after funding. | SFMTA (2022a, p. 2) | Document | Rule: `specified` = 0 at start; owner indicator 0 in M-A/M-D | High for the text. "No obligation" is an inference from silence. |
| E53 | In July 2026 SFMTA presented three pages on technical challenges and cost to the Council and said remaining requests are "selected based on funding". | SFMTA (2026a, pp. 4–6, 8); MDC (2026) | Document | Parameter: `p_deflect` ∈ [0.5, 0.95] (M-A, M-D) | Medium for the response pattern; the probability is not measured. |
| E54 | Responsibility for applying is passed between agencies, and the response to disability advocates is that money is lacking and costs are high. | SFMTA staff, personal communication, 2026 | Interview | Supports the deflection rule and the `oversight` range [0.05, 0.6] | Low. A single source; used only to set a sampled range, never a point value. |
| E55 | Court orders elsewhere require a named funding lead and pursuit of all funding sources. | S.D.N.Y. (2022, p. 9); N.D. Ill. (2025, pp. 9–11) | Document | Rule: the accountability-first pathway sets owner = 1 and `specified` = 1 and adds 0.3 to oversight (`Sim._accountability_on`) | Medium. The analogy transfers the form of the remedy, not its effect size. |
| E56 | Within the searched records, no public APS advocacy statement in San Francisco was found for 2024–2026, and the July 2026 Council item drew no public comment. | MDC (2026) | Document (absence) | Parameter: `lam_press` ∈ [0, 0.5] includes zero | Low. Private meetings are unrecorded; LightHouse's 2022 initiative (Albers, 2022) is a counter-example. |
| E57 | Litigation timelines: New York 2018 complaint to 2022 remedial order (3.7 years); Chicago 2019 complaint to 2025 remedial plan order (5.7 years). | S.D.N.Y. (2022, p. 1); N.D. Ill. (2025, pp. 1–2) | Document, computed | Not used as a duration; the enforcement level changes only the start probability | Medium. |
| E58 | No annual probability of an APS suit against San Francisco can be estimated from public records. | — | Inference | Parameter: `eps_enf` ∈ [0, 0.1] per year | Low. Pure assumption, including zero. |

### 4.7 Staffing

| ID | Claim | Source | Type | Used in model as | Confidence and caveat |
|---|---|---|---|---|---|
| E59 | 21 budgeted 9145 positions in each fiscal year 2023–24 to 2027–28 (20.58 in 2022–23); 8 on project support. | CCSF (2022, pp. 26–27); CCSF (2024); CCSF (2026, pp. 122–123) | Document | Context for `k0` ∈ [0.5, 3] sites per month | High for budgeted positions; actual staffing is unpublished. |
| E59a | The SFMTA bargaining unit that includes traffic signal electricians reported an 18% vacancy rate in April 2026. | SFMTA (2026e, p. 7) | Document | Context for the lower end of crew capacity; not a parameter | Medium. Unit-level, not class-level. |
| E60 | Eligible lists of 7 (2022), 25 (2023) and 41 (2025) candidates. | SF DHR (2022, 2023, 2025) | Document | Context; argues against a strong "cannot hire" version of M-B | High. |
| E61 | Hiring slowed from 1 July 2024 and non-essential hiring was frozen from 1 October 2024. | SFMTA (2025) | Document | Rule: strain start July 2024 in M-B1 (`switches`) | High for the dates; the freeze's effect on the Signal Shop is not reported. |
| E62 | Signal Shop staffing was "often the limiting factor" in 2023. | SFCTA (2023b, p. 9) | Document | Rule: strain start January 2023 in M-B2 | Medium. Qualitative statement. |
| E63 | City-wide average time to fill an approved vacancy was about 8 months (255 days) in 2022. | SFMTA (2022c, p. 9) | Document | Parameter: `t_vac` ∈ [3, 18] months | Medium. Not specific to grant staff. |

### 4.8 Pathway design elements

| ID | Claim | Source | Type | Used in model as | Confidence and caveat |
|---|---|---|---|---|---|
| E64 | Adaptive pathways specify actions, signposts and switching rules. | Haasnoot et al. (2013) | Document (method) | Rule: `Sim._pathway_signposts`, thresholds `th_defer`, `th_idle`, `th_parent`, `th_rule` | High for the method; thresholds are design choices swept as parameters. |
| E65 | All new signals and major upgrades receive APS. | SFMTA (2023, p. 6); SFMTA (2026a, p. 7) | Document | Rule: the design-standards pathway extends this to push-button and hardware changes at C sites (`Sim._design_rule`), parameters `lam_hw`, `b_hw` | Low for the extension. No document gives hardware-change frequency or an APS add-on budget. |
| E66 | State-owned signals must receive LPI and touch-free APS when first installed or replaced. | Caltrans (2024b) | Document | Not used (state signals are outside the request list); cited as precedent for a design rule | High for the directive. |

## 5. Evidence not incorporated, and why

| Evidence | Source | Reason not incorporated |
|---|---|---|
| Citywide coverage series (e.g. 490 of 1,285 signals in July 2023; 611 of 1,305 in July 2026) and net citywide additions of about 30–40 a year | SFMTA (2023, p. 3); SFMTA (2026a, p. 3) | The model covers the request channel. Citywide additions mix in-house and project installations and cannot be split by delivery route, so they serve only as an outer plausibility bound. |
| Peer-city programmes and court-ordered installation quotas (New York minimums of 400 rising to 1,200 a year; Chicago minimums of 70 to 245 a year) | S.D.N.Y. (2022, pp. 3–4); N.D. Ill. (2025, p. 6) | Quotas reflect court supervision in cities with coverage below 5%; transferring them to San Francisco would assign an effect size without local evidence. Enforcement acts only on application initiation (Section 3.6). |
| Federal Safe Streets and Roads for All (SS4A) grants for the Tenderloin and Western Addition signal projects, both including APS in scope | SFMTA (n.d.-d, n.d.-e) | Existing awards enter through fold-in sites (E13). New SS4A rounds are not simulated: the programme's continuation after FY2026 could not be verified. |
| Active Transportation Program eligibility and oversubscription | — | Not simulated; no public source on San Francisco applications for APS was found, and the programme's success rate by amount (about 7–15%) would be an unsupported parameter. |
| The ride-hail (TNC) tax: the county authority's half is dedicated to street safety including signal improvements; the agency's half lists access and signal items in transit-oriented terms | CCSF (2019, § 3208) | The City share last funded APS in the FY2023–27 plan (E49); whether the agency's half can fund pedestrian APS is a contested reading. No TNC channel is simulated beyond the standing local line. |
| New York's remedy opinion found that the city had not applied for federal funds, including HSIP, for APS before the litigation | S.D.N.Y. (2021, pp. 63–64) | Supports the form of the accountability remedy (E55) but describes another city; no effect size is transferred. |
| Public right-of-way accessibility guidelines | Architectural and Transportation Barriers Compliance Board (2023) | Not enforceable for city signals until adopted by the Department of Justice; external standards are excluded. |
| ADA transition-plan obligations for curb ramps | — | Ramps enter only as a conditional cost (E17); no corresponding federal retrofit schedule for APS was found. |
| Statement that leaving existing curb ramps untouched could make installation "five times faster" | MDC (2026) | An untested oral statement; no legal basis for the ramp requirement was found. Not used as a multiplier. |
| Accessibility strategy adopted without an APS goal | SFMTA (2026f) | No modelled channel; a performance target would act through ownership or deadlines, already represented. |
| November 2026 ballot measures | — | No measure directs money to signals or APS; any indirect effect through operating deficits is outside the model. |
| Malfunctioning installed devices and maintenance | SFMTA (2026a, p. 9) | The outcome is installation; device condition is excluded. |
| Hypotheses from an adversarial review of the design by a large language model (Anthropic's Claude Sonnet, prompted to act as funding staff and advocates): district Prop L shares as a funding route; shifting ramp and conduit costs to the curb-ramp programme; separating APS from its HSIP carrier application; promises of follow-up absorbing advocacy pressure; SFCTA gatekeeping and staged allocations; fault repairs displacing a restored dedicated line | Method rationale: Larooij & Törnberg (2025) | Unverified hypotheses with no documentary support; reported as limitations, not incorporated. |

## 6. Boundaries of the evidence

- **Single interview.** Two model elements rest partly on the author's interview with SFMTA staff: the SI02 carrier switch (E42) and the deflection pattern (E54). Neither is used as a point estimate. The switch is reported in both positions; the deflection probability is sampled over [0.5, 0.95] and active only in the unassigned-responsibility settings.
- **Evidence of absence.** Claims that something did not happen (no APS application in Cycle 12, no advocacy statements, no suit) rest on bounded searches of public records and are graded Low or Medium accordingly.
- **Uncalibrated behaviour.** All coefficients of the start probability (`b0`, `b_own`, `b_spec`, `b_ov`, `b_pr`, `b_enf`, `m_b`, `m_c`) have no documentary value. The historical screening constrains them only weakly; results are shares across assumed ranges, not estimates.
- **Unverifiable at the time of the study.** Whether SFMTA applied to HSIP Cycle 13, and with which carriers; site-level LPI and countdown status for 66 intersections; actual Signal Shop staffing; the date San Francisco's local road safety plan was last confirmed.
