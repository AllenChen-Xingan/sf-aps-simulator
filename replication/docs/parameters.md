# Model parameters

## 1. Scope

The model has 98 parameters. Their machine-readable definition is `code/params.py` (list `_S`, functions `param_schema`, `default_params` and `sample`). `data/parameters.csv` reproduces that list row for row and adds, for each parameter, a description, a source category, a source and notes on how the code uses it. Numerical columns in the CSV (`low`, `high`, `default`, `choices`) are copied from `code/params.py` without rounding; where the CSV and the code ever differ, the code governs.

This document explains the columns, the source categories, the prior widths, where each parameter is active, the functional groups, the quantities that are fixed in code rather than listed as parameters, and the Morris screening ranking. References to `Sim.<method>` denote methods of class `Sim` in `code/model.py`. Citations use the author–date keys of `docs/references.md`.

## 2. Columns of `data/parameters.csv`

| Column | Content |
|---|---|
| `name` | Identifier used in code. |
| `description` | What the parameter represents. |
| `unit` | Unit as recorded in `code/params.py`. `0-1` is an index, `logit` a log-odds intercept, `logit/unit` and `logit/level` a change in log-odds per unit, `code` a categorical code, `switch` a 0/1 indicator. Rates "per year" are converted to monthly probabilities as 1 − exp(−λ/12) unless the notes say otherwise. |
| `distribution` | `uniform` (continuous, sampled uniformly between `low` and `high`), `switch` (0 or 1, equal probability) or `discrete` (equal probability over `choices`). |
| `low`, `high` | Bounds of the base prior. For switches and discrete parameters, the smallest and largest admissible values. |
| `default` | Value used when the parameter is not sampled (single runs, and the fixed background of the Sobol analysis). |
| `choices` | Admissible values of switches and discrete parameters, separated by semicolons. |
| `settings` | Settings (mechanisms) in which the parameter can affect outcomes, separated by semicolons. |
| `stage` | `all`: used in the historical segment (from July 2022) and in projections (from July 2026); `projection`: used only in projections. |
| `source_category` | One of four categories (Section 3). |
| `source` | Basis of the range or value, with public sources cited author–date and page, clause, slide or question number. |
| `notes` | How the code uses the parameter, and any difference between the design documentation and the code. |

## 3. Source categories

| Category | Meaning | Count |
|---|---|---|
| `document` | A public document states the value, the range ends or a rule that fixes them; range ends not given by the document are marked as assumptions in `source`. | 4 |
| `data-derived` | Calculated from a data set (request status lists, HSIP project records, signal diagrams). | 5 |
| `assumption-range` | No document gives a number; the range is chosen to span plausible values and is explored by sampling. Where a document gives a scale reference or the governing rule, `source` cites it. | 88 |
| `hypothetical` | Neither the value nor the mechanism has documentary support. | 1 (`q_dir`) |

The predominance of `assumption-range` reflects the nature of the question: most quantities concern internal agency behaviour (how often staff start an application, how pressure decays, how often a vacancy occurs) for which no public record exists. The model therefore reports results as shares across these ranges, not as forecasts. Personal communication with SFMTA staff is the sole basis for one parameter value (`sw_si02` = 1) and for the qualitative description behind `oversight` and `p_deflect`; it is cited without identifying details.

## 4. Prior widths

All continuous parameters have a base prior U(`low`, `high`). Two alternative widths are used in the historical screening (experiment E1) to test sensitivity to the prior:

- **Base** (width 1.0): U(`low`, `high`).
- **Narrowed** (width 0.5): same midpoint, half the width.
- **Widened** (width 2.0): same midpoint, twice the width, kept within the legal domain: parameters with unit `probability`, `fraction` or `0-1` are clipped to [0, 1]; other parameters with `low` ≥ 0 are not allowed below 0 (if `low` = 0) or below half of `low` (if `low` > 0); parameters with negative `low` (`b0`, `lrsp_until`) are not clipped.

Switches and discrete parameters are sampled with equal probability over their choices at every width (`code/params.py`, `sample`). Sampling is Latin hypercube over the continuous parameters.

A fourth screening group, "wide independent rates", keeps the base width for all parameters but redraws `h_in` from U(0.3, 2.0) and `h_fs` from U(0.03, 0.5), because the base ranges of these two rates are estimated from the same transitions that the screening targets use (`code/experiments.py`, `e1`).

## 5. How parameters enter the experiments

- **Historical screening (E1).** All parameters are sampled. Parameters with `stage` = `projection` have no effect on the historical segment, with one exception: `q_topup` also governs local cost overruns in the historical segment (`Sim._overruns`).
- **Projections (E2, E3).** Parameters with `stage` = `all` are resampled jointly, as whole accepted combinations, from the base-width E1 screening; parameters with `stage` = `projection`, including `q_topup`, are drawn by an independent Latin hypercube, replacing the values in the accepted combination (`code/experiments.py`, `e23`). Two parameters labelled `all` (`t_parent`, `done3_real`) act only at the projection start, so their screened values carry no information from the history.
- **Sensitivity analysis (E4).** Morris screening samples all 98 parameters over their base ranges without historical screening; the unit interval is mapped linearly to each continuous range and in equal slices to the choices of switches and discrete parameters (`code/experiments.py`, `decode`). The Sobol analysis varies the 12 leading parameters and fixes the other 86 at `default`; a background check reruns PW0 and PW4 under M-A and M-D with the other 86 fixed at their 25th and then 75th prior percentiles (base sample 256) (`code/experiments.py`, `e4b`).
- **Direct-effect-zero control.** `b_own`, `b_spec`, `b_ov` and `b_pr` are set to 0; everything else is unchanged.

## 6. Where parameters are active

Every parameter is sampled in every setting and pathway; a parameter outside its active domain has no effect on outcomes.

### 6.1 Setting-specific parameters

| Parameter | Active in |
|---|---|
| `p_deflect`, `r_back` | M-A, M-D |
| `m_b`, `strain_ramp`, `strain_end`, `phi` | M-B1, M-B2, M-D |
| `m_c`, `g_cost` | M-C1, M-D |
| `tau` | M-C2, M-D |

The settings also change two quantities that are not parameters: the owner indicator falls to 0 after the dedicated funds end under M-A and M-D, and staffing strain starts in July 2024 (M-B1, M-D) or January 2023 (M-B2) (`code/model.py`, `switches`). All other parameters apply in all six settings.

### 6.2 Pathway-specific parameters

| Parameter | Used by |
|---|---|
| `a_line`, `aps_share` | Any run in which a standing local line is on: `sw_line` = 1; in the base design, PW4 from the start and PW5 at month 24 if design-rule installations are below `th_rule`; PW1 after an approved Prop L amendment; PW2 and PW6 after an approved Prop L amendment or General Fund request. In the approval variant PW4 and PW5 request the line through the Prop L and General Fund chain instead. `a_line` is also the one-time amount of a Director reallocation (PW1). |
| `q_veto`, `t_defer`, `th_defer` | PW1, PW2, PW6; PW4 and PW5 in the approval variant. |
| `q_gf` | PW2, PW6; PW4 and PW5 in the approval variant. |
| `q_dir` | PW1 only (last step). |
| `th_idle` | PW3 only. |
| `th_parent`, `t_parent` | PW4 only. |
| `th_rule`, `lam_hw`, `b_hw` | PW5 only. |
| `q_sg017_block`, `a_sg017` | PW6 only. |
| `t_partner`, `q_partner_cancel` | Projects submitted in SG015-bundle mode (PW1, PW4). |

HSIP parameters (Section 7.5) matter only when an application is bundled with a carrier. Under PW0, PW3 and PW5 an HSIP application, if started, is submitted as APS-only and fails eligibility at once (`Sim._submit_hsip`), so these parameters have no effect in those pathways. PW1 and PW4 bundle from Cycle 13; PW2 and PW6 reach HSIP bundling only after their local routes fail.

## 7. Parameter groups

### 7.1 Initiation (11)

`oversight`, `b0`, `b_own`, `b_spec`, `b_ov`, `b_pr`, `b_enf`, `d_prep`, `lam_quit`, `t_vac`, `q_drop`.

Each month in an open funding window, an idle application task starts preparation with probability p, where

logit p = b0 + b_own·Owner + b_spec·Deadline + b_ov·oversight + b_pr·Pressure + b_enf·max(0, Enforcement − 1) − m_b·Strain − m_c·CostPressure

(`Sim.p_start`). No document gives these coefficients; all effect sizes are drawn from ranges that include zero. Preparation takes `d_prep` months and must finish by the window deadline. The owner leaves at rate `lam_quit`, the post stays vacant for `t_vac` months (Owner = 0), and a task in preparation is dropped with probability `q_drop`.

### 7.2 Pressure and enforcement (7)

`lam_press`, `k_decay`, `p_deflect`, `r_back`, `lam_quiet`, `t_quiet`, `eps_enf`.

Advocacy pressure events arrive at rate `lam_press`, except during quiet spells that start at rate `lam_quiet` and last `t_quiet` months. Each retained event decays as exp(−Δt/`k_decay`). Under M-A and M-D an event is deflected with probability `p_deflect` (buck-passing, in the form of Fioretti & Lomi, 2010), which blocks idle tasks for `r_back` months instead of adding pressure. External enforcement rises one level at rate `eps_enf`, up to a court order (level 4).

### 7.3 Staffing (5)

`m_b`, `strain_ramp`, `strain_end`, `phi`, `k0`.

In the staffing settings, strain rises linearly to 1 over `strain_ramp` months from the setting's start month and ends `strain_end` months after December 2026. Strain lowers the start log-odds by `m_b` and crew capacity by the fraction `phi`. `k0` is the in-house crew capacity in all settings.

### 7.4 Costs and technical constraints (9)

`u0`, `g_cost`, `m_c`, `tau`, `q_pipe`, `q_ramp`, `k_cont`, `sigma_over`, `q_topup`.

The base APS unit cost `u0` grows at `g_cost` per year from July 2022 in the cost settings, where cost pressure lowers start log-odds by `m_c` per unit. In the technical-constraint settings a share `tau` of candidate sites is blocked. Conduit and ramp adders (`q_pipe`, `q_ramp`, $200,000 each) are drawn when a site is created and counted once. Budgets include contingency `k_cont`; overruns found at design completion follow a log-normal with scale `sigma_over`; gaps beyond contingency receive a top-up with probability `q_topup`, otherwise the site or project is returned to the pending pool.

### 7.5 HSIP application, benefit–cost ratio and eligibility (24)

`y_win`, `l_rule`, `f_aff`, `crash_impute`, `c_final`, `r_other`, `rho_flag`, `q_fail`, `p_sa`, `d_split`, `s_12in_C`, `s_bp`, `s_mast`, `s_lpi`, `s_cd`, `c_12in`, `c_bp`, `c_lpi`, `c_full`, `c_cd`, `c_xing`, `lrsp_until`, `q_lrsp`, `t_lrsp`.

These parameters build and judge HSIP applications (`Sim._site_bcr_parts`, `Sim._build_app`, `Sim._submit_hsip`, `Sim._setaside`, `Sim._hsip_events`). Carrier availability at each site (`s_*`) and carrier costs (`c_*`) determine which countermeasures can accompany APS; benefits combine crash reduction factors over two crash groups (pedestrian or bicycle, and other), the share `f_aff` of crashes on upgraded approaches, crash windows `y_win` and service-life rule `l_rule`. Bundles must reach a BCR of 5.0 to be submitted and max(5.0, `c_final`) to be approved, within the $10M agency cap less `r_other`. Eligibility depends on a valid local road safety plan (`lrsp_until`, `q_lrsp`, `t_lrsp`), on red flags from other San Francisco projects (`rho_flag`, one draw per review month) and on modelled projects that missed milestones or passed five years without construction. Technically blocked sites (`tau`) never enter a bundle. A pedestrian-crossing set-aside application (`p_sa`, `c_xing`) is added when preparation time allows (`d_split`).

### 7.6 Prop L and General Fund (9)

`a_local`, `a_line`, `aps_share`, `q_veto`, `t_defer`, `q_gf`, `q_dir`, `q_sg017_block`, `a_sg017`.

Under current practice local money for APS is at most `a_local` per year and is allocated only when staff submit a local application; one-time amounts from a Director reallocation or SG017 are allocated on their own. A standing line provides `a_line` × `aps_share` per year without an application. PW2 requests a line through a Prop L amendment (`q_veto`, `t_defer`), then the General Fund (`q_gf`), then turns to HSIP bundling. PW6 first tries the existing SG017 hardware programme (`q_sg017_block`, `a_sg017`), then follows the same chain. PW1 reaches a Prop L amendment only after two HSIP cycles and, if it fails, ends with a Director reallocation (`q_dir`, hypothetical); it makes no General Fund request.

### 7.7 Construction and delivery (21)

`h_in`, `h_fs`, `t_des`, `sw_pe`, `t_pe`, `t_pif`, `q_pif_deny`, `sw_consult`, `t_con_med`, `t_dsg`, `t_pause`, `t_fix`, `t_contract`, `k_contract`, `t_partner`, `q_partner_cancel`, `t_build`, `e_ext`, `t_ext`, `t_parent`, `pi_scope`.

Funded in-house sites install at rate `h_in` subject to crew capacity; sites funded through signal projects install at rate `h_fs`. HSIP projects pass through design (`sw_pe`, `t_pe`, `t_dsg`), a public interest finding (`t_pif`, `q_pif_deny`) and construction authorization (`t_con_med`); milestone limits (9 months for PE, 36 or 42 months for construction, depending on `sw_consult`) raise red flags that last from the missed limit until the late authorization plus `t_fix` months, merged into one interval when both occur; a project without construction after five years is removed unless extended (`e_ext`, `t_ext`). A denied finding leads to contracting out (`t_contract`, `k_contract`, `t_build`, `t_pause`). `t_partner` and `q_partner_cancel` govern partner projects in SG015 bundles; `pi_scope` and `t_parent` govern sites folded into existing projects.

### 7.8 Arrivals (1)

`lam_arr`.

In projections new requests arrive as a Poisson count with monthly mean `lam_arr`/12. In the historical segment arrivals are read from the request lists.

### 7.9 Pathway signposts and the design rule (6)

`th_defer`, `th_idle`, `th_parent`, `th_rule`, `lam_hw`, `b_hw`.

The pathways are adaptive (Haasnoot et al., 2013): each starts with a short-term action and switches when a signpost threshold is crossed. Thresholds are design choices, swept as parameters. `lam_hw` and `b_hw` define PW5's design rule, under which hardware-change events at candidate sites fund APS within a capped annual budget; funded sites join the in-house queue and install subject to `h_in` and crew capacity.

### 7.10 Scenario switches (5)

`sw_si02`, `sw_si07`, `sw_line`, `done3_real`, `fs5_parent`.

Switches represent unresolved factual questions: whether a signal-hardware upgrade (SI02) or mast-arm conversion (SI07) is accepted as an APS carrier, whether a standing local line exists from the start, whether three sites whose parent work is complete are truly undelivered, and whether five signal-project sites without an identified parent project have one. Both states are sampled; results can be reported by switch state.

## 8. Quantities fixed in code

The following quantities are constants in `code/model.py`, not sampled parameters.

| Quantity | Value | Basis |
|---|---|---|
| Crash costs, signalized intersection | KA $2,379,000; B $213,000; C $121,000 | Caltrans (2026g), Appendix D |
| Crash reduction factors and service lives | SI02 15%, all crashes, 10 years; SI07 30%, all crashes, 20 years; SI18PB 25%, pedestrian and bicycle, 20 years; SI22PB 60%, pedestrian and bicycle, 10 years | Caltrans (2026g) |
| BCR submission minimum | 5.0 | Caltrans (2026c), p. 4; Caltrans (2026d), Q65 |
| Agency cap, BCR category | $10,000,000 | Caltrans (2026c), p. 4; Caltrans (2026d), Q60–61 |
| Set-aside limits | total ≤ $400,000 (HSIP ≤ $360,000 at 90%); APS ≤ 20% of total | Caltrans (2026c), pp. 4–6 |
| HSIP share of cost | 90% (local 10%) | Caltrans (2026d), Q14, Q59 |
| Countermeasure types per bundle | at most 3 | Caltrans (2026d), Q28–29 |
| Delivery limits | PE authorization 9 months; construction authorization 36 months (42 with consultant design); removal at 5 years; 10% of cost recorded as refunded on removal | Caltrans (2021a), p. 8; Caltrans (2026f), slide 23 |
| HSIP calendar | cycles in 2026, 2028, 2030, 2032, 2034; preparation July–October (a task committed by a pathway may start up to ceil(`d_prep` + (m − 1)·`d_split`) months before the deadline, m = 1 for an SG015 bundle and 3 for a repack; an unsubmitted commitment rolls over to the next cycle); deadline and eligibility review in November; approval in March or April of the next year (equal probability; set-aside applications in April); project start the following January | Caltrans (2026c) |
| Local calendar | preparation January–June; allocation decision in July | assumption |
| Prop L amendment | decision 3 months after request (plus `t_defer`) | assumption |
| Road safety plan validity after an update | 60 months | Caltrans (2026c), p. 1 |
| Conduit and ramp adders | $200,000 each | SFMTA (2026a), pp. 4–5 |
| Cap on local actual cost after overrun | $1,500,000 per site | SFMTA (2026a), pp. 4–5 |
| Cost-pressure reference | $20,000 | SFMTA (2018a), slide 6 |
| End of dedicated funds (owner indicator, history) | June 2024 | not documented; the screening scanned 2023-06, 2023-12, 2024-02, 2024-06 and 2024-12 at base width (`code/runner.py` sets the value per task) |
| Construction-authorization spread | log-normal, σ = 0.40 | assumption |
| PW3 accountability package | oversight +0.3 (capped at 1); pressure rate × 2; Owner and Deadline = 1 | design |
| PW1 switching dates | Cycle 14 repack in May 2027 if Cycle 13 brought no award or fewer than two awarded sites; Prop L amendment in May 2029 if there has been no award since the repack | design |
| Undated parent project | nominal finish 18 months after start | assumption |
| New-request states | C 32/41, Fs 6/41, N 3/41 | historical arrivals in SFMTA (2020–2026) |
| Historical exogenous moves into signal projects | C→Fs 0.0127 per year; N→Fs 0.033 per year | request-list transition rates |
| Crew capacity bank | at most max(3 × monthly capacity, 1) sites | assumption |
| Partner cancellation timing | 6 months after project start | assumption |

## 9. Morris screening ranking

Morris screening (Morris, 1991) used all 98 parameters, 20 trajectories, 4 levels and 20 replicates per parameter combination, in 42 cells (7 pathways × 6 settings), with the replicate mean of installations within ten years as the outcome. It ran twice with different seeds. The two top-12 lists shared 10 parameters, so the first list was used for the Sobol analysis, as fixed before the run (source: `results/e4-sensitivity/morris.json`).

| Rank | Parameter | Group | Mean μ*, pass 1 | Mean μ*, pass 2 |
|---|---|---|---|---|
| 1 | `aps_share` | Prop L and General Fund | 14.91 | 17.81 |
| 2 | `q_ramp` | Costs | 14.23 | 12.40 |
| 3 | `q_pipe` | Costs | 13.03 | 18.03 |
| 4 | `h_fs` | Construction and delivery | 11.72 | 12.32 |
| 5 | `sw_line` | Scenario switches | 10.97 | 10.07 |
| 6 | `lam_arr` | Arrivals | 10.33 | 9.36 |
| 7 | `a_line` | Prop L and General Fund | 7.95 | 14.38 |
| 8 | `k_cont` | Costs | 6.23 | 2.02 |
| 9 | `fs5_parent` | Scenario switches | 6.23 | 6.30 |
| 10 | `q_topup` | Costs | 5.56 | 4.22 |
| 11 | `pi_scope` | Construction and delivery | 5.40 | 5.32 |
| 12 | `u0` | Costs | 5.24 | 5.24 |

Ranking is by pass-1 μ* averaged over the 42 cells. Only in pass 2's top 12: `g_cost`, `done3_real`; only in pass 1's: `k_cont`, `q_topup`. SALib normalizes elementary effects by the unit-cube step, so μ* approximates the change in ten-year installations when a parameter moves across its full range; switches and continuous parameters are not directly comparable. None of the initiation coefficients (Section 7.1) appears in either list: within the sampled ranges, money and cost parameters dominate the outcome.

## 10. Differences between design documentation and code

The parameter table fixed before the main runs is identical to `code/params.py` in all 98 rows (names, kinds, bounds, defaults, choices, settings and stages). The narrative design documentation differed from the code in the following points; the code was run as written.

| Parameter | Design documentation | Code |
|---|---|---|
| `h_in` | Gamma(23.5, 294.7 site-months), mean stated as about 0.94 per year | U(0.59, 1.41), default 0.94 |
| `h_fs` | Gamma(9.5, 657.7 site-months), mean stated as about 0.16 per year | U(0.08, 0.31), default 0.16 |
| `q_fail` | 0 in the control, U(0, 0.2) otherwise | U(0, 0.2), default 0 |
| `sw_line` | main scenario 1 | default 0; the main pathway comparison, a secondary analysis of the E3 runs, uses only combinations with `sw_line` = 0 |
| `done3_real` | equal probability | switch, equal probability when sampled, default 1 |
| `t_parent`, `done3_real` | stage "all" | used only at the projection start |
| `rho_flag` | probability per cycle | drawn once per review month, shared by all applications reviewed that month |
| `c_full` | upper end anchored at about $554,000 per site (Contract 35) | range unchanged; the anchor could not be traced to a page of a public document (see the `c_full` row of `data/parameters.csv`) |
