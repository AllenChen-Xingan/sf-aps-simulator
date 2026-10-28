# Funding and coordination pathways for accessible pedestrian signals in San Francisco: an agent-based model

This package contains the code, documentation, input data and results of an agent-based model (ABM) that compares how San Francisco could convert pending requests for accessible pedestrian signals (APS) into funded installations. The model accompanies a 2026 policy analysis of APS delivery in San Francisco. It is a scenario comparison under deep uncertainty, not a forecast.

## What the model does

The San Francisco Municipal Transportation Agency (SFMTA) keeps a list of crossings where residents have requested APS. Since 2023, crossings that need new funding have rarely received it. The model follows the 76 crossings pending in June 2026, and new requests, month by month for ten years. In each month, SFMTA's capital-budget and grant staff decide whether to prepare a funding application; applications then pass through rule-based venues (federal HSIP rounds, the local Prop L sales-tax programme, the city General Fund and existing signal projects) to design, construction and installation.

Seven pathways (current practice and six alternatives) are compared under six alternative explanations of the observed stall, across 1,000 combinations of uncertain parameters with 20 replicates each. The analysis asks which pathways outperform current practice across these conditions, under what conditions money flows, and which uncertain inputs matter most.

A one-page summary of intended use and limitations is in [`MODEL_CARD.md`](MODEL_CARD.md).

## Contents

| Path | Contents |
|---|---|
| `MODEL_CARD.md` | Intended use, uses the model is not suited to, structure in XLRM form, main results and limitations |
| `docs/ODD+D.md` | Full model description following the ODD protocol (Grimm et al., 2020) with the ODD+D extension for human decisions (Müller et al., 2013): every state variable, schedule and submodel, with code locations |
| `docs/TRACE.md` | Development, testing and analysis record following TRACE (Grimm et al., 2014) |
| `docs/experiment-protocol.md` | Experimental protocol: checksums, seeds, criteria, experiments E0–E4 |
| `docs/results.md` | All results, with the results file behind every number |
| `docs/parameters.md`, `data/parameters.csv` | All 98 parameters: range, default, unit, settings where active, source category and source |
| `docs/data-dictionary.md` | Input files, fields, provenance and processing |
| `docs/actors-and-evidence.md` | Evidence base for every actor, relationship and rule, with public sources |
| `docs/STRESS-ABS.md` | STRESS-ABS reporting checklist (Monks et al., 2019) mapped to this package |
| `docs/reproducibility.md` | Environment, verification checks, rerun comparison, hardware and run times |
| `docs/references.md` | All references (APA 7), with DOIs checked against Crossref |
| `code/` | Model and experiment code (Python) and input data |
| `environment/` | Python version and pinned dependencies |
| `results/` | Summary results of every experiment, figures and the adversarial-review records |
| `reproduce.sh` | One-command reproduction |
| `SHA256SUMS` | Checksums of every file in the package |

## Reproducing the results

Requirements: Python (version in `environment/python-version.txt`), a POSIX shell, and about 4.5 hours on 8 CPU cores for the full set of experiments.

```bash
./reproduce.sh --quick      # environment, checksums, self-tests, baseline check and one sensitivity cell (~5 min)
./reproduce.sh              # all main experiments, compared field by field with results/
./reproduce.sh --e4-full    # additionally reruns the complete sensitivity analysis
```

The script builds a fresh virtual environment from the pinned dependencies, copies `code/` to a working directory, runs each experiment and compares every regenerated summary with the files in `results/`. Nothing in `code/` or `results/` is modified. Results do not depend on the number of worker processes. Large raw outputs (per-run tables and shards) are not included; the script regenerates them. Details and measured run times are in `docs/reproducibility.md`.

## Versions and checksums

The reported results were produced by the code in `code/`. The combined fingerprint of the model, parameter and input files is `e0f4869e2c32e15f2f3b905a242bcbaa09f7102cf6aaf151acf3e2ac11dff18f`; file-level checksums are in `docs/experiment-protocol.md` §2 and `SHA256SUMS`.

## Data, privacy and sources

All inputs come from public documents and data sets (listed in `docs/data-dictionary.md` and `docs/references.md`) and from one interview with SFMTA staff, cited as personal communication. The package contains no personal information about the interviewee or any other individual. Public documents are cited, not redistributed.

## Use of AI tools

The model code, the experiment scripts and this documentation were developed by the author with the assistance of Anthropic's Claude models, which drafted code and text under the author's design and direction and checked the documentation against the code. A large language model was also used as an adversarial reviewer to search the design for omitted mechanisms; its proposals were recorded as unverified hypotheses and not incorporated into the model (`docs/TRACE.md` §4.5; `results/llm-redteam/`).

## Licence and citation

Code (`code/`, `reproduce.sh`): MIT licence (`LICENSE`). Documentation, data and results: CC BY 4.0 (`LICENSE-docs`). Citation metadata: `CITATION.cff`.

> Chen, A. (2026). *An agent-based model of funding and coordination pathways for accessible pedestrian signals in San Francisco* [Computer software and documentation]. https://allenchen-xingan.github.io/sf-aps-simulator/replication/
