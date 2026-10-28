# Data dictionary

## 1. Scope

The model reads one data file, `code/data/inputs.json`, passed to `run()` as a parsed dictionary (`code/model.py`, `load_inputs`); it reads no file at import. `inputs.json` is built by `code/build_inputs.py` from the SFMTA request lists, a site-attribute table and `code/data/pending76-crashes.csv`, which `code/data_prep.py` builds from DataSF crash records. This document describes both distributed files field by field, their public origins, the processing steps and known defects.

| File | Rows / objects | Bytes | SHA-256 |
|---|---|---|---|
| `code/data/inputs.json` | 74 initial sites, 41 historical arrivals, 9 snapshots, 76 pending sites | 40,192 | `f37b2885f630e8fe94d4ec9a690968e35b1ab7960f0aef5d141ff1a2218f0401` |
| `code/data/pending76-crashes.csv` | 76 rows, 30 columns | 7,047 | `1d8fdb11193bfca6fc598bfc5e0849a91cdba6551da02e280972532bd53ff760` |

The SHA-256 of `inputs.json` equals the value recorded when the experimental design was fixed before the main runs.

## 2. Codes used in both files

**Request states** (from the status labels in SFMTA's request lists):

| Code | SFMTA label | Meaning in the model |
|---|---|---|
| `C` | Candidate for in-house APS (also "Strong candidate") | Candidate: SFMTA judges in-house installation feasible; no funding identified. |
| `N` | Funding needed (for full upgrade / new poles) | Funding-needed: requires a full signal upgrade or new poles. |
| `Fi` | Pending per funded in-house APS | Funded agency-crew installation. |
| `Fs` | Pending per funded signal project | Funded through a signal project; installed with that project. |
| `I` | Installed | Installed (appears only in counts). |

`Fh` (funded through HSIP, in delivery) is a model-internal state and does not occur in the data.

**Rank**: SFMTA's published priority rank for the request (`high`, `medium`, `low`), taken from the request tables. It orders sites in local batches and set-aside selection and defines the high-priority outcome.

**Crash fields** are named `{group}_{severity}_{window}`:

- `group`: `pb` = crashes involving a pedestrian or bicyclist (DataSF collision groups BB, CC, DD, EE, FF, GG, HH and "BB CC"); `nonpb` = all other crashes (AA vehicles only, II unknown, blank); `ped` = pedestrian collision groups from the pedestrian extract, used only for a reconciliation check.
- `severity`: `KA` = fatal or severe injury; `B` = other visible injury; `C` = complaint of pain. Classes follow the Local Roadway Safety Manual crash-cost categories (Caltrans, 2026g, Appendix D).
- `window`: `w3` = 2023-01-01 to 2025-12-31; `w5` = 2021-01-01 to 2025-12-31; `w11` = 2015-01-01 to 2025-12-31.

## 3. `code/data/inputs.json`

Top level: `version` (string, `"dev"`), `history` (object), `pending76` (array).

### 3.1 `history`

Used only in runs that start in July 2022 (historical screening).

| Field | Type | Content |
|---|---|---|
| `snapshots` | array of 9 dates (YYYY-MM-DD) | Publication dates of the request lists from 2022-07-29 to 2026-06-30. The first is the initial state; the screening compares model stocks at 2023-01-03, 2023-06-30, 2024-02-20, 2024-08-21 and 2025-02-21, and the hold-out check at 2025-08-08, 2026-01-29 and 2026-06-30. |
| `initial_2022_07` | array of 74 objects | Requests pending on 2022-07-29. Fields: `key` (string, normalized intersection name), `state` (`C`, `N`, `Fi`, `Fs`), `rank` (string; `medium` where none was published). Counts: C 8, N 17, Fi 22, Fs 27. |
| `arrivals` | array of 41 objects | Requests first listed after 2022-07-29. Fields: `snapshot` (date of first appearance), `key`, `state` (C 32, Fs 6, N 3), `rank`. The model adds each arrival in the month of its snapshot (`Sim._arrivals`). |
| `observed_stocks` | object keyed by snapshot date | Counts of requests by state: `C`, `N`, `Fi`, `Fs` (integers, sites) and `I` (cumulative requests listed as installed). These are the screening targets. |

Observed stocks:

| Snapshot | C | N | Fi | Fs | I |
|---|---|---|---|---|---|
| 2022-07-29 | 8 | 17 | 22 | 27 | 30 |
| 2023-01-03 | 8 | 18 | 19 | 23 | 39 |
| 2023-06-30 | 10 | 18 | 15 | 22 | 45 |
| 2024-02-20 | 26 | 18 | 4 | 22 | 56 |
| 2024-08-21 | 26 | 19 | 1 | 19 | 62 |
| 2025-02-21 | 28 | 19 | 1 | 20 | 62 |
| 2025-08-08 | 32 | 20 | 1 | 21 | 62 |
| 2026-01-29 | 38 | 19 | 1 | 17 | 67 |
| 2026-06-30 | 35 | 18 | 2 | 21 | 69 |

### 3.2 `pending76`

The 76 requests pending on 2026-06-30; the initial population of every projection and the pool from which new requests copy attributes.

| Field | Type | Content |
|---|---|---|
| `key` | string | Intersection name as published by SFMTA (e.g. `03rd Street / 16th Street`). |
| `state` | string | State on 2026-06-30: C 35, Fs 21, N 18, Fi 2. |
| `rank` | string | `high` 14, `medium` 53, `low` 5; empty for 4 sites (Section 8). |
| `route` | string | Delivery route identified from public project documents: `fold` (11; site lies in a named, funded or planned project), `corridor` (13; a capital-programme corridor project may cover it, matched at corridor level), `unidentified` (52; no parent project found). |
| `fold` | string or null | Execution status of the 11 `fold` sites: `yes` (1; APS in scope of a funded project in construction), `likely` (2), `unverified` (4), `no_unfunded` (1; parent construction unfunded), `no_parent_done` (3; parent signal work completed 2023-04-25, 2025-02-27 and 2025-05-02 while the site remains listed). Null for other sites. |
| `sg015_corridor` | boolean | Site lies on a corridor of the SG015 signal-visibility programme (9 sites). Restricts PW1's first bundle. |
| `parent_finish` | string (YYYY-MM) or null | Nominal finish of the parent project for dated fold-in sites (2026-06, 2027-12, 2028-02, 2028-10). Undated fold-in sites receive start + 18 months in code. |
| `missing_ped_heads` | boolean | The 2024 signal inventory records no pedestrian heads, or heads on some phases only, so new countdown heads (SI18PB) are a confirmed carrier (10 sites, all in state N). |
| `crash_matched` | boolean | The site was located and crash counts computed (75 sites); false for 1 site. |
| `crashes` | object, 12 integers | `pb` and `nonpb` counts by severity (`KA`, `B`, `C`) for windows `w3` and `w5`, copied from `pending76-crashes.csv`; 0 where the source is blank. |

## 4. `code/data/pending76-crashes.csv`

One row per pending request (76 rows).

| Column | Type | Content |
|---|---|---|
| `location` | string | Intersection name, as in `pending76.key`. |
| `status_2026` | string | SFMTA status label on 2026-06-30 (`C-candidate`, `N-funding`, `F-inhouse`, `F-signal`). |
| `matched` | integer 0/1 | 1 if the intersection was located (75); 0 otherwise (1), in which case all crash columns are blank. |
| `ped_{KA,B,C}_{w3,w5,w11}` | integer, crashes | Pedestrian-group injury crashes within 50 m; used only to reconcile with an earlier independent count (`w11`). Not read by the model. |
| `pb_{KA,B,C}_{w3,w5,w11}` | integer, crashes | Pedestrian-or-bicycle injury crashes within 50 m. |
| `nonpb_{KA,B,C}_{w3,w5,w11}` | integer, crashes | All other injury crashes within 50 m. |

Totals over the 75 matched sites, 2021–2025: 240 `pb` and 379 `nonpb` crashes. The `w11` columns are not used by the model.

## 5. Original sources

| Source | Content used | Date | Access |
|---|---|---|---|
| SFMTA APS request and installed lists (SFMTA, 2020–2026) | Request names, status labels, ranks for 12 published snapshots (2020-01-03 to 2026-06-30); the model uses the 9 from 2022-07-29 onward | publication dates as listed | Published PDF lists on sfmta.com |
| DataSF, Traffic crashes resulting in injury, data set ubvf-ztfx (CCSF, n.d.) | All-mode injury crashes 2015–2025: 33,584 records with date, severity, collision group, killed and injured counts, intersection identifier and coordinates | retrieved 2026-10-26 | `https://data.sf.gov/resource/ubvf-ztfx.csv` (SoQL query selecting the listed fields for 2015-01-01 to 2025-12-31); SHA-256 of the retrieved file `9e8bfa09ec56e96837b7c0d13bf3195bd17c9d0e95526aa55298567b7b2b5571` |
| Same data set, pedestrian extract | 8,006 pedestrian-group records, used only for the reconciliation check | data as of 2026-10-07 | SoQL query on `https://data.sf.gov/resource/ubvf-ztfx.json` |
| SFMTA traffic signal inventory, DataSF ybh5-27n2 (SFMTA, 2024d) | Intersection coordinates (matched by street-network identifier) and the `PED_SIGNAL` field | data as of 2024-05-28 (latest release) | `https://data.sf.gov/api/views/ybh5-27n2/rows.csv?accessType=DOWNLOAD` |
| SFMTA project pages and capital documents (SFMTA, n.d.-a, n.d.-b, n.d.-d, n.d.-e; SFMTA, 2026c; SF Public Works, n.d.) | Parent project, funding and construction phase of fold-in and corridor sites | retrieved October 2026 | sfmta.com, sfpublicworks.org |

## 6. Raw inputs

The scripts that build the data files read their inputs from a folder `raw/` at the package root. Two of the seven files are distributed in `raw/`: the request-list history and the earlier baseline results, so that the baseline check (E0) can be rerun from the package. The other five are not distributed: two are public extracts that can be retrieved again, and three are tables compiled by the author from public documents. The model and the experiments E1–E4 need only `code/data/inputs.json`; the files not distributed are required only to rebuild the data files (`code/data_prep.py`, `code/build_inputs.py`). SHA-256 digests identify the versions used.

| File in `raw/` | Distributed in `raw/` | Code constant | Content and fields used | Source | How to obtain or rebuild | SHA-256 |
|---|---|---|---|---|---|---|
| `datasf-ubvf-ztfx-all-crash-points-2015-2025.csv` | no | `ALL` in `code/data_prep.py` | All-mode injury crashes, 2015–2025 (33,584 records): `collision_date`, `collision_severity`, `dph_col_grp`, `tb_latitude`, `tb_longitude` | DataSF, Traffic crashes resulting in injury, data set ubvf-ztfx (CCSF, n.d.) | Download `https://data.sf.gov/resource/ubvf-ztfx.csv` selecting `unique_id, collision_date, collision_severity, dph_col_grp, number_killed, number_injured, cnn_intrsctn_fkey, tb_latitude, tb_longitude` for collision dates 2015-01-01 to 2025-12-31 (limit 200,000). Retrieved 2026-10-26; later releases may revise records. | `9e8bfa09ec56e96837b7c0d13bf3195bd17c9d0e95526aa55298567b7b2b5571` |
| `datasf-ubvf-ztfx-ped-crash-points-2015-2025.csv` | no | `PED` in `code/data_prep.py` | Pedestrian collision groups, accident years 2015–2025 (8,006 records); used only for the reconciliation check | Same data set | Query `https://data.sf.gov/resource/ubvf-ztfx.json` for `unique_id, case_id_pkey, collision_date, accident_year, collision_severity, dph_col_grp, number_killed, number_injured, cnn_intrsctn_fkey, cnn_sgmt_fkey, primary_rd, secondary_rd, intersection, tb_latitude, tb_longitude, supervisor_district` with pedestrian collision groups and accident years 2015–2025. Data as of 2026-10-07. | `d8874b25ead617ae6b082c0f8681dab55b4091855b7ebb63701c64a78b8a5e40` |
| `intersections-spatial-20261022.csv` | no | `SP` in `code/data_prep.py` | One row per intersection in four analysis groups (1,046 rows); fields used: `group` (`c` = the 76 requests pending on 2026-06-30; other groups are not used), `location`, `lon`, `lat`, `crashes_50m_2015_2025` | Compiled by the author: request names matched to the SFMTA traffic signal inventory (SFMTA, 2024d) for coordinates; pedestrian injury crashes within 50 m counted from the pedestrian extract above | Rebuild by matching each pending intersection name to the signal inventory (`https://data.sf.gov/api/views/ybh5-27n2/rows.csv?accessType=DOWNLOAD`, data as of 2024-05-28) and counting pedestrian crashes 2015–2025 within 50 m. Only `lon`, `lat` affect the model; the crash column serves the reconciliation check. | `ab72c35bcc0ff3b6ef0ae55b431e523fa0c98453b7e52b6f4d88e88f1d6c28a3` |
| `countdown-lpi-pending76.csv` | no | `P76` in `code/data_prep.py` and `code/build_inputs.py` | One row per pending site (76 rows); fields used: `location`, `status_2026`, `other_corridor_project`, `countdown_status` | Compiled by the author from the signal inventory field `PED_SIGNAL` (SFMTA, 2024d), signal inventory diagrams (SFMTA, n.d.-c), project pages and the capital programme (SFMTA, n.d.-a, n.d.-b, n.d.-d, n.d.-e; SFMTA, 2026c; SF Public Works, n.d.) | Rebuild by the rules in Section 7, step 2: `countdown_status` = `no` where `PED_SIGNAL` is `NONE` or `SOME PHASES`; `other_corridor_project` beginning "possible" for corridor-level matches and "none found" where no parent project was found. | `5f37febf30ea495dbb7841abcc58e8156ef9b32ef132fcb89138b5766d4c11a7` |
| `history-long.csv` | yes | `HIST` in `code/build_inputs.py`; `SRC` in `code/baseline.py` | One row per intersection and snapshot (1,752 rows: 146 intersections × 12 snapshots, 2020-01-03 to 2026-06-30); fields used: `key`, `snapshot`, `state`, `rank` | Compiled by the author from the published SFMTA APS request and installed lists (SFMTA, 2020–2026) | Distributed. To rebuild (Section 7, step 1): parse each published list, normalize names to `key`, map status labels to `C-candidate`, `N-funding`, `F-inhouse`, `F-signal`, `INSTALLED`, `P` (listed as pending in snapshots before 2022-07-29, which carry no status detail) and `-` (not listed) and record the published rank. | `cfce6182d1d74c1f4ad0a15dd35141fe14f1b42512aeb28f7dc677a229fd1ef1` |
| `pending-2026.csv` | no | `PEND` in `code/build_inputs.py` | One row per pending site (76 rows); fields used: `location`, `rank` | Compiled by the author from the same lists | Rebuild from the 2026-06-30 list: the most recent published rank of each pending request (empty where none was published). | `08eb379a9b9a466efc9c0afc489f1f6adb668295461994be5b347f04d0ee03ce` |
| `baseline-simulation-results.json` | yes | `REF` in `code/baseline.py` | Results of the author's earlier Markov model of request-list transitions (transition rates, arrivals, backtest of installations from February 2024 to June 2026) | Earlier analysis by the author | Distributed; not regenerable from the package; used only for the E0 comparison. The baseline check uses it as the reference in the baseline check (E0), which reproduces its backtest (median 20 installations, 10–90% range 13–28, against the original 20 and 13–27); no other part of the model depends on it. | `f2110ac06c13bd0944e8b8ee8333ce1c89cc10c4fd53fef7bcff97e798235602` |

Rebuilt public extracts will differ from the digests above if DataSF has revised records since the retrieval date; the distributed `code/data/` files are the versions used for all reported results.

## 7. Processing

1. **Request histories.** The published lists were parsed into one record per intersection and snapshot. Names were normalized (case, punctuation, "Street"/"Avenue" abbreviations, known misspellings) to form `key`; status labels, including variants with missing spaces, were mapped to the codes of Section 2. Snapshot dates are publication dates, not event dates.
2. **Site attributes.** For each pending request the delivery route was classified from public project pages and capital documents (Section 5): a site named in a project's scope or limits is `fold`; a possible corridor-level match is `corridor`; otherwise `unidentified`. The execution status (`fold`) and parent finish dates were entered by hand from the same documents and are listed in `code/build_inputs.py` (`FOLD`, `PARENT_FINISH`). `missing_ped_heads` is true where the 2024 signal inventory's `PED_SIGNAL` field is `NONE` or `SOME PHASES`.
3. **Crash counts** (`code/data_prep.py`). Each crash with coordinates is assigned to every pending intersection within 50 m, using a planar approximation (111,320 m per degree of longitude × cos(latitude); 110,540 m per degree of latitude). Severity is mapped as in Section 2; collision groups as in Section 2. Counts are tabulated for the three windows. The script stops if the 2015–2025 pedestrian count of any matched site differs from an earlier independent count of the same quantity.
4. **Assembly** (`code/build_inputs.py`). Reads the request histories, the site-attribute table and `pending76-crashes.csv`; writes `inputs.json`. Historical arrivals are requests whose first appearance is after 2022-07-29 in a pending state.

Both scripts run with the Python standard library only: `python3 -I code/data_prep.py`, then `python3 -I code/build_inputs.py`. They read their inputs from `raw/`; Section 6 lists which inputs are distributed.

## 8. Known defects and limitations

- **Property-damage-only crashes are absent.** The DataSF data set contains injury crashes only, so benefit–cost ratios understate benefits.
- **Unmapped severity labels** would be counted as `C`; the retrieved file contains only the four mapped labels.
- **128 crash records lack coordinates** and are dropped.
- **Overlapping 50 m circles.** A crash near two pending intersections is counted at both; 50 m is not the HSIP influence area, which is why the model applies `f_aff`.
- **One unmatched site** (`03rd Street / North & South Mission Bay`) has no crash counts; the model treats it according to `crash_impute`.
- **Empty rank for four sites** (`06th Avenue / Fulton`, `11th Street / Howard`, `Eddy / Fillmore`, `Great Highway / Lincoln`). `build_inputs.py` stores the empty string rather than `medium`; the model's ordering treats unknown ranks as medium (`RANK.get(..., 1)`), so ordering is unaffected, and these sites are not counted as high priority.
- **Name matching.** Histories link snapshots by normalized names; renamings not caught by the normalization would appear as a removal plus an arrival.
- **Publication dates.** State changes are dated to the list on which they first appear; the true event lies somewhere in the preceding interval.
- **Hand-classified routes.** `route`, `fold` and `parent_finish` rest on public project documents matched to sites by name; corridor matches are at corridor level and of moderate to low confidence. One parent date (`Ellis / Powell`, 2026-06) was already past at the projection start.
- **Signal inventory age.** `PED_SIGNAL` is from the May 2024 release; changes since then are not reflected. Countdown status for the other 66 sites and leading-interval status for all 76 are not public.
- **Two key formats.** `history` uses normalized keys (e.g. `03rdst|16thst`); `pending76` uses published names. The two parts are never joined in the model.

## 9. Personal data

The distributed files contain no personal data. Records are intersections identified by public street names, published status labels and ranks, and counts of crashes aggregated by intersection, group, severity and window. Both crash extractions selected only crash-level attributes (record identifiers, date, severity, collision group, counts of killed and injured, street and intersection identifiers, district and coordinates); no names, case narratives or demographic fields of the people involved were retrieved, and the distributed files contain only aggregated counts. The two distributed raw files contain intersection names, snapshot dates, published status labels, scores, ranks and High Injury Network flags (`raw/history-long.csv`) and aggregate model results (`raw/baseline-simulation-results.json`). Requesters of APS installations are not identified in any file.
