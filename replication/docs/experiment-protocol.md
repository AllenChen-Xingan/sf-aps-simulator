# Experiment protocol

This document records the experimental protocol: the model version, seeds, replicate counts, sample sizes, acceptance criteria and analysis rules under which the reported experiments were run, and the changes made to the model after the criteria were fixed, each with its reason. Results are reported in `docs/results.md`. The model is described in `docs/ODD+D.md`; parameters are listed in `docs/parameters.md` and `data/parameters.csv`. Development and testing are reported in `docs/TRACE.md`.

## 1. Status of the protocol

1. The acceptance criteria, tolerances, seeds, replicate counts, sample sizes and primary analysis rules in Sections 3–6 were fixed on 27 October 2026. None of them was changed afterwards.
2. The model code was corrected after that date: ten implementation defects were corrected and one design rule was revised (Section 9; `docs/TRACE.md` §5.6). The reported experiments were run with the corrected model identified in Section 2.
3. The secondary analyses in Section 8.3, including the main comparison restricted to combinations without a standing local line and the approval variant for PW4 and PW5, were specified before the reported runs. They are computed from the E3 runs (and, for the variant, an additional run of two pathways) and are identified as secondary analyses in `docs/results.md`.
4. Section 7 was written after the Morris screening and before the Sobol analysis, as Section 5.4 requires.
5. Results are reported whether or not they meet any criterion.

## 2. Versions and checksums

All checksums are SHA-256 of the file bytes.

| Item | SHA-256 |
|---|---|
| `code/model.py` | `6777d8e742dbe414635ab4e4af95092f7abdcb563e1b69d184f56e1e81a114eb` |
| `code/params.py` | `e83c1938cb73657070a3b03c031109c3651cf96bb1903bdd86c00464f9dc49d8` |
| `code/data/inputs.json` | `f37b2885f630e8fe94d4ec9a690968e35b1ab7960f0aef5d141ff1a2218f0401` |
| `code/experiments.py` | `3c96eaf7872ac9449e194225dbe455bd30d33d8a06779deffe4891edb5d0c862` |
| `code/runner.py` | `a6aa9b70585d629513bab540fba2fcb7921d5f9c93e303b6cad16ff666a315fc` |
| Combined model fingerprint | `e0f4869e2c32e15f2f3b905a242bcbaa09f7102cf6aaf151acf3e2ac11dff18f` |
| Design specification on which the protocol was based (a working document, not distributed; superseded by `docs/ODD+D.md`) | `63391da637a5ecfc39109d3e9632a102de223ba7402977bc79240e0528906a8f` |

The combined fingerprint is the SHA-256 of the three hexadecimal digests of `model.py`, `params.py` and `data/inputs.json`, joined in that order with a newline character (`code/final_export.py`, `code/e3_variant.py`). Recomputing it from the three digests above gives the value in the table. Since the criteria were fixed, `data/inputs.json` is unchanged, and `params.py`, `experiments.py` and `runner.py` have changed only in comments and documentation strings: their parameter values, sampling, seeding, criteria and analysis code are unchanged. Only the behaviour of `model.py` was changed (Section 9).

## 3. Seeds, replicates and execution

1. **Master seed:** 146.
2. **Replicates:** R = 20 stochastic replicates for every parameter combination in every experiment.
3. **Replicate seeds:** for a task with label *L*, the 20 seeds are `numpy.random.SeedSequence([146, crc32(L)]).generate_state(20)` (`code/experiments.py`, `seeds_for`). Task labels are `e1-{prior}-{i}` with `{prior}` ∈ {`base`, `narrow`, `wide`, `wide_rates`} (E1), `e23-{setting}-{i}` with `{setting}` ∈ {`M-A`, `M-B1`, `M-B2`, `M-C1`, `M-C2`, `M-D`} (E2/E3), `e4a-{pass}-{i}` with `{pass}` ∈ {1, 2} (E4a) and `e4b-{i}` (E4b), where *i* is the index of the parameter combination. Labels contain neither the pathway nor, in E1, the setting, so the same combination receives the same seeds in every pathway (all experiments) and every setting (E1). Seeds depend only on the label, not on the process that runs the task or on execution order.
4. **Common random numbers:** within an experiment, the same parameter combination receives the same seeds in every pathway and in both controls (E3), and in every pathway–setting cell (E4). Where pathways draw different numbers of random values, their random streams diverge after the first such draw.
5. **Parallel execution:** tasks are split into shards and run on (CPU count − 2) processes; merged output is ordered by task identifier (`code/runner.py`). The self-test `python -I code/runner.py --selftest` runs 168 tasks (12 combinations × 7 pathways × 2 settings) × 3 replicates on one process and on several processes and requires the serialised outputs to be identical.

## 4. Settings and pathways

Each experiment is run separately for six settings, each representing one explanation of why requested installations stalled: M-A unassigned responsibility; M-B1 staffing constraint from 2024; M-B2 staffing constraint from 2023; M-C1 rising costs; M-C2 technical constraints; M-D combined. Settings are parallel scenarios. The protocol contains no criterion for choosing between them.

Seven pathways are compared: PW0 current practice; PW1 HSIP-first (federal safety-grant first); PW2 local-first; PW3 accountability-first; PW4 crossing-specific allocation; PW5 design standards; PW6 existing hardware programme. Their rules are given in `docs/ODD+D.md`.

## 5. Primary experiments

### 5.1 E0: code check against an earlier baseline

A Markov multi-state model of the request lists was re-implemented (`code/baseline.py`) and compared with an earlier, independently written implementation of the same model. Both fit transition rates on the lists from 29 July 2022 to 20 February 2024 and predict installations from 20 February 2024 to 30 June 2026 (2,000 simulations, seed 146). The check passes if the medians differ by at most 1 and the 10th and 90th percentiles by at most 2. E0 checks code, not the agent-based model.

### 5.2 E1: historical screening and retrospective check

1. **Period simulated:** 48 months from July 2022, with pathway PW0 (no reform), for each setting.
2. **Observed stocks** (from the published request lists, `code/data/inputs.json`): candidates (C), funding-needed (N), funded agency-crew (Fi), funded signal-project (Fs) and cumulative installed among listed crossings (I).
3. **Screening snapshots** (up to 21 February 2025): 3 January 2023, 30 June 2023, 20 February 2024, 21 August 2024, 21 February 2025.
4. **Retrospective-check snapshots:** 8 August 2025, 29 January 2026, 30 June 2026.
5. **Acceptance criterion:** at every screening snapshot and for every stock, the mean of the 20 replicates differs from the observed value by no more than the tolerance: C ±6, N ±4, Fi ±5, Fs ±6, I ±8. A combination that meets this at all five screening snapshots is accepted.
6. **Retrospective check (H1):** an accepted combination passes H1 if the same criterion holds at the three retrospective snapshots.
7. **Samples:** 2,000 combinations for each prior width, drawn once with `numpy.random.default_rng([146, crc32(width name)])` and used for all six settings (`code/experiments.py`, `e1`). Continuous parameters are drawn by Latin hypercube; switches and discrete parameters are drawn independently and uniformly over their values (`code/params.py`, `sample`). Prior widths: base (×1.0), narrow (×0.5) and wide (×2.0), obtained by scaling the half-width of each continuous range about the midpoint of its base range. Scaled ranges are clipped to [0, 1] for probabilities and fractions; for other non-negative parameters a lower bound is not reduced below 0, or below half of a positive base lower bound. Switches and discrete parameters are not affected by width. An additional group of 400 combinations (label `wide_rates`) uses the base width but replaces the priors of the two installation rates estimated from the same request lists with wide independent priors, `h_in` ~ U(0.3, 2.0) and `h_fs` ~ U(0.03, 0.5), to test the effect of using the same records both to set priors and to screen.
8. **Exhaustion date of the earlier dedicated programme (SG105):** not documented; scanned at 2023-06, 2023-12, 2024-02, 2024-06 and 2024-12 under the base width, and fixed at 2024-06 for the other widths.
9. **Reported quantities:** acceptance rate, H1 pass rate among accepted combinations, the number of combinations meeting each stock's tolerance, and the 10th, 50th and 90th percentiles of selected parameters among accepted combinations.
10. **Interpretation rule:** screening acceptance is not a calibration and does not yield a posterior. The protocol contains no rule that selects a setting from E1.

### 5.3 E2 and E3: conditions for funding, and pathway comparison

1. **Parameter combinations:** for each setting, 1,000 combinations, generated with `numpy.random.default_rng([146, 23, index of setting])`. Parameters that act in the historical period are resampled as whole combinations, with replacement, from that setting's E1 combinations accepted under the base width, so that joint constraints from screening are preserved. The pool holds one entry per acceptance at each of the five exhaustion dates, so a combination accepted at *k* dates has weight *k*. Projection-only parameters are drawn independently (continuous parameters by Latin hypercube, switches and discrete parameters uniformly over their values).
2. **Design:** 6 settings × 1,000 combinations × 7 pathways × 2 controls = 84,000 tasks, each with R = 20 replicates (1,680,000 runs). Projection horizon: 120 months from July 2026.
3. **Controls:** *positive* (parameters as sampled) and *direct initiation effects zero* (`b_own`, `b_spec`, `b_ov` and `b_pr` set to 0, all other processes unchanged, including PW3's doubled pressure frequency and enforcement escalation). The second control asks how much of each result depends on ownership, deadlines, oversight and pressure raising the monthly probability of starting an application. It is not a "PW3 has no effect" control: that comparison is PW3 against PW0.
4. **Outcomes per combination** (means over the 20 replicates): `coverage_10y`, crossings installed among pending and newly arriving requests by month 120; `P_money`, the share of replicates in which at least one request-channel funding award occurs within 60 months (*funding within five years*).
5. **Robustness:** for each pathway, the share of combinations in which its `coverage_10y` exceeds that of PW0 under the same combination, control and seeds. **Maximum regret** is computed within a setting across pathways.
6. **Funding success** (for E2): a combination is a success if `P_money` ≥ 0.5. Thresholds 0.25 and 0.75 are also reported.
7. **PRIM (E2):** for each pathway (positive control), the combinations are split 50/50 into training and test halves, five times (split *s* uses `default_rng([146, s])`). On each training half, PRIM (EMA Workbench, default peeling settings) traces a peeling trajectory; the box selected is the densest box with at most three restricted dimensions and training coverage of at least 0.3. Coverage and density are reported on the test half. Candidate inputs are all projection-phase parameters plus `p_deflect`, `b0`, `b_own`, `k0`, `a_local` and `lam_press`.
8. **CART cross-check:** a decision tree of depth 3 (`scikit-learn`, `random_state = 0`) is fitted on the same training half and its test-set accuracy reported.

### 5.4 E4: global sensitivity analysis

E4 samples the full prior ranges (unit cube mapped linearly to each continuous range; switches and discrete parameters map equal slices of [0, 1) to their values). It does not use the E1 screening. The outcome is the mean of `coverage_10y` over 20 replicates.

1. **E4a, Morris screening:** all 98 parameters; SALib `morris` sampling with r = 20 trajectories and 4 levels, i.e. 20 × 99 = 1,980 combinations per cell; 42 cells (7 pathways × 6 settings). Run twice with sampling seeds 147 and 148 (the analysis seed is 146). For each pass, parameters are ranked by μ* averaged over the 42 cells.
2. **Stability rule:** if the two passes' top-12 lists share at least 10 parameters, the first pass's list is used for E4b; otherwise the union of both lists is used.
3. **E4b, Sobol analysis:** the parameters selected in E4a; all other parameters fixed at the `default` column of `code/params.py`. SALib Saltelli sampling without second-order terms (seed 146), base samples N = 256 and N = 512, i.e. N × (k + 2) combinations per cell for k selected parameters. Cells: 7 pathways × {M-A, M-D} = 14 cells. First-order (S1) and total (ST) indices with bootstrap confidence intervals are reported.
4. **Fixed-background check:** at N = 256, for PW0 and PW4 in M-A and M-D, the non-selected parameters are fixed at the 25th and at the 75th percentile of their priors instead of the default (for switches and discrete parameters the percentile is nominal: it selects one of their values).
5. **Interpretation rule:** E4b is a conditional sensitivity analysis. It describes variance contributions of the selected parameters given one fixed background, and cannot show that excluded parameters are unimportant.

## 6. Parameter table

The parameter table has 98 rows: name, distribution type (uniform, discrete or switch), lower and upper bound, default, admissible values for discrete parameters, the settings in which the parameter acts, and the phase (all periods, or projection only). It is given in `data/parameters.csv` and described in `docs/parameters.md`; the values are those in `code/params.py` (checksum in Section 2).

## 7. E4b input list

The two Morris passes (seeds 147 and 148) produced the following top-12 lists, ranked by μ* averaged over the 42 cells (source: `results/e4-sensitivity/morris.json`, fields `top12_pass1`, `top12_pass2`, `overlap`, `chosen_for_sobol`):

- **Pass 1:** `aps_share`, `q_ramp`, `q_pipe`, `h_fs`, `sw_line`, `lam_arr`, `a_line`, `fs5_parent`, `k_cont`, `q_topup`, `pi_scope`, `u0`.
- **Pass 2:** `q_pipe`, `aps_share`, `a_line`, `q_ramp`, `h_fs`, `sw_line`, `lam_arr`, `fs5_parent`, `u0`, `pi_scope`, `g_cost`, `done3_real`.

The lists share 10 parameters. Under the stability rule (Section 5.4, item 2) the pass-1 list was therefore used for E4b, with k = 12.

**Table 7.1.** Rank and mean μ* of the 14 parameters that appear in either list.

| Parameter | Meaning | Pass 1: rank (mean μ*) | Pass 2: rank (mean μ*) |
|---|---|---|---|
| `aps_share` | APS share of a standing local line | 1 (14.73) | 2 (17.57) |
| `q_ramp` | Probability that a site needs new curb ramps | 2 (14.21) | 4 (12.73) |
| `q_pipe` | Probability that a site needs conduit work | 3 (13.04) | 1 (18.58) |
| `h_fs` | Installation rate of signal-project sites | 4 (11.82) | 5 (12.27) |
| `sw_line` | Switch: standing local line from the start | 5 (10.97) | 6 (10.17) |
| `lam_arr` | Arrival rate of new requests | 6 (10.31) | 7 (9.44) |
| `a_line` | Size of a standing local line | 7 (7.87) | 3 (14.33) |
| `fs5_parent` | Switch: five signal-project sites have a parent project | 8 (6.25) | 8 (6.31) |
| `k_cont` | Contingency share of planned cost | 9 (6.18) | 39 (2.11) |
| `q_topup` | Probability that a funding gap receives a top-up | 10 (5.68) | 13 (4.25) |
| `pi_scope` | Probability that a fold-in site is within its parent scope | 11 (5.32) | 10 (5.28) |
| `u0` | Base APS unit cost | 12 (5.25) | 9 (5.33) |
| `done3_real` | Switch: three sites with completed parent work are undelivered | 13 (4.50) | 12 (4.57) |
| `g_cost` | Annual growth of the APS unit cost | 14 (3.27) | 11 (5.08) |

*Note.* Mean μ* is the mean of `cells["<pathway>|<setting>"]["pass<k>"].mu_star["<parameter>"]` over the 42 cells, in ten-year installations (Section 8.1). Values for all 98 parameters, and σ, are in the same file. Ranks below the leading twelve are unstable between passes (for example `k_cont`, 9 and 39).

## 8. Notes on outputs and secondary analyses

### 8.1 Unit of μ*

SALib computes elementary effects on the unit cube and divides by the step Δ = 2/3 (4 levels), so μ* approximates the change in ten-year installations associated with moving a parameter across its full range. Values for switches and for continuous parameters are therefore not directly comparable. This affects interpretation only.

### 8.2 Extraction of PRIM rules

The function `prim_all` (`code/experiments.py`) decides whether a box dimension is restricted by comparing the box limits with the range of the full sample, whereas an unrestricted box limit equals the range of the training half. Nearly every dimension is therefore listed as restricted, and the list is then truncated to its first three entries in column order. The stored rule lists consequently omit binding restrictions (for example `sw_line`) and include near-full-range entries (for example `c_final`). The test-set coverage and density stored by `prim_all` are computed on the whole box, not on the truncated list, and describe the box correctly. The analysis code of `experiments.py` is not changed, so that its output remains reproducible as specified.

Corrected rules are computed by `code/posthoc.py` from the E3 runs, without new simulation. Two differences from the primary procedure must be noted:

1. a dimension is treated as restricted when the box limit lies inside the training-half range, and no truncation is applied;
2. PRIM is re-fitted on a fixed list of 19 candidate inputs (`sw_line`, `a_line`, `aps_share`, `c_final`, `r_other`, `q_dir`, `q_gf`, `q_veto`, `p_deflect`, `b0`, `b_own`, `k0`, `a_local`, `lam_press`, `q_pipe`, `q_ramp`, `u0`, `h_fs`, `lam_arr`) with the same five splits, threshold 0.5 only. Because the candidate set differs, the re-fitted boxes are not identical to the primary boxes, and their test-set coverage and density differ. Both are reported in `docs/results.md`.

### 8.3 Secondary analyses

The following analyses supplement the primary outputs of Section 5. Items 1–5 use only the E3 runs and the E1 accepted combinations and are computed by `code/posthoc.py` (output `results/e3-pathways/posthoc.json`); item 6 requires an additional run (Section 9.3):

1. robustness and funding within five years reported separately for combinations that start without a standing local line (`sw_line` = 0) and with one (`sw_line` = 1). The primary output (`results/e3-pathways/robustness.json`) pools them. The `sw_line` = 0 group corresponds to current conditions (no standing local APS line exists) and is used as the main comparison; the design specification required switch scenarios to be reported as separate groups;
2. the same table restricted to `sw_line` = 0 and `q_dir` < 0.08, which approximately disables the hypothetical reallocation fallback at the end of PW1;
3. one-parameter splits by `q_dir`, `lam_press`, `b_pr`, `k0` and `h_in`;
4. correlations between pairs of history-screened parameters among the E1 accepted combinations;
5. the corrected PRIM rules (Section 8.2);
6. the approval variant for PW4 and PW5 (Section 9.3).

### 8.4 Analyses specified in the design but not performed

The design specification also described (i) a convergence check re-running 5% of combinations with R = 40 and (ii) moment-independent (delta) indices on the history-screened E1 sample. Neither is part of the protocol in Sections 3–7, and neither was performed; no results exist for them.

## 9. Changes to the model after the protocol was fixed

Only `code/model.py` was changed. No parameter was added, renamed or re-ranged, and the inputs, sampling, seeds, replicate counts, sample sizes, criteria and analysis rules of Sections 3–6 are unchanged.

### 9.1 Correction of implementation defects

Ten implementation defects, found when the code was read line by line against its documentation, were corrected. Their nature, the correction and the code lines are listed in `docs/TRACE.md` §5.6. All act only in the projection segment; the historical segment used by E1 is unaffected.

### 9.2 Design revision

Under the original design, a committed HSIP application could start preparation only when the application window opened in July, so that with long preparation times it could never meet the November deadline and the first HSIP step of PW1 and PW4 never occurred. The design was revised so that a committed application may start earlier (`docs/TRACE.md` §5.6). No parameter was added.

### 9.3 Approval variant for PW4 and PW5

**Reason.** In the base design, PW4 has a standing local line from the first month, and PW5 adds one automatically after 24 months if fewer installations than a threshold have occurred. Neither requires approval. PW2 obtains the same kind of line only through a Prop L amendment that can be vetoed or deferred. Part of the advantage of PW4 and PW5 could therefore be produced by the specification rather than by the pathways' other rules. The variant measures that part.

**Rules.** A module-level switch `LINE_APPROVAL` (default `False`) controls the variant. When it is `False`, no additional random number is drawn and PW4 and PW5 follow the base design. When it is `True` and the combination starts without a standing line (`sw_line` = 0), PW4 at the start (after the corridor draws) and PW5 at month t₀ + 24, when its trigger is met, do not open the line directly. They request a Prop L amendment through the same function and parameters as PW2 (`q_veto`, `t_defer`, `th_defer`). If it passes, the line opens. If it is vetoed or deferred beyond the threshold, one General Fund request is decided in the next July (`q_gf`). If that fails, the pathway has no standing line; its other rules continue. Unlike PW2, the variant does not continue to an HSIP repackaging step: PW4 already pursues HSIP from the start, and PW5 does not use HSIP. A failed General Fund request is not recorded as a failure event, as in PW2.

**Tests.** `code/replay_check.py` passes with the switch off and, with the switch set on by a one-off modification of the script (not distributed), with it on. Behavioural tests with the switch on: forced veto with `q_gf` = 0 never opens the line; forced approval opens it at t₀ + 3 + `t_defer`; veto followed by `q_gf` = 1 opens it in the following July.

**Experiment.** `code/e3_variant.py`. Only combinations with `sw_line` = 0 are run (with `sw_line` = 1 the line already exists and the variant changes nothing): PW4 and PW5 × {positive, direct initiation effects zero} × 6 settings, R = 20, with the same parameter combinations and replicate seeds as E3. PW0 is taken from E3. PRIM is not run for the variant.

## 10. Primary and secondary analyses

| Analysis | Role | Output file |
|---|---|---|
| E0 baseline code check | Primary | `results/e0-baseline-check.json` |
| E1 screening and H1 retrospective check | Primary | `results/e1-fit/fit-table.json` |
| E3 robustness and funding, combinations pooled over `sw_line` | Primary | `results/e3-pathways/robustness.json` |
| E2 PRIM boxes (test coverage and density) and CART accuracy | Primary (stored rule lists defective, §8.2) | `results/e2-prim/prim.json` |
| E4a Morris, E4b Sobol, fixed-background check | Primary | `results/e4-sensitivity/morris.json`, `sobol.json` |
| E3 split by `sw_line` (main comparison uses `sw_line` = 0) | Secondary | `results/e3-pathways/posthoc.json` |
| `q_dir` < 0.08 subset; one-parameter splits; screened-parameter correlations | Secondary | `results/e3-pathways/posthoc.json` |
| Corrected PRIM rules | Secondary | `results/e3-pathways/posthoc.json` |
| Approval variant for PW4 and PW5 | Secondary | `results/e3-variant/summary.json` |
| LLM red team | Methodological probe, not used in any result | `results/llm-redteam/` |
