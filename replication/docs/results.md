# Results

This document reports the experiments defined in `docs/experiment-protocol.md` and the secondary analyses listed there. All results are **uncalibrated scenario projections, not forecasts**. A share reported here is a share of sampled parameter combinations under the model's stated rules; it is not a probability that an outcome will occur in San Francisco.

## 1. How to read this document

1. **Source of every number.** Each table note names the results file and the field from which the numbers are taken; paths are relative to the package root. Where a number is derived arithmetically from stored values (for example a weighted average across settings), the note gives the derivation.
2. **Ranges.** Unless stated otherwise, "a–b" is the minimum and maximum across the six settings (M-A, M-B1, M-B2, M-C1, M-C2, M-D). Settings are parallel scenarios; a range across them is not a confidence interval.
3. **Percentages** are given to one decimal place, computed from the stored proportions.
4. **Sampling error.** In the main comparison each setting contains 461–528 combinations (Table 7 note). For a share near 0.9, the binomial standard error at these sample sizes is 1.3–1.4 percentage points. Pathways are evaluated on the same combinations and seeds, so differences between pathways are paired; paired tests were not computed. Small differences between pathways are therefore not interpreted, and comparisons are stated as counts of settings (Table 9).
5. **Reference level of "outperforms current practice".** A combination counts only if the pathway's mean ten-year installations strictly exceed those of PW0; ties count as not outperforming. A pathway identical to PW0 would score 0%. A pathway with no systematic effect whose random stream diverges from PW0's (because it draws additional random numbers) would score close to, but below, 50%. Shares should be read against this reference, not against 0%. The measure records direction only, not size.
6. **Installation counts** vary widely across combinations and depend on many assumed ranges. They are reported only where needed to interpret a comparison, and not as estimates.
7. **Primary and secondary analyses.** Section headings state which analyses are primary (Section 5 of the protocol) and which are secondary analyses computed from the E3 runs (Section 8.3 of the protocol).

## 2. E0: code check against an earlier baseline (primary)

**Table 1.** Installations predicted for 20 February 2024 to 30 June 2026 by a Markov multi-state model fitted to the request lists from 29 July 2022 to 20 February 2024 (2,000 simulations).

| Implementation | Median | 10th percentile | 90th percentile |
|---|---|---|---|
| Re-implementation (`code/baseline.py`, seed 146) | 20 | 13 | 28 |
| Earlier, independently written implementation | 20 | 13 | 27 |

*Source:* `results/e0-baseline-check.json` (fields `ours`, `reference_simulate_py`, `observed`, `match_within_tolerance`).

The re-implementation agrees with the earlier implementation within the specified tolerance (`match_within_tolerance` = true). The number observed in the request lists over the same period is 13, at the 10th percentile of both predictions. E0 checks code; it is not a validation of the agent-based model.

## 3. E1: historical screening and retrospective check (primary)

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

The binding constraint is the funded agency-crew stock (Fi): 381–630 of 2,000 combinations per setting meet its tolerance, against 1,467–2,000 for the other stocks. Observed Fi fell from 22 in July 2022 to 1 in August 2024 and was not replenished (`code/data/inputs.json`, `history.observed_stocks`). Any setting that stops new local funding batches can reproduce that pattern.

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

*Source:* `results/e1-fit/fit-table.json`, `cells["<setting>|base|<date>"].accept_rate`. The five dates use the same combinations and seeds, so differences between columns are exact.

**Table 5.** Acceptance and H1 pass rate (%) by prior width. Exhaustion date 2024-06. Narrow, base and wide: 2,000 combinations each; independent rate priors: 400 combinations.

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

**Table 6.** Median (10th–90th percentile) of selected parameters among combinations accepted under the base width, pooled over the five exhaustion dates (a combination accepted at several dates is counted once per date).

| Parameter | M-A | M-B1 | M-B2 | M-C1 | M-C2 | M-D |
|---|---|---|---|---|---|---|
| `b0` | −5.08 (−6.52 to −3.43) | −5.13 (−6.55 to −3.43) | −4.96 (−6.51 to −3.32) | −5.01 (−6.52 to −3.43) | −5.11 (−6.53 to −3.4) | −4.96 (−6.47 to −3.38) |
| `k0` | 1.27 (0.889 to 2.6) | 1.26 (0.893 to 2.58) | 1.48 (0.997 to 2.64) | 1.28 (0.89 to 2.6) | 1.31 (0.89 to 2.59) | 1.33 (0.889 to 2.64) |
| `phi` | 0.446 (0.0969 to 0.816) | 0.445 (0.0907 to 0.811) | 0.304 (0.0555 to 0.614) | 0.444 (0.0907 to 0.81) | 0.463 (0.102 to 0.813) | 0.464 (0.0973 to 0.811) |
| `h_in` | 0.855 (0.671 to 1.29) | 0.869 (0.678 to 1.28) | 0.852 (0.671 to 1.25) | 0.844 (0.667 to 1.27) | 0.848 (0.671 to 1.28) | 0.831 (0.653 to 1.27) |
| `h_fs` | 0.216 (0.14 to 0.294) | 0.216 (0.139 to 0.293) | 0.217 (0.139 to 0.294) | 0.217 (0.141 to 0.293) | 0.212 (0.139 to 0.29) | 0.212 (0.14 to 0.291) |

*Source:* `results/e1-fit/fit-table.json`, `needed_parameter_values["<setting>"]["<parameter>"]` (10th, 50th and 90th percentiles). The same field holds `b_own`, `p_deflect`, `m_b`, `m_c`, `g_cost`, `tau` and `a_local`.

### 3.4 Reading of E1

1. Acceptance under the base width is 15.4–26.2%, and 64.7–69.1% of accepted combinations also pass the retrospective check. Five of the six settings lie between 22.6% and 26.2%. The request lists do not discriminate between these explanations.
2. M-B2 (staffing constraint from 2023) has the lowest acceptance under the base width (15.4%), the wide width (5.1%) and the independent rate priors (7.8%), but the highest under the narrow width (26.6%). The ordering of settings is therefore not stable across prior widths.
3. Among the settings in which the staffing parameters act (M-B1, M-B2, M-D), accepted combinations of M-B2 have a lower median capacity reduction `phi` (0.304, against 0.445–0.464 in M-B1 and M-D). In the other settings `phi` has no effect, and its distribution there reflects the prior.
4. Acceptance changes by at most 1.8 percentage points across exhaustion dates (M-A, from 24.9% to 23.1%; Table 4).
5. Narrow priors give acceptance of 24.3–26.6% and H1 pass rates of 89.6–91.2%; wide priors 5.1–8.1% and 44.3–49.5%. With independent priors for the two reused installation rates, acceptance is 7.8–12.5% and the H1 pass rate 46.0–56.5%.
6. The percentiles of accepted parameters (Table 6) lie close to the prior ranges (`docs/parameters.md`): the history constrains these parameters only weakly. Screening is a weak filter, not a calibration.

## 4. E3: pathway comparison

### 4.1 Main comparison: combinations without a standing local line at the start (secondary analysis)

The primary E3 output pools combinations with and without a standing local line at the start (`sw_line` = 0 or 1). Because no standing local APS line exists today, the main comparison uses the `sw_line` = 0 group (protocol §8.3). The pooled output is reported in Section 4.4.

**Table 7.** Main comparison. Share of combinations in which the pathway's mean ten-year installations exceed those of current practice (PW0) under the same combination and seeds; share of runs with funding within five years.

| Pathway | Outperforms PW0 (%) | Outperforms PW0, direct initiation effects zero (%) | Funding within five years (%) | Funding within five years, direct initiation effects zero (%) |
|---|---|---|---|---|
| PW5 design standards (base design) | 94.6–97.3 | 95.4–97.3 | 84.5–91.0 | 84.4–91.0 |
| PW4 crossing-specific allocation (base design) | 92.4–96.9 | 95.7–98.1 | 86.8–91.3 | 86.8–91.3 |
| PW6 existing hardware programme | 91.5–95.0 | 91.9–95.9 | 68.0–79.4 | 67.6–75.3 |
| PW1 HSIP-first | 89.4–95.0 | 92.6–96.2 | 65.1–77.6 | 64.8–73.0 |
| PW2 local-first | 87.4–92.1 | 90.0–93.2 | 59.3–73.0 | 59.0–67.5 |
| PW3 accountability-first | 66.9–88.6 | 44.5–80.5 | 35.6–67.8 | 11.7–36.0 |
| PW0 current practice | — | — | 3.2–30.8 | 1.9–9.8 |
| PW5 design standards (approval variant) | 91.8–95.2 | 93.6–96.9 | 46.9–63.1 | 46.6–54.8 |
| PW4 crossing-specific allocation (approval variant) | 91.2–93.9 | 93.4–95.2 | 51.3–66.5 | 51.0–59.5 |

*Sources:* base design: `results/e3-pathways/posthoc.json`, `by_sw_line.line0_status_quo["<pathway>|positive"]` and `["<pathway>|zero_direct"]`, fields `share_better` and `P_money`. Approval variant: `results/e3-variant/summary.json`, `table["<pathway>|positive"]` and `["<pathway>|zero_direct"]`, fields `share_better_than_PW0` and `P_money`. Combinations per setting: M-A 518, M-B1 517, M-B2 502, M-C1 483, M-C2 461, M-D 528 (`results/web/meta.json`, `n_param_sets_by_mechanism`; `results/e3-variant/summary.json`, `by_mech[...].n_sets`). The fields `base_share_better` and `base_P_money` of `results/e3-variant/summary.json` hold the base-design values of PW4 and PW5 for the same combinations and reproduce the corresponding rows of this table.

**Table 8.** Outperforms PW0 (%), by setting. Main comparison, positive control.

| Pathway | M-A | M-B1 | M-B2 | M-C1 | M-C2 | M-D |
|---|---|---|---|---|---|---|
| PW1 | 95.0 | 92.3 | 92.4 | 93.2 | 89.4 | 92.8 |
| PW2 | 92.1 | 89.9 | 87.5 | 90.3 | 87.4 | 90.1 |
| PW3 | 88.6 | 82.8 | 86.5 | 66.9 | 86.3 | 71.8 |
| PW4 (base design) | 96.7 | 93.0 | 92.4 | 96.9 | 93.5 | 96.6 |
| PW5 (base design) | 97.3 | 95.5 | 94.6 | 96.7 | 94.6 | 96.2 |
| PW6 | 95.0 | 93.2 | 91.8 | 94.6 | 91.5 | 92.0 |
| PW4 (approval variant) | 93.8 | 91.7 | 91.2 | 93.6 | 92.2 | 93.9 |
| PW5 (approval variant) | 95.2 | 94.6 | 93.4 | 93.6 | 91.8 | 92.8 |

*Sources:* `results/e3-pathways/posthoc.json`, `by_sw_line.line0_status_quo["<pathway>|positive"].by_mech`; `results/e3-variant/summary.json`, `table["<pathway>|positive"].by_mech[...].share_better_than_PW0`.

**Table 9.** Number of settings (out of six) in which the row pathway outperforms PW0 in a larger share of combinations than the column pathway. Main comparison, positive control.

| Row \ column | PW1 | PW2 | PW3 | PW4 | PW5 | PW6 | PW4 var. | PW5 var. |
|---|---|---|---|---|---|---|---|---|
| PW1 | — | 6 | 6 | 0 | 0 | 2 | 3 | 0 |
| PW2 | 0 | — | 6 | 0 | 0 | 0 | 0 | 0 |
| PW3 | 0 | 0 | — | 0 | 0 | 0 | 0 | 0 |
| PW4 | 5 | 6 | 6 | — | 2 | 5 | 6 | 4 |
| PW5 | 6 | 6 | 6 | 4 | — | 6 | 6 | 6 |
| PW6 | 3 | 6 | 6 | 1 | 0 | — | 4 | 1 |
| PW4 var. | 3 | 6 | 6 | 0 | 0 | 2 | — | 2 |
| PW5 var. | 6 | 6 | 6 | 2 | 0 | 5 | 3 | — |

*Derivation:* from the per-setting values of Table 8. "var." denotes the approval variant.

**Table 10.** Share of runs (%) reaching each pathway step. Main comparison, positive control, 60,180 runs per pathway (3,009 combinations × 20 replicates).

| Pathway | Step reached | Runs (%) |
|---|---|---|
| PW1 | Repackaged application in the next HSIP cycle | 100.0 |
| PW1 | Hypothetical management reallocation | 42.6 |
| PW1 | Prop L amendment | 77.7 |
| PW2 | General Fund request | 55.0 |
| PW2 | HSIP repackaging | 41.2 |
| PW3 | Litigation | 64.6 |
| PW3 | Structured negotiation | 96.5 |
| PW5 | Standing local line (added by trigger) | 99.7 |
| PW6 | General Fund request | 41.6 |
| PW6 | HSIP repackaging | 31.1 |
| PW6 | Prop L amendment | 76.2 |
| PW4 (approval variant) | General Fund request | 55.0 |
| PW4 (approval variant) | Prop L amendment | 100.0 |
| PW5 (approval variant) | General Fund request | 54.9 |
| PW5 (approval variant) | Prop L amendment | 99.7 |
| PW5 (approval variant) | Standing local line (added by trigger) | 99.7 |

*Source:* `results/web/pathways.json`, `path_reach["<pathway>"].nodes` and `variant_path_reach["<pathway>-approval"].nodes`; `runs`.

### 4.2 Reading of the main comparison

1. Under the base design, PW5 and PW4 outperform current practice in 92.4–97.3% of combinations and PW6 in 91.5–95.0%. PW5 lies above PW6 in 6 of the six settings and PW4 above PW6 in 5; PW6 lies above PW1 in 3, PW1 above PW2 in 6 (Table 9).
2. PW3 has the lowest share in 6 of the six settings (66.9–88.6%). In M-C1 and M-D its share (66.9% and 71.8%) is well below the other pathways.
3. **Approval variant.** Requiring approval for the standing line lowers the share outperforming PW0 to 91.2–93.9% (PW4) and 91.8–95.2% (PW5). Funding within five years falls from 86.8–91.3% to 51.3–66.5% for PW4 and from 84.5–91.0% to 46.9–63.1% for PW5. Measured as a share of each pathway's advantage over PW0 within a setting, the approval requirement removes 39–43% of PW4's advantage in funding within five years and 45–48% of PW5's, and 44–51% (PW4) and 27–33% (PW5) of the advantage in median ten-year installations. The line received without approval therefore accounts for a substantial part, but not all, of the two pathways' advantage. In the variant, the General Fund fallback is reached in 55.0% (PW4) and 54.9% (PW5) of runs, i.e. the Prop L amendment fails in those runs (Table 10).
4. Setting the direct initiation effects to zero changes PW3 most: the share outperforming PW0 falls from 66.9–88.6% to 44.5–80.5%, and funding within five years from 35.6–67.8% to 11.7–36.0%. In this control `b_pr` is zero, so advocacy pressure no longer affects initiation. What remains of PW3's effect comes from the escalation of the enforcement level, whose effect `b_enf` is retained, and from PW3's other rule changes; part of it may reflect divergence of random streams, given the reference level in §1, item 5.
5. Median ten-year installations per combination range from 22.75–25.27 (PW0) to 33.35–38.90 (PW4) across settings (`results/e3-pathways/posthoc.json`, `by_sw_line.line0_status_quo["<pathway>|positive"].median_cov10`). They are reported for scale only.
6. *Derivations in item 3:* for each setting, (base − variant) / (base − PW0), using funding within five years from `results/web/robustness.json` (`table`, field `P_money_flows_5y_mean`) and `results/e3-variant/summary.json` (`by_mech[...].P_money`), and median ten-year installations from `results/web/robustness.json` (`coverage_10y_p50`) and `results/e3-variant/summary.json` (`by_mech[...].median_cov10`). The installation measure is a ratio of differences of medians, not a median of differences.

### 4.3 Primary output: all combinations pooled

**Table 11.** Pooled over `sw_line` = 0 and 1 (1,000 combinations per setting), as stored by `code/experiments.py`.

| Pathway | Outperforms PW0 (%) | Outperforms PW0, direct initiation effects zero (%) | Funding within five years (%) | Maximum regret (installations) |
|---|---|---|---|---|
| PW1 HSIP-first | 82.2–87.0 | 83.6–88.8 | 76.3–86.0 | 31.90–64.65 |
| PW2 local-first | 73.2–78.1 | 74.8–79.1 | 71.1–82.1 | 34.95–57.55 |
| PW3 accountability-first | 53.2–71.0 | 35.9–65.3 | 58.6–79.1 | 39.50–85.65 |
| PW4 crossing-specific allocation | 82.2–85.7 | 82.6–87.4 | 85.0–90.6 | 23.05–33.60 |
| PW5 design standards | 81.6–87.8 | 80.8–88.2 | 83.5–90.9 | 16.30–28.25 |
| PW6 existing hardware programme | 77.6–82.0 | 78.0–82.4 | 78.1–87.2 | 32.35–57.65 |
| PW0 current practice | — | — | 40.6–61.6 | 45.05–85.65 |

*Source:* `results/e3-pathways/robustness.json`, entries with `control` = `positive` (and `zero_direct` for the second column), fields `share_better_than_PW0`, `P_money_mean`, `max_regret`; range over the six settings. `results/e3-pathways/posthoc.json`, `by_sw_line.pooled`, reproduces the first three columns.

The pooled output counts combinations that already have a standing local line as current practice. Current practice then has funding within five years in 40.6–61.6% of runs, which does not describe current conditions. For this reason it is not used as the main comparison.

### 4.4 Combinations that already have a standing local line (secondary analysis)

**Table 12.** `sw_line` = 1 (not current conditions; 472–539 combinations per setting).

| Pathway | Outperforms PW0 (%) | Outperforms PW0, direct initiation effects zero (%) | Funding within five years (%) |
|---|---|---|---|
| PW1 HSIP-first | 75.7–81.4 | 75.8–82.8 | 88.8–94.7 |
| PW2 local-first | 57.0–63.1 | 57.2–63.9 | 84.2–92.4 |
| PW3 accountability-first | 40.4–52.1 | 27.9–50.6 | 82.5–91.5 |
| PW4 crossing-specific allocation | 70.1–74.9 | 71.4–77.4 | 83.1–91.5 |
| PW5 design standards | 69.7–78.3 | 68.3–78.4 | 82.5–91.4 |
| PW6 existing hardware programme | 63.3–68.0 | 64.5–68.7 | 89.4–95.2 |
| PW0 current practice | — | — | 82.5–91.4 |

*Source:* `results/e3-pathways/posthoc.json`, `by_sw_line.line1`. Combinations per setting are 1,000 minus the counts in the Table 7 note.

When a standing line already exists, current practice already receives funding within five years in 82.5–91.4% of runs. The shares outperforming PW0 for PW2 (57.0–63.1%) and PW3 (40.4–52.1%) are close to the reference level for no systematic effect (§1, item 5).

### 4.5 Accountability-first and the standing line, pooled over settings (secondary analysis)

**Table 13.** Pooled over the six settings.

| Group | PW3 outperforms PW0 (%) | PW2 outperforms PW0 (%) | PW0 funding within five years (%) | PW3 funding within five years (%) |
|---|---|---|---|---|
| No standing line at the start (3,009 combinations) | 80.5 | 89.6 | 18.0 | 55.8 |
| Standing line at the start (2,991 combinations) | 46.0 | 59.7 | 87.7 | 87.7 |

*Derivation:* weighted averages over settings, weights equal to the number of combinations per setting. No-line group: `results/web/robustness.json`, `table` (fields `share_better_than_PW0`, `P_money_flows_5y_mean`). Standing-line group: (1,000 × value in `table_pooled_sw_line` − n₀ × value in `table`) / (1,000 − n₀) per setting, then weighted. Pooling over settings mixes scenarios with different shares; the per-setting values are in the cited fields. The same quantities are plotted in `results/figures/fig2-accountability-by-standing-line.png`.

In the model, accountability-first adds most where no standing source of local money exists; where one exists, its share is close to the reference level for no systematic effect.

### 4.6 PW1 with the hypothetical reallocation step approximately disabled (secondary analysis)

**Table 14.** `sw_line` = 0 and `q_dir` < 0.08 (at least 44 combinations per setting).

| Pathway | Outperforms PW0 (%) | Funding within five years (%) |
|---|---|---|
| PW5 design standards | 93.2–98.3 | 85.9–96.7 |
| PW4 crossing-specific allocation | 93.2–97.9 | 85.8–96.9 |
| PW6 existing hardware programme | 94.9–97.7 | 72.9–83.1 |
| PW2 local-first | 89.8–96.3 | 61.6–77.3 |
| PW1 HSIP-first | 75.0–90.9 | 54.1–75.9 |
| PW3 accountability-first | 63.0–93.2 | 40.3–71.2 |
| PW0 current practice | — | 2.2–33.4 |

*Source:* `results/e3-pathways/posthoc.json`, `line0_q_dir_lt_0.08["<pathway>|positive"]`; minimum combinations per setting in `n_sets_per_mech`.

The final step of PW1, a one-time allocation of `a_line` with probability `q_dir`, has no documentary support (`docs/ODD+D.md`). With that step approximately disabled, PW1 outperforms PW0 in 75.0–90.9% of combinations, against 89.4–95.0% in the main comparison. The subset is small, so these ranges are noisy.

## 5. One-parameter splits and correlations (secondary analysis)

The splits below group all E3 combinations (both values of `sw_line`, positive control) by one parameter while all other parameters vary. They are marginal splits, not comparisons with other parameters held fixed, and they pool combinations with and without a standing line.

**Table 15.** Advocacy pressure frequency `lam_press` (events per year).

| Bin | PW0 funding within five years (%) | PW3 outperforms PW0 (%) | PW3 funding within five years (%) | PW1 outperforms (%) | PW4 outperforms (%) | PW5 outperforms (%) |
|---|---|---|---|---|---|---|
| [0, 0.1) | 42.1–61.3 | 53.2–70.6 | 59.4–76.3 | 82.7–92.2 | 81.3–89.0 | 78.6–91.0 |
| [0.1, 0.25) | 43.2–62.4 | 52.6–67.3 | 60.3–80.4 | 82.7–87.3 | 79.9–88.5 | 83.6–87.0 |
| [0.25, 0.4) | 39.8–62.7 | 55.0–77.1 | 59.7–81.5 | 79.3–88.7 | 77.2–86.4 | 79.6–90.3 |
| [0.4, 0.5] | 36.9–62.7 | 51.7–67.9 | 53.8–78.8 | 78.4–88.8 | 80.0–86.1 | 83.4–87.2 |

**Table 16.** Internal crew capacity `k0` (installations per month).

| Bin | PW0 funding within five years (%) | PW0 median 10-year installations | PW3 outperforms PW0 (%) | PW4 median 10-year installations | PW5 median 10-year installations |
|---|---|---|---|---|---|
| [0.5, 1) | 41.3–63.3 | 26.4–31.1 | 49.1–71.0 | 33.9–40.5 | 33.7–41.4 |
| [1.0, 2) | 41.1–61.2 | 25.5–29.5 | 53.2–74.4 | 33.4–38.1 | 32.1–38.8 |
| [2.0, 3] | 39.4–62.9 | 25.4–29.5 | 57.5–64.6 | 32.0–38.6 | 31.7–39.5 |

**Table 17.** Installation rate of funded agency-crew crossings `h_in` (per year).

| Bin | PW0 funding within five years (%) | PW0 median 10-year installations | PW3 median 10-year installations | PW3 funding within five years (%) | PW4 funding within five years (%) |
|---|---|---|---|---|---|
| [0.59, 0.85) | 37.9–60.8 | 25.4–28.8 | 26.8–32.2 | 58.6–77.8 | 84.6–90.1 |
| [0.85, 1.15) | 42.1–61.1 | 25.4–29.5 | 27.7–33.4 | 59.4–78.3 | 84.1–94.1 |
| [1.15, 1.41] | 45.0–67.2 | 26.8–30.6 | 27.8–36.0 | 56.6–85.1 | 87.2–94.8 |

*Sources (Tables 15–17):* `results/e3-pathways/posthoc.json`, `splits["<parameter>[<low>,<high>)"]["<pathway>"]`, fields `P_money`, `share_better`, `median_cov10`. In the keys the upper bound of the last bin is written slightly above the range maximum (for example `0.5001`) so that the maximum is included. The same field holds the splits by `b_pr` and `q_dir`.

**Pressure effect per event `b_pr`.** In the bins [0, 0.5), [0.5, 1.5), [1.5, 2], PW0 funding within five years is 40.3–65.4%, 42.0–63.2%, 37.8–58.8%, and PW3 outperforms PW0 in 51.0–73.5%, 53.3–70.7%, 54.5–69.0% of combinations (same source, `splits["b_pr[...]"]`).

**Correlations among history-screened parameters** (`results/e3-pathways/posthoc.json`, `screened_param_correlations`): `lam_press`–`b0` -0.06; `lam_press`–`b_pr` -0.052; `b_pr`–`b0` 0.02; `k0`–`h_in` -0.704; `k0`–`b0` -0.012; `k0`–`phi` 0.071; `h_in`–`b0` -0.003; `p_deflect`–`b0` -0.022. They are computed over the 13,759 entries of the E1 accepted pool, all settings together. The six settings screen the same base sample of 2,000 combinations, and a combination accepted at several exhaustion dates or in several settings appears once per acceptance, so the entries contain at most 2,000 distinct combinations and are weighted by the number of acceptances.

**Reading.** Across the sampled ranges, the bins of advocacy pressure frequency and of pressure effect show no monotonic trend in PW0's funding or in PW3's advantage; the ranges across settings overlap and are wide relative to the differences between bins. Pressure is nearly uncorrelated with the baseline initiation propensity among screened combinations, so this pattern is not produced by a pairwise screening correlation; it does not rule out a modest trend, which these marginal bins could not detect. Higher crew capacity shows no gain, but this split is confounded: screening induces a strong negative correlation between `k0` and `h_in` (-0.704), because the request lists constrain only their joint output. In the model, pressure and ownership act only on the probability of starting an application, and crew capacity is only a monthly ceiling; these results describe that model structure and are not evidence that pressure or capacity are unimportant in practice.

## 6. E2: conditions under which funding flows

### 6.1 Primary PRIM output

**Table 18.** Test-set coverage and density of the PRIM boxes and test-set accuracy of the depth-3 CART cross-check; range over five splits.

| Pathway | Threshold | Test coverage | Test density | CART test accuracy |
|---|---|---|---|---|
| PW0 | 0.25 | 0.573–0.628 | 0.981–0.988 | 0.821–0.832 |
| PW0 | 0.5 | 0.687–0.750 | 0.970–0.979 | 0.885–0.907 |
| PW0 | 0.75 | 0.678–0.812 | 0.939–0.963 | 0.921–0.938 |
| PW1 | 0.25 | 0.399–0.746 | 0.973–0.993 | 0.929–0.939 |
| PW1 | 0.5 | 0.390–0.436 | 0.981–0.986 | 0.866–0.877 |
| PW1 | 0.75 | 0.450–0.483 | 0.968–0.977 | 0.785–0.825 |
| PW2 | 0.25 | 0.403–0.801 | 0.958–0.989 | 0.913–0.925 |
| PW2 | 0.5 | 0.426–0.463 | 0.974–0.986 | 0.854–0.866 |
| PW2 | 0.75 | 0.486–0.522 | 0.944–0.963 | 0.792–0.807 |
| PW3 | 0.25 | 0.440–0.480 | 0.981–0.986 | 0.831–0.843 |
| PW3 | 0.5 | 0.480–0.527 | 0.967–0.975 | 0.785–0.797 |
| PW3 | 0.75 | 0.461–0.549 | 0.948–0.963 | 0.748–0.777 |
| PW4 | 0.25 | 0.689–0.790 | 0.984–0.991 | 0.955–0.963 |
| PW4 | 0.5 | 0.679–0.763 | 0.976–0.984 | 0.943–0.948 |
| PW4 | 0.75 | 0.483–0.660 | 0.970–0.991 | 0.922–0.928 |
| PW5 | 0.25 | 0.500–0.764 | 0.979–0.995 | 0.943–0.952 |
| PW5 | 0.5 | 0.558–0.776 | 0.974–0.989 | 0.935–0.941 |
| PW5 | 0.75 | 0.419–0.624 | 0.974–0.995 | 0.909–0.924 |
| PW6 | 0.25 | 0.754–0.803 | 0.982–0.984 | 0.958–0.966 |
| PW6 | 0.5 | 0.396–0.772 | 0.944–0.990 | 0.899–0.914 |
| PW6 | 0.75 | 0.414–0.491 | 0.970–0.977 | 0.798–0.815 |

*Source:* `results/e2-prim/prim.json`, `["<pathway>"][k]`, fields `threshold`, `coverage_test`, `density_test`, `cart_test_accuracy`. CART accuracy over all 105 pathway–threshold–split entries: 0.748–0.966. The `rules` field of this file is not reported, because its extraction is defective (protocol §8.2). The share of successful combinations (the base rate) is not stored; density and CART accuracy should be compared with it, and for pathways in which most combinations succeed, high density and accuracy indicate little improvement over the base rate.

### 6.2 Corrected PRIM rules (secondary analysis)

**Table 19.** Corrected rules at threshold 0.5. Each row is one of five 50/50 splits; restrictions are given as box bounds and, in brackets, as the share of the training range that the restriction removes.

| Pathway | Split | Restrictions | Test coverage | Test density |
|---|---|---|---|---|
| PW0 | 0 | `sw_line` = 1; `aps_share` ≥ 0.0423 (8.4%); `q_ramp` 0.00296–0.963 (3.7%) | 0.813 | 0.968 |
| PW0 | 1 | `sw_line` = 1; `aps_share` ≥ 0.0702 (14.0%); `q_ramp` 0.00296–0.962 (3.8%) | 0.769 | 0.978 |
| PW0 | 2 | `sw_line` = 1; `aps_share` ≥ 0.0444 (8.9%); `q_pipe` 0.00106–0.952 (4.8%) | 0.825 | 0.956 |
| PW0 | 3 | `sw_line` = 1; `aps_share` ≥ 0.0702 (14.0%); `q_pipe` 0.00106–0.948 (5.2%) | 0.779 | 0.980 |
| PW0 | 4 | `sw_line` = 1; `aps_share` ≥ 0.0619 (12.3%); `q_ramp` 0.00296–0.955 (4.5%) | 0.795 | 0.977 |
| PW1 | 0 | `sw_line` = 1; `aps_share` ≥ 0.0475 (9.5%); `q_pipe` 0.00106–0.951 (4.9%) | 0.490 | 0.983 |
| PW1 | 1 | `sw_line` = 1; `aps_share` ≥ 0.0715 (14.3%); `q_pipe` 0.00106–0.95 (5.0%) | 0.460 | 0.987 |
| PW1 | 2 | `sw_line` = 1; `aps_share` ≥ 0.072 (14.4%); `q_pipe` 0.00106–0.953 (4.7%) | 0.472 | 0.988 |
| PW1 | 3 | `sw_line` = 1; `aps_share` ≥ 0.0496 (9.9%); `q_pipe` 0.00106–0.944 (5.6%) | 0.479 | 0.983 |
| PW1 | 4 | `sw_line` = 1; `aps_share` ≥ 0.0875 (17.5%); `q_pipe` 0.00106–0.948 (5.2%) | 0.458 | 0.988 |
| PW2 | 0 | `sw_line` = 1; `aps_share` ≥ 0.0475 (9.5%); `q_pipe` 0.00106–0.951 (4.9%) | 0.509 | 0.971 |
| PW2 | 1 | `sw_line` = 1; `aps_share` ≥ 0.0723 (14.4%); `q_pipe` 0.00106–0.948 (5.2%) | 0.475 | 0.976 |
| PW2 | 2 | `sw_line` = 1; `aps_share` ≥ 0.0472 (9.4%); `q_pipe` 0.00106–0.951 (4.9%) | 0.515 | 0.964 |
| PW2 | 3 | `sw_line` = 1; `aps_share` ≥ 0.074 (14.7%); `q_pipe` 0.00106–0.95 (5.0%) | 0.481 | 0.981 |
| PW2 | 4 | `sw_line` = 1; `aps_share` ≥ 0.0654 (13.0%); `q_pipe` 0.00106–0.948 (5.2%) | 0.502 | 0.980 |
| PW3 | 0 | `sw_line` = 1; `aps_share` ≥ 0.0446 (8.9%); `a_local` ≥ 23,613 (4.1%) | 0.563 | 0.954 |
| PW3 | 1 | `sw_line` = 1; `aps_share` ≥ 0.0702 (14.0%); `q_ramp` 0.00296–0.962 (3.8%) | 0.537 | 0.978 |
| PW3 | 2 | `sw_line` = 1; `aps_share` ≥ 0.0467 (9.3%); `q_pipe` 0.00106–0.953 (4.7%) | 0.580 | 0.958 |
| PW3 | 3 | `sw_line` = 1; `aps_share` ≥ 0.072 (14.4%); `a_local` ≥ 24,073 (4.1%) | 0.544 | 0.972 |
| PW3 | 4 | `sw_line` = 1; `aps_share` ≥ 0.0634 (12.6%); `a_local` ≥ 23,613 (4.1%) | 0.562 | 0.963 |
| PW4 | 0 | `aps_share` ≥ 0.13 (25.9%); `q_pipe` 0.00106–0.887 (11.3%); `q_ramp` 0.00296–0.917 (8.3%) | 0.676 | 0.997 |
| PW4 | 1 | `aps_share` ≥ 0.0917 (18.3%); `q_pipe` 0.00106–0.95 (5.0%); `q_ramp` 0.00296–0.913 (8.7%) | 0.773 | 0.993 |
| PW4 | 2 | `aps_share` ≥ 0.0911 (18.2%); `q_pipe` 0.00106–0.894 (10.6%); `q_ramp` 0.00296–0.964 (3.6%) | 0.808 | 0.994 |
| PW4 | 3 | `aps_share` ≥ 0.0736 (14.7%); `q_pipe` 0.00106–0.948 (5.2%); `q_ramp` 0.00296–0.915 (8.6%) | 0.802 | 0.992 |
| PW4 | 4 | `aps_share` ≥ 0.108 (21.6%); `q_pipe` 0.00106–0.875 (12.5%); `q_ramp` 0.00296–0.91 (9.0%) | 0.688 | 0.998 |
| PW5 | 0 | `aps_share` ≥ 0.0909 (18.2%); `q_pipe` 0.00106–0.951 (4.9%); `q_ramp` 0.00296–0.917 (8.3%) | 0.779 | 0.990 |
| PW5 | 1 | `aps_share` ≥ 0.0917 (18.3%); `q_pipe` 0.00106–0.95 (5.0%); `q_ramp` 0.00296–0.913 (8.7%) | 0.774 | 0.990 |
| PW5 | 2 | `aps_share` ≥ 0.112 (22.4%); `q_pipe` 0.00106–0.89 (11.0%); `q_ramp` 0.00296–0.922 (7.8%) | 0.727 | 0.992 |
| PW5 | 3 | `aps_share` ≥ 0.074 (14.7%); `q_pipe` 0.00106–0.95 (5.0%); `q_ramp` 0.00296–0.915 (8.6%) | 0.802 | 0.991 |
| PW5 | 4 | `aps_share` ≥ 0.108 (21.5%); `q_pipe` 0.00106–0.948 (5.2%); `q_ramp` 0.00296–0.88 (12.1%) | 0.706 | 0.998 |
| PW6 | 0 | `aps_share` ≥ 0.0682 (13.6%); `q_pipe` 0.00106–0.951 (4.9%); `q_ramp` 0.00296–0.961 (3.9%) | 0.829 | 0.944 |
| PW6 | 1 | `aps_share` ≥ 0.0715 (14.3%); `q_pipe` 0.00106–0.948 (5.2%); `q_ramp` 0.00296–0.961 (3.9%) | 0.818 | 0.949 |
| PW6 | 2 | `aps_share` ≥ 0.0472 (9.4%); `q_pipe` 0.00106–0.951 (4.9%); `q_ramp` 0.00296–0.964 (3.6%) | 0.878 | 0.944 |
| PW6 | 3 | `aps_share` ≥ 0.0496 (9.9%); `q_pipe` 0.00106–0.95 (5.0%); `q_ramp` 0.00296–0.915 (8.6%) | 0.808 | 0.945 |
| PW6 | 4 | `aps_share` ≥ 0.0669 (13.3%); `q_pipe` 0.00106–0.95 (5.0%); `q_ramp` 0.00296–0.955 (4.5%) | 0.829 | 0.953 |

*Source:* `results/e3-pathways/posthoc.json`, `prim_full_rules_thr0.5["<pathway>"][split]`, fields `rules` (`param`, `low`, `high`, `trimmed_share_of_range`), `coverage_test`, `density_test`. Bounds are rounded to three significant figures; the unrounded values are in the file. `sw_line` is a 0/1 switch, so a lower bound of 0.5 means `sw_line` = 1. For `aps_share` and `a_local` only the lower bound is shown, the upper bound being the training maximum.

**Reading.**

1. For PW0–PW3, every box requires a standing local line and an APS share of that line of at least 4.2–8.8% (`aps_share` lower bounds 0.0423–0.0875). The third restriction (`a_local`, `q_pipe`, `q_ramp`) removes only 3.7–5.6% of its range. Test coverage is 0.769–0.825 for PW0 and 0.458–0.580 for PW1–PW3, which have other routes to funding, such as federal awards.
2. For PW4–PW6 (a line provided by design, or an existing hardware programme), every box requires an APS share of at least 4.7–13.0% and trims the extreme combinations in which almost all costly crossings need conduit or curb-ramp work (3.6–12.5% of those ranges). Test coverage is 0.676–0.878.
3. Test density is 0.944–0.998 for all boxes; see the base-rate caveat under Table 18.
4. The size of the standing line (`a_line`, sampled between $0.5 million and $2 million per year) does not appear in any corrected box.
5. These boxes were re-fitted on a different candidate set from the primary boxes (protocol §8.2), so their coverage and density differ from Table 18. PRIM was not run for the approval variant.

## 7. E4: global sensitivity analysis (primary)

E4 samples the full prior ranges without historical screening. It describes which inputs drive ten-year installations in the model, not in the screened combinations of E3.

### 7.1 E4a: Morris screening

The two passes' top-12 lists share 10 parameters; the list used for E4b is given in `docs/experiment-protocol.md` §7 (source `results/e4-sensitivity/morris.json`, fields `top12_pass1`, `top12_pass2`, `overlap`, `chosen_for_sobol`, and `cells["<pathway>|<setting>"]["pass1"|"pass2"].mu_star`).

**Table 20.** Rank by mean μ* (out of 98) of parameters that represent accountability, pressure, capacity and two funding thresholds.

| Parameter | Meaning | Pass 1: rank (mean μ*) | Pass 2: rank (mean μ*) |
|---|---|---|---|
| `k0` | Internal crew capacity | 20 (2.52) | 67 (1.92) |
| `c_final` | HSIP selection threshold | 22 (2.42) | 14 (3.14) |
| `b_own` | Effect of a named owner on initiation | 24 (2.35) | 69 (1.91) |
| `q_dir` | Probability of the hypothetical reallocation | 34 (2.10) | 43 (2.08) |
| `b_spec` | Effect of a specified deadline on initiation | 51 (1.88) | 42 (2.08) |
| `b_ov` | Effect of oversight on initiation | 54 (1.84) | 75 (1.86) |
| `b_enf` | Effect of external enforcement on initiation | 69 (1.79) | 35 (2.16) |
| `lam_press` | Advocacy pressure frequency | 82 (1.73) | 94 (1.68) |
| `b_pr` | Effect of a pressure event on initiation | 97 (1.57) | 91 (1.73) |

*Derivation:* mean of `cells[...]["pass<k>"].mu_star["<parameter>"]` over the 42 cells of `results/e4-sensitivity/morris.json`, ranked in decreasing order. μ* approximates the change in ten-year installations from moving a parameter across its range (protocol §8.1).

None of these parameters is among the leading twelve in either pass. Below the leading twelve, ranks are unstable between passes (median absolute change in rank 18 places), so ranks in that region are not interpreted beyond "outside the leading twelve". Two reasons for the low position of accountability, pressure and capacity apply. First, the model gives them narrow channels: ownership, deadlines, oversight, pressure and enforcement act only on the probability of starting an application, and crew capacity is a monthly ceiling. Second, μ* is averaged over 42 cells, which dilutes parameters that act in only some settings. This is not evidence that these factors are unimportant in practice.

### 7.2 E4b: Sobol indices

**Table 21.** Total (ST) and first-order (S1) indices, simple mean over the 14 default-background cells (7 pathways × {M-A, M-D}).

| Parameter | ST, N = 512 | S1, N = 512 | Mean of per-cell 95% half-widths of ST, N = 512 | ST, N = 256 | S1, N = 256 |
|---|---|---|---|---|---|
| `aps_share` | 0.330 | 0.146 | 0.068 | 0.329 | 0.148 |
| `q_pipe` | 0.217 | 0.109 | 0.049 | 0.198 | 0.147 |
| `q_ramp` | 0.190 | 0.109 | 0.044 | 0.204 | 0.128 |
| `sw_line` | 0.180 | 0.109 | 0.048 | 0.194 | 0.107 |
| `a_line` | 0.135 | 0.025 | 0.057 | 0.110 | 0.048 |
| `lam_arr` | 0.116 | 0.068 | 0.025 | 0.106 | 0.066 |
| `h_fs` | 0.106 | 0.073 | 0.024 | 0.108 | 0.079 |
| `u0` | 0.061 | 0.008 | 0.014 | 0.059 | 0.016 |
| `fs5_parent` | 0.050 | 0.040 | 0.010 | 0.053 | 0.051 |
| `pi_scope` | 0.033 | 0.022 | 0.007 | 0.033 | 0.024 |
| `q_topup` | 0.028 | 0.020 | 0.006 | 0.030 | 0.033 |
| `k_cont` | 0.022 | 0.004 | 0.007 | 0.022 | −0.001 |
| Sum | 1.467 | 0.732 | | 1.447 | 0.846 |

*Derivation:* simple mean over the keys `"<pathway>|<M-A or M-D>|default"` of `results/e4-sensitivity/sobol.json`, `cells[...]["N512"|"N256"]`, fields `ST`, `S1`, `ST_conf`.

**Table 22.** Parameters with the two largest total indices in each cell (N = 512, default background), with the 95% half-width of each.

| Pathway | M-A: first | M-A: second | M-D: first | M-D: second |
|---|---|---|---|---|
| PW0 | `sw_line` 0.58 ± 0.17 | `aps_share` 0.24 ± 0.06 | `sw_line` 0.52 ± 0.12 | `aps_share` 0.26 ± 0.06 |
| PW1 | `aps_share` 0.34 ± 0.07 | `q_pipe` 0.25 ± 0.06 | `aps_share` 0.35 ± 0.08 | `sw_line` 0.19 ± 0.05 |
| PW2 | `aps_share` 0.41 ± 0.08 | `q_pipe` 0.27 ± 0.06 | `aps_share` 0.40 ± 0.08 | `q_pipe` 0.18 ± 0.04 |
| PW3 | `q_pipe` 0.30 ± 0.06 | `aps_share` 0.29 ± 0.07 | `sw_line` 0.39 ± 0.10 | `aps_share` 0.29 ± 0.07 |
| PW4 | `aps_share` 0.42 ± 0.08 | `q_pipe` 0.28 ± 0.06 | `aps_share` 0.41 ± 0.07 | `q_pipe` 0.18 ± 0.04 |
| PW5 | `q_pipe` 0.33 ± 0.06 | `q_ramp` 0.33 ± 0.07 | `aps_share` 0.28 ± 0.05 | `q_pipe` 0.23 ± 0.04 |
| PW6 | `aps_share` 0.36 ± 0.08 | `q_pipe` 0.27 ± 0.06 | `aps_share` 0.34 ± 0.07 | `q_pipe` 0.17 ± 0.04 |

*Source:* `results/e4-sensitivity/sobol.json`, `cells["<pathway>|<setting>|default"]["N512"]`, fields `ST`, `ST_conf`. In 8 of 14 cells the intervals of the first and second parameter overlap, so the leading parameter in those cells is not determined.

**Table 23.** Fixed-background check (N = 256): parameter with the largest total index.

| Cell | Default background | 25th-percentile background | 75th-percentile background |
|---|---|---|---|
| PW0, M-A | `sw_line` (0.62) | `sw_line` (0.64) | `sw_line` (0.56) |
| PW0, M-D | `sw_line` (0.56) | `sw_line` (0.61) | `sw_line` (0.49) |
| PW4, M-A | `aps_share` (0.44) | `aps_share` (0.42) | `aps_share` (0.43) |
| PW4, M-D | `aps_share` (0.39) | `aps_share` (0.42) | `aps_share` (0.36) |

*Source:* `results/e4-sensitivity/sobol.json`, `cells["<pathway>|<setting>|default"|"p25"|"p75"]["N256"].ST`.

**Reading.**

1. The four parameters with the largest mean total index at N = 512 are `aps_share`, `q_pipe`, `q_ramp`, `sw_line` (0.330, 0.217, 0.190, 0.180).
2. The mean index is an ordering aid only; averaging indices across cells has no variance-decomposition meaning. For example, the total index of `sw_line` ranges from 0.006 to 0.580 across the cells at N = 512. The per-cell confidence intervals in Table 21 are averages of per-cell half-widths and are not intervals for the mean index.
3. Total indices sum to 1.467 and first-order indices to 0.732 at N = 512 (1.447 and 0.846 at N = 256), so interactions are substantial. Stochastic noise from the separate replicate seeds of each Saltelli row inflates both sums to an unknown extent.
4. The fixed-background check was run for four cells, and Table 23 compares only their leading parameter: the leading parameter does not change between backgrounds in any of them.

## 8. LLM red team (methodological probe, not a result)

### 8.1 Purpose and design

An adversarial red team of large-language-model runs was used to search for decision behaviour that the rule-based model omits. It was not used to estimate, calibrate or test anything, and none of its proposals was incorporated into the model.

- **Model:** Anthropic Claude Sonnet, run in October 2026. The exact model version string was not recorded in the output files.
- **Roles (5):** SFMTA grant-application staff, SFMTA capital-finance staff, SFCTA programming staff, the city's disability-affairs office together with the Mayor's Disability Council, and advocacy groups.
- **Situations (6):** an HSIP deadline in the following week; departure of the application owner; an advocacy meeting; a cost overrun after design; a Prop L amendment before the board; an SG017 allocation request.
- **Runs:** 4 independent role runs for each of the 30 role–situation cells (120 runs). Each run received the model's rule description and the evidence base and was asked for behaviours missing from the model, each with trigger, effect, cited evidence, and a candidate parameter with range.
- **Checking:** one further LLM run per cell (30 runs), instructed to act as a checker, removed proposals that the model already covers, opened the cited evidence and removed proposals it did not support, merged duplicates, kept only proposals that can be expressed as one parameter or rule change, and retained at most five per cell. Each retained proposal was classified by evidence status and by how many of the four role runs proposed it. Both steps were performed by language-model runs; no proposal was verified by a person, and agreement between runs is not independent confirmation.

### 8.2 Counts

**Table 24.** Red-team counts.

| Quantity | Value |
|---|---|
| Role runs | 120 |
| Proposals in role-run output | 469 |
| Entries recorded by the checking runs | 297 |
| Retained | 146 |
| Not retained (already modelled, merged into a retained entry, not supported by the cited evidence, not expressible as one parameter, or beyond the limit of five per cell) | 151 |
| Retained, classified as supported by a document | 13 |
| Retained, classified as plausible but without a document | 98 |
| Retained, classified as inference only | 35 |
| Retained, proposed by 1 / 2 / 3 / 4 of the four role runs | 19 / 51 / 36 / 40 |

*Source:* `results/llm-redteam/raw-proposals.json` (entries and their `proposals`); `results/llm-redteam/checked.json`, `combos[...]` (counts of `kept` and `dropped`; fields `evidence_status` and `runs_proposing` of retained entries). The classifications were made by the checking runs.

### 8.3 Hypotheses not incorporated

The retained proposals were grouped by theme. Six themes are reported as unverified hypotheses that the model does not contain:

1. district-level Prop L funds for neighbourhood transportation projects as an additional local funding route (proposed in three roles; some entries classified as document-supported);
2. shifting conduit and curb-ramp costs to the curb-ramp programme of another department instead of charging them to APS;
3. separating APS from its HSIP carrier application when time is short or the benefit–cost ratio is close to the threshold;
4. promises to follow up that absorb advocacy pressure without an application;
5. gatekeeping by SFCTA before submission and staged allocations of construction funds;
6. fault repairs displacing a restored dedicated line, with funds reprogrammed to signal controllers.

Themes 1 and 2 would add funding routes; themes 4–6 would remove or delay them. The model may therefore understate the role of small local funds and district channels and overstate the durability of a restored line. These are hypotheses for future work, not findings.
