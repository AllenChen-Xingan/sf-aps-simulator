# Results

This document reports every experiment defined in `docs/experiment-protocol.md`, together with the post hoc analyses listed there. All results are **preliminary, uncalibrated scenario projections, not forecasts**. A share reported here is a share of sampled parameter combinations under stated rules; it is not a probability that an outcome will occur in San Francisco.

## 1. How to read this document

1. **Source of every number.** Each table note names the results file and the field from which the numbers are taken. Paths are relative to the package root. Where a number is derived arithmetically from stored values (for example, a weighted average across settings), the note gives the derivation. No number in this document comes from any other source.
2. **Ranges.** Unless stated otherwise, "a–b" is the minimum and maximum across the six settings (M-A, M-B1, M-B2, M-C1, M-C2, M-D). Settings are parallel scenarios; a range is not a confidence interval.
3. **Percentages** are given to one decimal place, computed from the stored proportions without other rounding.
4. **Sampling error.** In the main comparison each setting contains 461–528 combinations (Table 7 note). For a share near 0.9, the binomial standard error at these sample sizes is about 1.3–1.4 percentage points, so differences of a few points between pathways within a setting are not interpretable. Results are therefore read as tiers, not ranks.
5. **Installation counts.** Ten-year installation counts vary widely across combinations and depend on many assumed ranges. They are reported only where needed to interpret a comparison and are not offered as estimates.
6. **Pre-specified and post hoc.** Section headings state whether an analysis was pre-specified in the frozen protocol or is post hoc.
7. **Known implementation defect (†).** Rows marked † are affected by a defect in the General Fund fallback step of PW6 and of the post hoc approval variant (`docs/TRACE.md` §5.6). The frozen results are reported as produced. The direction of the effect is that some runs in which a General Fund request should have been decided never receive it, which can only remove funding opportunities from the affected pathways.

## 2. E0: code check against an earlier baseline (pre-specified)

**Table 1.** Installations predicted for 20 February 2024 to 30 June 2026 by a Markov multi-state model fitted to the request lists from 29 July 2022 to 20 February 2024 (2,000 simulations).

| Implementation | Median | 10th percentile | 90th percentile |
|---|---|---|---|
| Re-implementation (`code/baseline.py`, seed 146) | 20 | 13 | 28 |
| Earlier implementation | 20 | 13 | 27 |

*Source:* `results/e0-baseline-check.json` (fields `ours`, `reference_simulate_py`, `observed`, `match_within_tolerance`).

The re-implementation agrees with the earlier implementation within the pre-specified tolerance (`match_within_tolerance` = true). The number observed in the request lists over the same period is 13, at the 10th percentile of both predictions. E0 checks code. It is not a validation of the agent-based model.

## 3. E1: historical screening and retrospective check (pre-specified)

### 3.1 Acceptance and retrospective check

**Table 2.** Screening against five request-list snapshots (January 2023 to February 2025) and retrospective check (H1) against three later snapshots (August 2025 to June 2026). Base prior width; SG105 exhaustion date 2024-06.

| Setting | Combinations | Accepted | Acceptance (%) | Accepted and passing H1 | H1 pass among accepted (%) |
|---|---|---|---|---|---|
| M-A unassigned responsibility | 2,000 | 462 | 23.1 | 299 | 64.7 |
| M-B1 staffing constraint from 2024 | 2,000 | 451 | 22.6 | 296 | 65.6 |
| M-B2 staffing constraint from 2023 | 2,000 | 309 | 15.4 | 202 | 65.4 |
| M-C1 rising costs | 2,000 | 501 | 25.1 | 346 | 69.1 |
| M-C2 technical constraints | 2,000 | 476 | 23.8 | 317 | 66.6 |
| M-D combined | 2,000 | 525 | 26.2 | 363 | 69.1 |

*Source:* `results/e1-fit/fit-table.json`, `cells["<setting>|base|2024-06"]`, fields `n`, `accepted`, `accept_rate`, `h1_pass_among_accepted`, `h1_pass_rate`.

**Table 3.** Number of combinations (out of 2,000) whose replicate mean is within tolerance for each stock at all five screening snapshots. Base width; exhaustion date 2024-06.

| Setting | C (±6) | N (±4) | Fi (±5) | Fs (±6) | I (±8) |
|---|---|---|---|---|---|
| M-A | 1,987 | 2,000 | 546 | 1,700 | 1,718 |
| M-B1 | 1,979 | 2,000 | 537 | 1,702 | 1,713 |
| M-B2 | 1,998 | 2,000 | 381 | 1,693 | 1,467 |
| M-C1 | 1,997 | 2,000 | 600 | 1,698 | 1,715 |
| M-C2 | 1,992 | 2,000 | 565 | 1,693 | 1,716 |
| M-D | 2,000 | 2,000 | 630 | 1,693 | 1,719 |

*Source:* `results/e1-fit/fit-table.json`, `cells["<setting>|base|2024-06"].pattern_pass`.

The binding constraint is the funded agency-crew stock (Fi), which fell from 22 in July 2022 to 1 in August 2024 and was not replenished (observed stocks: `code/data/inputs.json`, `history.observed_stocks`). Any setting that stops new local funding batches can reproduce that pattern.

### 3.2 Sensitivity of screening to the exhaustion date and to prior width

**Table 4.** Acceptance (%) by assumed exhaustion date of the earlier dedicated programme (SG105). Base width.

| Setting | 2023-06 | 2023-12 | 2024-02 | 2024-06 | 2024-12 |
|---|---|---|---|---|---|
| M-A | 24.9 | 24.9 | 24.1 | 23.1 | 23.1 |
| M-B1 | 22.6 | 22.6 | 22.6 | 22.6 | 22.6 |
| M-B2 | 15.4 | 15.4 | 15.4 | 15.4 | 15.4 |
| M-C1 | 25.1 | 25.1 | 25.1 | 25.1 | 25.1 |
| M-C2 | 23.8 | 23.8 | 23.8 | 23.8 | 23.8 |
| M-D | 27.2 | 27.2 | 26.8 | 26.2 | 26.2 |

*Source:* `results/e1-fit/fit-table.json`, `cells["<setting>|base|<date>"].accept_rate`.

**Table 5.** Acceptance and H1 pass rate (%) by prior width. Exhaustion date 2024-06. Narrow, base and wide: 2,000 combinations each; wide independent rate priors: 400 combinations.

| Setting | Narrow: accepted | Narrow: H1 | Base: accepted | Base: H1 | Wide: accepted | Wide: H1 | Independent rate priors: accepted | Independent rate priors: H1 |
|---|---|---|---|---|---|---|---|---|
| M-A | 24.3 | 91.2 | 23.1 | 64.7 | 7.0 | 44.3 | 11.8 | 53.2 |
| M-B1 | 24.4 | 90.6 | 22.6 | 65.6 | 6.3 | 46.0 | 11.5 | 56.5 |
| M-B2 | 26.6 | 90.8 | 15.4 | 65.4 | 5.1 | 49.5 | 7.8 | 54.8 |
| M-C1 | 25.1 | 89.7 | 25.1 | 69.1 | 8.1 | 49.1 | 12.2 | 53.1 |
| M-C2 | 24.4 | 89.6 | 23.8 | 66.6 | 7.0 | 46.4 | 11.5 | 52.2 |
| M-D | 25.1 | 90.6 | 26.2 | 69.1 | 8.0 | 48.4 | 12.5 | 46.0 |

*Source:* `results/e1-fit/fit-table.json`, `cells["<setting>|<width>|2024-06"]`, with `<width>` = `narrow`, `base`, `wide`, `wide_rates`.

### 3.3 Parameter values among accepted combinations

**Table 6.** Median (10th–90th percentile) of selected parameters among combinations accepted under the base width, pooled over the five exhaustion dates.

| Parameter | M-A | M-B1 | M-B2 | M-C1 | M-C2 | M-D |
|---|---|---|---|---|---|---|
| `b0` | −5.08 (−6.52 to −3.43) | −5.13 (−6.55 to −3.43) | −4.96 (−6.51 to −3.32) | −5.01 (−6.52 to −3.43) | −5.11 (−6.53 to −3.40) | −4.96 (−6.47 to −3.38) |
| `k0` | 1.27 (0.889–2.60) | 1.26 (0.893–2.58) | 1.48 (0.997–2.64) | 1.28 (0.890–2.60) | 1.31 (0.890–2.59) | 1.33 (0.889–2.64) |
| `phi` | 0.446 (0.097–0.816) | 0.445 (0.091–0.811) | 0.304 (0.055–0.614) | 0.444 (0.091–0.810) | 0.463 (0.102–0.813) | 0.464 (0.097–0.811) |
| `h_in` | 0.855 (0.671–1.29) | 0.869 (0.678–1.28) | 0.852 (0.671–1.25) | 0.844 (0.667–1.27) | 0.848 (0.671–1.28) | 0.831 (0.653–1.27) |
| `h_fs` | 0.216 (0.140–0.294) | 0.216 (0.139–0.293) | 0.217 (0.139–0.294) | 0.217 (0.141–0.293) | 0.212 (0.139–0.290) | 0.212 (0.140–0.291) |

*Source:* `results/e1-fit/fit-table.json`, `needed_parameter_values["<setting>"]["<parameter>"]` (10th, 50th and 90th percentiles). The same field also holds `b_own`, `p_deflect`, `m_b`, `m_c`, `g_cost`, `tau` and `a_local`.

### 3.4 Reading of E1

1. Acceptance under the base width is 15.4–26.2%, and 64.7–69.1% of accepted combinations also pass the retrospective check. Five of the six settings lie between 22.6% and 26.2%. The request lists therefore do not discriminate between these explanations.
2. M-B2 (staffing constraint from 2023) has the lowest acceptance under the base and wide widths and under the independent rate priors, but the highest under the narrow width (26.6%). Its accepted combinations require a smaller capacity reduction (`phi` median 0.304, against 0.444–0.464 elsewhere).
3. Acceptance is almost unchanged across exhaustion dates from 2023-06 to 2024-12 (Table 4).
4. The percentiles of accepted parameters (Table 6) lie close to the prior ranges (`docs/parameters.md`): the history constrains these parameters only weakly.
5. Narrow priors raise the H1 pass rate to 89.6–91.2%, wide priors lower it to 44.3–49.5%. With independent priors for the two reused installation rates, acceptance falls to 7.8–12.5% and the H1 pass rate to 46.0–56.5%.

## 4. E3: pathway comparison

### 4.1 Main comparison: combinations without a standing local line at the start (post hoc grouping)

The frozen output pools combinations with and without a standing local line at the start (`sw_line` = 0 or 1). Because no standing local APS line exists today, the main comparison uses the `sw_line` = 0 group (Section 8.3 of the protocol). The pooled frozen output is reported in Section 4.3.

**Table 7.** Main comparison. Share of combinations in which the pathway's mean ten-year installations exceed current practice (PW0) under the same combination and seeds; share of runs with funding within five years.

| Pathway | Outperforms PW0 (%) | Outperforms PW0, direct initiation effects zero (%) | Funding within five years (%) | Funding within five years, direct initiation effects zero (%) |
|---|---|---|---|---|
| PW5 design standards (frozen design) | 94.6–97.3 | 95.4–97.3 | 91.8–95.8 | 91.8–95.8 |
| PW4 crossing-specific allocation (frozen design) | 92.2–97.5 | 95.7–98.8 | 86.8–91.2 | 86.8–91.2 |
| PW6 existing hardware programme † | 93.0–95.8 | 94.8–96.9 | 73.2–81.1 | 73.0–77.7 |
| PW5 design standards with approval (post hoc variant) † | 91.1–95.2 | 92.8–96.7 | 75.2–87.6 | 75.0–84.2 |
| PW4 crossing-specific allocation with approval (post hoc variant) † | 90.7–93.4 | 93.6–94.8 | 50.4–65.5 | 50.1–58.0 |
| PW1 HSIP-first | 89.6–94.0 | 91.5–95.2 | 61.9–74.2 | 61.6–68.2 |
| PW2 local-first | 85.5–90.5 | 86.8–92.6 | 55.2–69.9 | 55.0–62.9 |
| PW3 accountability-first | 66.9–88.6 | 44.5–80.5 | 35.6–67.8 | 11.7–36.0 |
| PW0 current practice | — | — | 3.2–30.8 | 1.9–9.8 |

*Sources:* frozen pathways: `results/e3-pathways/posthoc.json`, `by_sw_line.line0_status_quo["<pathway>|positive"]` and `["<pathway>|zero_direct"]`, fields `share_better` and `P_money`. Variant rows: `results/e3-variant/summary.json`, `table["<pathway>|positive"]` and `["<pathway>|zero_direct"]`, fields `share_better_than_PW0` and `P_money`. Combinations per setting: M-A 518, M-B1 517, M-B2 502, M-C1 483, M-C2 461, M-D 528 (`results/e3-variant/summary.json`, `by_mech[...].n_sets`; `results/web/meta.json`, `n_param_sets_by_mechanism`). The fields `frozen_share_better` and `frozen_P_money` in `results/e3-variant/summary.json` reproduce the frozen PW4 and PW5 rows of this table exactly.

**Table 8.** Outperforms PW0 (%), by setting. Main comparison, positive control.

| Pathway | M-A | M-B1 | M-B2 | M-C1 | M-C2 | M-D |
|---|---|---|---|---|---|---|
| PW1 | 94.0 | 91.1 | 91.4 | 90.7 | 89.6 | 92.6 |
| PW2 | 90.5 | 88.2 | 87.2 | 89.6 | 85.5 | 88.8 |
| PW3 | 88.6 | 82.8 | 86.5 | 66.9 | 86.3 | 71.8 |
| PW4 (frozen design) | 96.9 | 92.5 | 92.2 | 96.7 | 93.3 | 97.5 |
| PW5 (frozen design) | 97.3 | 95.5 | 94.6 | 96.7 | 94.6 | 96.2 |
| PW6 † | 95.8 | 95.0 | 93.0 | 94.2 | 93.3 | 94.5 |
| PW4 with approval (post hoc) † | 93.2 | 91.7 | 91.6 | 93.4 | 90.7 | 93.0 |
| PW5 with approval (post hoc) † | 95.2 | 94.6 | 93.6 | 93.2 | 91.1 | 92.8 |

*Sources:* `results/e3-pathways/posthoc.json`, `by_sw_line.line0_status_quo["<pathway>|positive"].by_mech`; `results/e3-variant/summary.json`, `table["<pathway>|positive"].by_mech[...].share_better_than_PW0`.

**Table 9.** Share of runs (%) reaching each pathway step. Main comparison, positive control, 60,180 runs per pathway (3,009 combinations × 20 replicates).

| Pathway | Step reached | Runs (%) |
|---|---|---|
| PW1 | Repackaged application in the next HSIP cycle | 97.0 |
| PW1 | Prop L amendment | 84.9 |
| PW1 | Hypothetical management reallocation | 46.5 |
| PW2 | General Fund request | 55.0 |
| PW2 | HSIP repackaging | 41.2 |
| PW3 | Structured negotiation | 96.5 |
| PW3 | Litigation | 64.6 |
| PW5 | Standing local line (added by trigger) | 99.7 |
| PW6 † | Prop L amendment | 76.2 |
| PW6 † | General Fund request | 41.6 |
| PW6 † | HSIP repackaging | 28.3 |
| PW4 with approval (post hoc) † | Prop L amendment | 100.0 |
| PW4 with approval (post hoc) † | General Fund request | 55.0 |
| PW5 with approval (post hoc) † | Prop L amendment | 99.7 |
| PW5 with approval (post hoc) † | General Fund request | 54.9 |

*Source:* `results/web/pathways.json`, `path_reach["<pathway>"].nodes` and `variant_path_reach["<pathway>-approval"].nodes` (node names `C14_repack`, `PropL_amendment`, `Director_or_GF`, `GF_request`, `HSIP_repack`, `structured_negotiation`, `lawsuit`, `local_line`); `runs` = 60,180.

### 4.2 Reading of the main comparison

1. Under the frozen design, PW5, PW4 and PW6 form the leading tier (92.2–97.5% of combinations outperform current practice), and their order changes between settings (Table 8).
2. PW1 follows (89.6–94.0%), then PW2 (85.5–90.5%). PW3 is lowest in five of six settings; in M-C2 it lies above PW2 (86.3% against 85.5%).
3. With the approval variant, PW4 and PW5 outperform current practice in 90.7–95.2% of combinations, the same tier as PW6 and PW1. Their funding within five years falls from 86.8–91.2% to 50.4–65.5% (PW4) and from 91.8–95.8% to 75.2–87.6% (PW5). In the model, therefore, most of the advantage of PW4 and PW5 in installations comes from their other rules, whereas most of PW4's advantage in early funding comes from the line it receives without approval. In the variant, the General Fund fallback is reached in 55.0% (PW4) and 54.9% (PW5) of runs, i.e. the Prop L amendment fails in those runs (Table 9).
4. Setting the direct initiation effects to zero changes PW3 most (from 66.9–88.6% to 44.5–80.5%; funding within five years from 35.6–67.8% to 11.7–36.0%). The remainder of PW3's effect operates through its other channels, doubled pressure frequency and escalation of enforcement, both of which act only on the probability of starting an application (`docs/ODD+D.md`).
5. Median ten-year installations per combination range from 22.75–25.28 (PW0) to 33.28–39.08 (PW4) across settings (`results/e3-pathways/posthoc.json`, `by_sw_line.line0_status_quo["<pathway>|positive"].median_cov10`). These are reported for scale only.

### 4.3 Frozen output: all combinations pooled (pre-specified)

**Table 10.** Pooled over `sw_line` = 0 and 1 (1,000 combinations per setting), as stored by the frozen code.

| Pathway | Outperforms PW0 (%) | Outperforms PW0, direct initiation effects zero (%) | Funding within five years (%) | Maximum regret (installations) |
|---|---|---|---|---|
| PW1 HSIP-first | 79.3–84.2 | 80.6–85.2 | 74.0–83.8 | 34.15–69.25 |
| PW2 local-first | 68.9–74.3 | 69.8–75.4 | 68.6–80.3 | 34.95–58.15 |
| PW3 accountability-first | 53.2–71.0 | 35.9–65.3 | 58.6–79.1 | 39.50–88.50 |
| PW4 crossing-specific allocation | 82.1–86.9 | 82.7–87.6 | 85.1–90.6 | 16.00–34.15 |
| PW5 design standards | 81.6–87.8 | 80.8–88.2 | 91.1–96.0 | 14.35–30.55 |
| PW6 existing hardware programme † | 76.0–81.0 | 76.7–81.4 | 80.7–87.8 | 32.60–60.05 |
| PW0 current practice | — | — | 40.6–61.6 | 45.40–88.50 |

*Source:* `results/e3-pathways/robustness.json`, entries with `control` = `positive` (and `zero_direct` for the second column), fields `share_better_than_PW0`, `P_money_mean`, `max_regret`; range over the six settings. `results/e3-pathways/posthoc.json`, `by_sw_line.pooled`, reproduces the first three columns exactly.

The pooled output counts combinations that already have a standing local line as current practice. Current practice then has funding within five years in 40.6–61.6% of runs, which does not describe current conditions. For this reason the pooled table is not used as the main comparison.

### 4.4 Combinations that already have a standing local line (post hoc grouping)

**Table 11.** `sw_line` = 1 (not current conditions; 472–539 combinations per setting).

| Pathway | Outperforms PW0 (%) | Outperforms PW0, direct initiation effects zero (%) | Funding within five years (%) |
|---|---|---|---|
| PW1 HSIP-first | 70.5–73.7 | 69.9–75.1 | 87.5–93.7 |
| PW2 local-first | 52.0–56.8 | 51.3–57.7 | 83.5–91.8 |
| PW3 accountability-first | 40.4–52.1 | 27.9–50.6 | 82.5–91.5 |
| PW4 crossing-specific allocation | 70.1–75.4 | 69.9–77.2 | 83.1–91.6 |
| PW5 design standards | 69.7–78.3 | 68.3–78.4 | 90.3–96.8 |
| PW6 existing hardware programme † | 58.8–65.1 | 60.4–64.7 | 89.1–94.8 |
| PW0 current practice | — | — | 82.5–91.4 |

*Source:* `results/e3-pathways/posthoc.json`, `by_sw_line.line1`. Minimum combinations per setting: `n_sets_per_mech` = 472; per-setting counts are 1,000 minus the counts in the Table 7 note.

When a standing line already exists, current practice already receives funding within five years in 82.5–91.4% of runs, and every pathway's advantage over it is smaller.

### 4.5 Accountability-first and the standing line, pooled over settings (post hoc)

**Table 12.** Pooled over the six settings.

| Group | PW3 outperforms PW0 (%) | PW2 outperforms PW0 (%) | PW0 funding within five years (%) | PW3 funding within five years (%) |
|---|---|---|---|---|
| No standing line at the start (3,009 combinations) | 80.5 | 88.4 | 18.0 | 55.8 |
| Standing line at the start (2,991 combinations) | 46.0 | 53.9 | 87.7 | 87.7 |

*Derivation:* weighted averages over settings, weights equal to the number of combinations per setting. No-line group: `results/web/robustness.json`, `table` (fields `share_better_than_PW0`, `P_money_flows_5y_mean`, `n_sets`). Standing-line group: from `table_pooled_sw_line` (1,000 combinations per setting) minus the no-line group, i.e. (1,000 × pooled value − n₀ × no-line value) / (1,000 − n₀). The same quantities are plotted in `results/figures/fig2-accountability-by-standing-line.png`.

In the model, accountability-first adds most where no standing source of local money exists; where one exists, its additional effect is small.

### 4.6 PW1 with the hypothetical reallocation step approximately disabled (post hoc)

**Table 13.** `sw_line` = 0 and `q_dir` < 0.08 (at least 44 combinations per setting).

| Pathway | Outperforms PW0 (%) | Funding within five years (%) |
|---|---|---|
| PW5 design standards | 93.2–98.3 | 95.1–98.2 |
| PW4 crossing-specific allocation | 90.9–97.9 | 85.7–96.9 |
| PW6 existing hardware programme † | 88.6–98.1 | 75.4–83.9 |
| PW2 local-first | 81.8–94.4 | 56.6–72.2 |
| PW1 HSIP-first | 75.0–88.6 | 50.6–69.8 |
| PW3 accountability-first | 63.0–93.2 | 40.3–71.2 |
| PW0 current practice | — | 2.2–33.4 |

*Source:* `results/e3-pathways/posthoc.json`, `line0_q_dir_lt_0.08["<pathway>|positive"]`; minimum combinations per setting `n_sets_per_mech` = 44.

The final step of PW1, a one-time reallocation of `a_line` with probability `q_dir`, has no documentary support (`docs/ODD+D.md`). With that step approximately disabled, PW1 falls into the range of PW2. The subset is small, so these ranges are noisy.

## 5. One-parameter splits and correlations (post hoc)

The splits below group all E3 combinations (both values of `sw_line`, positive control) by one parameter while all other parameters vary. They are marginal splits, not ceteris paribus comparisons.

**Table 14.** Advocacy pressure frequency `lam_press` (events per year).

| Bin | PW0 funding within five years (%) | PW3 outperforms PW0 (%) | PW3 funding within five years (%) | PW1 outperforms (%) | PW4 outperforms (%) | PW5 outperforms (%) |
|---|---|---|---|---|---|---|
| [0, 0.1) | 42.1–61.3 | 53.2–70.6 | 59.4–76.3 | 78.4–86.9 | 82.9–87.4 | 78.6–91.0 |
| [0.1, 0.25) | 43.2–62.4 | 52.6–67.3 | 60.3–80.4 | 78.4–85.6 | 80.2–87.5 | 83.6–87.0 |
| [0.25, 0.4) | 39.8–62.7 | 55.0–77.1 | 59.7–81.5 | 77.5–86.8 | 78.7–86.6 | 79.6–90.3 |
| [0.4, 0.5] | 36.9–62.7 | 51.7–67.9 | 53.8–78.8 | 77.7–82.4 | 78.3–88.3 | 83.4–87.2 |

**Table 15.** Internal crew capacity `k0` (installations per month).

| Bin | PW0 funding within five years (%) | PW0 median 10-year installations | PW3 outperforms PW0 (%) | PW4 median 10-year installations | PW5 median 10-year installations |
|---|---|---|---|---|---|
| [0.5, 1.0) | 41.3–63.3 | 26.4–31.1 | 49.1–71.0 | 33.8–40.6 | 33.7–41.4 |
| [1.0, 2.0) | 41.1–61.2 | 25.5–29.5 | 53.2–74.4 | 33.4–38.1 | 32.1–38.8 |
| [2.0, 3.0] | 39.4–62.9 | 25.4–29.5 | 57.5–64.6 | 32.1–38.6 | 31.7–39.5 |

**Table 16.** Installation rate of funded agency-crew crossings `h_in` (per year).

| Bin | PW0 funding within five years (%) | PW0 median 10-year installations | PW3 median 10-year installations | PW3 funding within five years (%) | PW4 funding within five years (%) |
|---|---|---|---|---|---|
| [0.59, 0.85) | 37.9–60.8 | 25.4–28.8 | 26.8–32.2 | 58.6–77.8 | 84.8–90.1 |
| [0.85, 1.15) | 42.1–61.1 | 25.4–29.5 | 27.7–33.4 | 59.4–78.3 | 84.0–94.1 |
| [1.15, 1.41] | 45.0–67.2 | 26.8–30.6 | 27.8–36.0 | 56.6–85.1 | 87.0–94.8 |

*Sources (Tables 14–16):* `results/e3-pathways/posthoc.json`, `splits["<parameter>[<low>,<high>)"]["<pathway>"]`, fields `P_money`, `share_better`, `median_cov10`. The same field holds the splits by `b_pr` and `q_dir`.

**Pressure effect per event `b_pr`.** In the three bins [0, 0.5), [0.5, 1.5) and [1.5, 2.0], PW0 funding within five years is 40.3–65.4%, 42.0–63.2% and 37.8–58.8%, and PW3 outperforms PW0 in 51.0–73.5%, 53.3–70.7% and 54.5–69.0% of combinations (same source, `splits["b_pr[...]"]`).

**Correlations among history-screened parameters** (13,759 entries of the E1 accepted pool, all settings pooled; they represent 671 distinct combinations, because the six settings screen the same draws and a combination accepted at several exhaustion dates appears once per acceptance): `lam_press`–`b0` −0.06; `lam_press`–`b_pr` −0.052; `b_pr`–`b0` 0.02; `k0`–`h_in` −0.704; `k0`–`b0` −0.012; `k0`–`phi` 0.071; `h_in`–`b0` −0.003; `p_deflect`–`b0` −0.022 (`results/e3-pathways/posthoc.json`, `screened_param_correlations`).

**Reading.** Across the sampled range, more frequent or stronger advocacy pressure shows no trend in PW0's funding or in PW3's advantage. Pressure is nearly uncorrelated with the baseline initiation propensity among screened combinations, so this is not an artefact of screening. Higher crew capacity also shows no gain, but this split is confounded: screening induces a strong negative correlation between `k0` and `h_in` (−0.704), because the request lists constrain only their joint output. The unconfounded evidence on these parameters comes from E4a (Section 7.1), where neither is among the leading twelve. In the model, pressure and ownership act only on the probability of starting an application, and crew capacity is only a monthly ceiling; these results describe that model structure and are not evidence that pressure or capacity are unimportant in practice.

## 6. E2: conditions under which funding flows

### 6.1 Frozen PRIM output (pre-specified)

**Table 17.** Test-set coverage and density of the frozen PRIM boxes and test-set accuracy of the depth-3 CART cross-check; range over five splits.

| Pathway | Threshold | Test coverage | Test density | CART test accuracy |
|---|---|---|---|---|
| PW0 | 0.25 | 0.573–0.628 | 0.981–0.988 | 0.821–0.832 |
| PW0 | 0.5 | 0.687–0.750 | 0.970–0.979 | 0.885–0.907 |
| PW0 | 0.75 | 0.678–0.812 | 0.939–0.963 | 0.921–0.938 |
| PW1 | 0.25 | 0.399–0.715 | 0.973–0.996 | 0.894–0.913 |
| PW1 | 0.5 | 0.388–0.430 | 0.983–0.988 | 0.855–0.877 |
| PW1 | 0.75 | 0.482–0.508 | 0.960–0.975 | 0.791–0.810 |
| PW2 | 0.25 | 0.404–0.695 | 0.947–0.991 | 0.896–0.914 |
| PW2 | 0.5 | 0.441–0.481 | 0.972–0.984 | 0.826–0.847 |
| PW2 | 0.75 | 0.451–0.539 | 0.942–0.963 | 0.785–0.807 |
| PW3 | 0.25 | 0.440–0.480 | 0.981–0.986 | 0.831–0.843 |
| PW3 | 0.5 | 0.480–0.527 | 0.967–0.975 | 0.785–0.797 |
| PW3 | 0.75 | 0.461–0.549 | 0.948–0.963 | 0.748–0.777 |
| PW4 | 0.25 | 0.691–0.790 | 0.984–0.991 | 0.955–0.963 |
| PW4 | 0.5 | 0.643–0.756 | 0.981–0.985 | 0.943–0.949 |
| PW4 | 0.75 | 0.483–0.665 | 0.972–0.991 | 0.922–0.930 |
| PW5 | 0.25 | 0.644–0.749 | 0.989–0.993 | 0.965–0.972 |
| PW5 | 0.5 | 0.580–0.757 | 0.976–0.989 | 0.942–0.954 |
| PW5 | 0.75 | 0.542–0.599 | 0.980–0.987 | 0.913–0.930 |
| PW6 † | 0.25 | 0.641–0.749 | 0.986–0.991 | 0.964–0.969 |
| PW6 † | 0.5 | 0.400–0.766 | 0.947–0.990 | 0.913–0.925 |
| PW6 † | 0.75 | 0.401–0.456 | 0.969–0.977 | 0.820–0.834 |

*Source:* `results/e2-prim/prim.json`, `["<pathway>"][k]`, fields `threshold`, `coverage_test`, `density_test`, `cart_test_accuracy`. CART accuracy over all 105 pathway–threshold–split entries: 0.748–0.972. The `rules` field of this file is not reported, because its extraction was defective (protocol §8.2).

### 6.2 Corrected PRIM rules (post hoc)

**Table 18.** Corrected rules at threshold 0.5. Each row is one of five 50/50 splits; restrictions are given as box bounds and as the share of the training range that the restriction removes.

| Pathway | Split | Restrictions | Test coverage | Test density |
|---|---|---|---|---|
| PW0 | 0 | `sw_line` = 1; `aps_share` ≥ 0.0423 (8.4%); `q_ramp` ≤ 0.963 (3.7%) | 0.813 | 0.968 |
| PW0 | 1 | `sw_line` = 1; `aps_share` ≥ 0.0702 (14.0%); `q_ramp` ≤ 0.962 (3.8%) | 0.769 | 0.978 |
| PW0 | 2 | `sw_line` = 1; `aps_share` ≥ 0.0444 (8.9%); `q_pipe` ≤ 0.952 (4.8%) | 0.825 | 0.956 |
| PW0 | 3 | `sw_line` = 1; `aps_share` ≥ 0.0702 (14.0%); `q_pipe` ≤ 0.948 (5.2%) | 0.779 | 0.980 |
| PW0 | 4 | `sw_line` = 1; `aps_share` ≥ 0.0619 (12.3%); `q_ramp` ≤ 0.956 (4.5%) | 0.795 | 0.977 |
| PW1 | 0 | `sw_line` = 1; `aps_share` ≥ 0.0475 (9.5%); `q_pipe` ≤ 0.948 (5.2%) | 0.502 | 0.977 |
| PW1 | 1 | `sw_line` = 1; `aps_share` ≥ 0.0723 (14.4%); `q_pipe` ≤ 0.948 (5.2%) | 0.474 | 0.984 |
| PW1 | 2 | `sw_line` = 1; `aps_share` ≥ 0.0472 (9.4%); `q_pipe` ≤ 0.953 (4.7%) | 0.515 | 0.976 |
| PW1 | 3 | `sw_line` = 1; `aps_share` ≥ 0.0733 (14.6%); `q_pipe` ≤ 0.948 (5.2%) | 0.473 | 0.987 |
| PW1 | 4 | `sw_line` = 1; `aps_share` ≥ 0.0850 (16.9%); `q_ramp` ≤ 0.959 (4.1%) | 0.471 | 0.991 |
| PW2 | 0 | `sw_line` = 1; `aps_share` ≥ 0.0475 (9.5%); `q_pipe` ≤ 0.951 (4.9%) | 0.524 | 0.968 |
| PW2 | 1 | `sw_line` = 1; `aps_share` ≥ 0.0713 (14.2%); `q_pipe` ≤ 0.948 (5.2%) | 0.493 | 0.974 |
| PW2 | 2 | `sw_line` = 1; `aps_share` ≥ 0.0472 (9.4%); `q_pipe` ≤ 0.953 (4.7%) | 0.536 | 0.963 |
| PW2 | 3 | `sw_line` = 1; `aps_share` ≥ 0.0740 (14.7%); `q_pipe` ≤ 0.948 (5.2%) | 0.496 | 0.980 |
| PW2 | 4 | `sw_line` = 1; `aps_share` ≥ 0.0454 (9.0%); `q_pipe` ≤ 0.948 (5.2%) | 0.535 | 0.968 |
| PW3 | 0 | `sw_line` = 1; `aps_share` ≥ 0.0446 (8.9%); `a_local` ≥ 23,613 (4.1%) | 0.563 | 0.954 |
| PW3 | 1 | `sw_line` = 1; `aps_share` ≥ 0.0702 (14.0%); `q_ramp` ≤ 0.962 (3.8%) | 0.537 | 0.978 |
| PW3 | 2 | `sw_line` = 1; `aps_share` ≥ 0.0467 (9.3%); `q_pipe` ≤ 0.953 (4.7%) | 0.580 | 0.958 |
| PW3 | 3 | `sw_line` = 1; `aps_share` ≥ 0.0720 (14.4%); `a_local` ≥ 24,073 (4.1%) | 0.544 | 0.972 |
| PW3 | 4 | `sw_line` = 1; `aps_share` ≥ 0.0634 (12.6%); `a_local` ≥ 23,613 (4.1%) | 0.562 | 0.963 |
| PW4 | 0 | `aps_share` ≥ 0.0917 (18.3%); `q_pipe` ≤ 0.951 (4.9%); `q_ramp` ≤ 0.895 (10.6%) | 0.746 | 0.997 |
| PW4 | 1 | `aps_share` ≥ 0.0917 (18.3%); `q_pipe` ≤ 0.950 (5.0%); `q_ramp` ≤ 0.915 (8.6%) | 0.775 | 0.993 |
| PW4 | 2 | `aps_share` ≥ 0.0911 (18.2%); `q_pipe` ≤ 0.951 (4.9%); `q_ramp` ≤ 0.925 (7.6%) | 0.801 | 0.994 |
| PW4 | 3 | `aps_share` ≥ 0.0736 (14.7%); `q_pipe` ≤ 0.948 (5.2%); `q_ramp` ≤ 0.915 (8.6%) | 0.801 | 0.992 |
| PW4 | 4 | `aps_share` ≥ 0.1083 (21.6%); `q_pipe` ≤ 0.875 (12.5%); `q_ramp` ≤ 0.911 (9.0%) | 0.687 | 0.998 |
| PW5 | 0 | `aps_share` ≥ 0.0916 (18.3%); `q_pipe` ≤ 0.951 (4.9%); `q_ramp` ≤ 0.917 (8.3%) | 0.735 | 0.993 |
| PW5 | 1 | `aps_share` ≥ 0.0720 (14.4%); `q_pipe` ≤ 0.948 (5.2%); `q_ramp` ≤ 0.915 (8.6%) | 0.758 | 0.993 |
| PW5 | 2 | `aps_share` ≥ 0.1134 (22.7%); `q_pipe` ≤ 0.896 (10.4%); `q_ramp` ≤ 0.895 (10.6%) | 0.655 | 0.997 |
| PW5 | 3 | `aps_share` ≥ 0.0736 (14.7%); `q_pipe` ≤ 0.948 (5.2%); `q_ramp` ≤ 0.917 (8.3%) | 0.755 | 0.995 |
| PW5 | 4 | `aps_share` ≥ 0.0909 (18.1%); `q_pipe` ≤ 0.951 (4.9%); `q_ramp` ≤ 0.913 (8.7%) | 0.725 | 0.996 |
| PW6 † | 0 | `aps_share` ≥ 0.0682 (13.6%); `q_pipe` ≤ 0.951 (4.9%); `q_ramp` ≤ 0.961 (3.9%) | 0.827 | 0.952 |
| PW6 † | 1 | `aps_share` ≥ 0.0721 (14.4%); `q_pipe` ≤ 0.948 (5.2%); `q_ramp` ≤ 0.961 (3.9%) | 0.814 | 0.956 |
| PW6 † | 2 | `aps_share` ≥ 0.0697 (13.9%); `q_pipe` ≤ 0.951 (4.9%); `q_ramp` ≤ 0.964 (3.6%) | 0.834 | 0.957 |
| PW6 † | 3 | `aps_share` ≥ 0.0730 (14.5%); `q_pipe` ≤ 0.948 (5.2%); `q_ramp` ≤ 0.961 (3.9%) | 0.807 | 0.957 |
| PW6 † | 4 | `aps_share` ≥ 0.0664 (13.2%); `q_pipe` ≤ 0.884 (11.6%); `q_ramp` ≤ 0.955 (4.5%) | 0.776 | 0.963 |

*Source:* `results/e3-pathways/posthoc.json`, `prim_full_rules_thr0.5["<pathway>"][split]`, fields `rules` (`param`, `low`, `high`, `trimmed_share_of_range`), `coverage_test`, `density_test`. Bounds are rounded to three or four significant figures; the unrounded values are in the file. `sw_line` is a 0/1 switch, so the bound 0.5–1 means `sw_line` = 1. For `q_pipe` and `q_ramp` only the upper bound restricts (the lower bound equals the training-half minimum); for `a_local` only the lower bound restricts.

**Reading.**

1. For PW0–PW3, every box requires a standing local line and an APS share of that line of at least 4.2–8.5% (`aps_share` lower bounds 0.0423–0.0850). The third restriction removes only 3.7–5.2% of the range of `q_ramp`, `q_pipe` or `a_local`. Test coverage is 0.769–0.825 for PW0 and 0.471–0.580 for PW1–PW3, which have other routes to funding, such as federal awards.
2. For PW4–PW6 (a line provided by design, or an existing hardware programme), every box requires an APS share of at least 6.6–11.3% (lower bounds 0.0664–0.1134) and trims the extreme combinations in which almost all costly crossings need conduit or curb-ramp work (3.6–12.5% of those ranges). Test coverage is 0.655–0.834.
3. Test density is 0.952–0.998 for all boxes.
4. The size of the standing line (`a_line`, sampled between $0.5 million and $2 million per year) does not appear in any corrected box.
5. These boxes were re-fitted on a different candidate set from the frozen boxes (protocol §8.2), so their coverage and density differ from Table 17. PRIM was not run for the approval variant.

## 7. E4: global sensitivity analysis (pre-specified)

E4 samples the full prior ranges without historical screening. It describes which inputs drive ten-year installations in the model, not in the screened scenarios of E3.

### 7.1 E4a: Morris screening

The two passes' top-12 lists share 10 parameters; the first-pass list was used for E4b. The list and the mean μ* of both passes are given in `docs/experiment-protocol.md` §7 (source `results/e4-sensitivity/morris.json`, fields `top12_pass1`, `top12_pass2`, `overlap`, `chosen_for_sobol`, and `cells["<pathway>|<setting>"]["pass1"|"pass2"].mu_star`).

**Table 19.** Rank by mean μ* (out of 98) of parameters that represent accountability, pressure and capacity.

| Parameter | Meaning | Pass 1: rank (mean μ*) | Pass 2: rank (mean μ*) |
|---|---|---|---|
| `b_own` | Effect of a named owner on initiation | 24 (2.35) | 69 (1.87) |
| `k0` | Internal crew capacity | 20 (2.54) | 53 (1.94) |
| `c_final` | HSIP selection threshold | 21 (2.45) | 17 (2.71) |
| `q_dir` | Probability of the hypothetical reallocation | 33 (2.13) | 36 (2.05) |
| `b_enf` | Effect of external enforcement on initiation | 62 (1.81) | 45 (2.01) |
| `b_spec` | Effect of a specified deadline on initiation | 52 (1.87) | 56 (1.92) |
| `b_ov` | Effect of oversight on initiation | 71 (1.78) | 72 (1.86) |
| `lam_press` | Advocacy pressure frequency | 75 (1.76) | 93 (1.63) |
| `b_pr` | Effect of a pressure event on initiation | 97 (1.59) | 88 (1.73) |

*Derivation:* mean of `cells[...]["pass<k>"].mu_star["<parameter>"]` over the 42 cells of `results/e4-sensitivity/morris.json`, ranked in decreasing order. μ* approximates the change in ten-year installations from moving a parameter across its range (protocol §8.1).

None of these parameters is among the leading twelve. Two reasons apply. First, the model gives them narrow channels: ownership, deadlines, oversight, pressure and enforcement act only on the probability of starting an application, and crew capacity is a monthly ceiling that binds rarely when few crossings are funded. Second, μ* is averaged over 42 cells, which dilutes parameters that act in only some settings. This is not evidence that these factors are unimportant in practice.

### 7.2 E4b: Sobol indices

**Table 20.** Total (ST) and first-order (S1) indices, simple mean over the 14 default-background cells (7 pathways × {M-A, M-D}).

| Parameter | ST, N = 512 | S1, N = 512 | Mean 95% half-width of ST, N = 512 | ST, N = 256 | S1, N = 256 |
|---|---|---|---|---|---|
| `aps_share` | 0.329 | 0.145 | 0.069 | 0.329 | 0.146 |
| `q_pipe` | 0.215 | 0.106 | 0.049 | 0.194 | 0.144 |
| `sw_line` | 0.188 | 0.114 | 0.052 | 0.202 | 0.108 |
| `q_ramp` | 0.188 | 0.104 | 0.043 | 0.200 | 0.119 |
| `a_line` | 0.134 | 0.025 | 0.057 | 0.109 | 0.047 |
| `lam_arr` | 0.115 | 0.067 | 0.025 | 0.104 | 0.065 |
| `h_fs` | 0.106 | 0.072 | 0.024 | 0.108 | 0.078 |
| `u0` | 0.060 | 0.007 | 0.013 | 0.058 | 0.016 |
| `fs5_parent` | 0.049 | 0.039 | 0.010 | 0.051 | 0.049 |
| `pi_scope` | 0.033 | 0.023 | 0.007 | 0.033 | 0.022 |
| `q_topup` | 0.027 | 0.020 | 0.006 | 0.030 | 0.032 |
| `k_cont` | 0.021 | 0.003 | 0.007 | 0.021 | −0.003 |
| Sum | 1.464 | 0.726 | | 1.440 | 0.822 |

*Derivation:* simple mean over the 14 keys `"<pathway>|<M-A or M-D>|default"` of `results/e4-sensitivity/sobol.json`, `cells[...]["N512"|"N256"]`, fields `ST`, `S1`, `ST_conf`.

**Table 21.** Parameter with the largest total index in each cell (N = 512, default background).

| Pathway | M-A | M-D |
|---|---|---|
| PW0 | `sw_line` (0.58) | `sw_line` (0.52) |
| PW1 | `aps_share` (0.34) | `aps_share` (0.34) |
| PW2 | `aps_share` (0.41) | `aps_share` (0.41) |
| PW3 | `q_pipe` (0.30) | `sw_line` (0.39) |
| PW4 | `aps_share` (0.42) | `aps_share` (0.41) |
| PW5 | `q_pipe` (0.33) | `aps_share` (0.28) |
| PW6 † | `aps_share` (0.36) | `aps_share` (0.35) |

*Source:* `results/e4-sensitivity/sobol.json`, `cells["<pathway>|<setting>|default"]["N512"].ST`.

**Table 22.** Fixed-background check (N = 256): parameter with the largest total index.

| Cell | Default background | 25th-percentile background | 75th-percentile background |
|---|---|---|---|
| PW0, M-A | `sw_line` (0.62) | `sw_line` (0.64) | `sw_line` (0.56) |
| PW0, M-D | `sw_line` (0.56) | `sw_line` (0.61) | `sw_line` (0.49) |
| PW4, M-A | `aps_share` (0.44) | `aps_share` (0.42) | `aps_share` (0.42) |
| PW4, M-D | `aps_share` (0.39) | `aps_share` (0.42) | `aps_share` (0.34) |

*Source:* `results/e4-sensitivity/sobol.json`, `cells["<pathway>|<setting>|default"|"p25"|"p75"]["N256"].ST`.

**Reading.**

1. Two groups of inputs dominate: local money for APS (whether a standing line exists, its size, and the share reserved for APS) and ancillary work at costly crossings (whether conduit or curb-ramp work is needed).
2. The mean index is an ordering aid only; it has no variance-decomposition meaning across cells. For example, the total index of `sw_line` ranges from 0.006 to 0.58 across the 14 cells at N = 512 (same source).
3. Mean confidence half-widths are about 0.04–0.07 for the leading parameters, so `q_pipe`, `sw_line` and `q_ramp` (0.188–0.215) cannot be ordered. At N = 256 the same four parameters lead, in a different order.
4. Effects are non-additive: total indices sum to 1.464 and first-order indices to 0.726. The total index of `aps_share` (0.329) is more than twice its first-order index (0.145), because the share matters only when a line exists. The first-order index of `a_line` (0.025) is smaller than its confidence half-width; it acts mainly through interactions.
5. Each row of a Saltelli matrix uses its own replicate seeds, so stochastic noise inflates total indices slightly. The total index of `k_cont` (0.021) indicates that this inflation is small.
6. The fixed-background check covered only the leading parameter of four cells; it did not change.

## 8. LLM red team (methodological probe, not a result)

### 8.1 Purpose and design

An adversarial "red team" of large-language-model runs was used to search for decision behaviour that the rule-based model omits. It was not used to estimate, calibrate or test anything, and none of its proposals was incorporated into the model.

- **Model:** Anthropic Claude Sonnet, run in October 2026. The exact model version string was not recorded in the output files.
- **Roles (5):** SFMTA grant-application staff, SFMTA capital-finance staff, SFCTA programming staff, the city's disability-affairs office together with the Mayor's Disability Council, and advocacy groups.
- **Situations (6):** an HSIP deadline in the following week; departure of the application owner; an advocacy meeting; a cost overrun after design; a Prop L amendment before the board; an SG017 allocation request.
- **Runs:** 4 independent role runs for each of the 30 role–situation cells (120 runs). Each run received the model's rule description and the evidence base and was asked for behaviours missing from the model, each with trigger, effect, cited evidence, and a candidate parameter with range.
- **Checking:** one further LLM run per cell (30 runs), instructed to act as a checker, removed proposals that the model already covers, opened and verified the cited evidence, merged duplicates, kept only proposals that can be expressed as one parameter or rule change, and retained at most five per cell. Each retained proposal was classified by evidence status and by how many of the four runs proposed it.

### 8.2 Counts

**Table 23.** Red-team counts.

| Quantity | Value |
|---|---|
| Role runs | 120 |
| Proposals in role-run output | 469 |
| Entries after merging duplicates within cells | 297 |
| Retained | 146 |
| Discarded (already modelled, unsupported, or not expressible as a parameter) | 151 |
| Retained, supported by a document | 13 |
| Retained, plausible but without a document | 98 |
| Retained, inference only | 35 |
| Retained, proposed by 1 / 2 / 3 / 4 of the four runs | 19 / 51 / 36 / 40 |

*Source:* `results/llm-redteam/raw-proposals.json` (120 entries; count of `proposals`); `results/llm-redteam/checked.json`, `combos[...]` (30 cells; counts of `kept` and `dropped`; fields `evidence_status` and `runs_proposing` of retained entries).

### 8.3 Hypotheses not incorporated

The retained proposals were grouped by theme. Six themes are reported as unverified hypotheses that the model does not contain:

1. district-level Prop L funds for neighbourhood transportation projects as an additional local funding route (proposed independently by three roles; some entries classified as document-supported);
2. shifting conduit and curb-ramp costs to the curb-ramp programme of another department instead of charging them to APS;
3. separating APS from its HSIP carrier application when time is short or the benefit–cost ratio is close to the threshold;
4. promises to follow up that absorb advocacy pressure without an application;
5. gatekeeping by SFCTA before submission and staged allocations of construction funds;
6. fault repairs displacing a restored dedicated line, with funds reprogrammed to signal controllers.

Themes 1 and 2 would add funding routes; themes 4–6 would remove or delay them. The model may therefore understate the role of small local funds and district channels and overstate the durability of a restored line. These are hypotheses for future work, not findings.
