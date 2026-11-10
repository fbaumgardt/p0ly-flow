---
id: VIS-1
type: vision
title: p0ly-flow — reproducible EEG analysis orchestration
status: approved
updated: 2026-11-03
---

# p0ly-flow

## Problem

EEG researchers — students, collaborators and scientific programmers alike — spend too much time on auxiliary tasks instead of analysis. Three concrete pains:

1. **Data-prep friction**: getting raw recordings (BrainVision/BIDS), metadata and manifests into an analysis-ready state takes disproportionate effort before any science happens.
2. **New code vs old preprocessing**: making new analysis code work with older preprocessing scripts is brittle; each new analysis tends to fork or re-implement preprocessing.
3. **Output sprawl**: managing analysis outputs (plots, stats, derived data) across subjects, cohorts, conditions and timelocks becomes manual bookkeeping.

Existing options fail because hand-written MNE scripts entangle preprocessing with analysis and scatter outputs ad hoc, and generic workflow tools don't understand EEG trial/data structure.

## Users

- **Primary — scientific programmers**: want a playground to test new analyses appended to known-good, reproducible preprocessing.
- **Collaborators**: want to quickly iterate across parameters for a particular analysis without editing code.
- **Students**: learn EEG concepts (timelocks, conditions, single-subject vs group analysis) and practice interpreting outputs (ERPs, TFR heatmaps with stats overlays) by running the pipeline; instructional material itself lives in a separate repo.

## Goals

1. Config-only iteration: a collaborator changes analysis parameters in `configs/default.yaml`, reruns, and gets correct outputs — no code edits.
2. Known-good preprocessing as a foundation: new analyses bolt onto the existing preprocessing chain without modifying it or forking it.
3. Standardized, discoverable outputs: every analysis writes predictable containers under `data/derivatives/` organized by timelock/cohort/condition, consumable by downstream presentation tools.
4. Runnable learning substrate: students can go from raw data to interpretable single-subject and group outputs on a small dataset.

## Non-goals

- **Teaching tool**: instructional material, exercises and guided interpretation live in a separate repository that uses this pipeline; p0ly-flow stays infrastructure.
- **Analysis-code repository**: signal processing, filtering, epoching, statistics implementations belong to p0ly-eeg; rule scripts here are thin wrappers.
- **General-purpose workflow engine**: schemas and ingestion target EEG trial and data structure (BrainVision, BIDS); MEG/iEEG are possible future siblings sharing that structure, but modalities with different structure (fMRI, behavior-only) are out.
- **Presentation/reporting layer**: reporting and visualization logic follows the same boundary as every other analysis — it lives in p0ly-eeg or a dedicated third library, and rule scripts here are thin wrappers that only translate configuration into library calls and persist the returned objects. Reporting is not an extension this DAG will grow.

## Success measures

- **Headline — config-only iteration walkthrough**: a collaborator changes parameters for one analysis (e.g. TFR band or epoching window) in `configs/default.yaml`, reruns Snakemake, and obtains correct regenerated outputs with zero edits to scripts or rules.
- Extension check: adding a new analysis requires only a new thin rule script plus a config block; no changes to existing preprocessing rules.
- Output check: group outputs for a configured cohort×condition×timelock land in the documented `data/derivatives/group_analysis/` layout without manual file management.
- Learning check: a student runs the 2-subject smoke test (`configs/test.yaml`, < 60 s) and can locate and read group ERP/TFR outputs unaided.

## Constraints

- **Snakemake + uv toolchain** — DAG semantics, wildcard expansion and rerun/incremental behavior come from Snakemake; dependencies are uv-managed.
- **p0ly-eeg boundary** — all signal processing must stay in the library so preprocessing remains a stable foundation; this forces thin wrappers here.
- **BrainVision/BIDS ingestion** — raw inputs arrive in these layouts, so ingestion and schemas are built around them.
- **Config as sole parameter surface** — parameters route through `configs/default.yaml` into `snakemake.params` so collaborators never edit code.
- **Solo-maintainer, research-lab setting** — favors convention and documentation over heavyweight schema/governance infrastructure.

## Decisions

- **Decision:** vision covers p0ly-flow only, not the whole p0ly system — keeps the repository boundary clean; library-side work links out to p0ly-eeg.
- **Decision:** primary success measure is the config-only iteration walkthrough — it is the most frequent real-world interaction and exercises ingestion, preprocessing reuse and output management at once.
- **Decision:** reporting and visualization follow the analysis boundary: their logic lives in a library (p0ly-eeg or a third component — decided at the architecture level); p0ly-flow contributes only thin scripts that translate configuration into library calls and handle/store the return values. Keeps the DAG orchestrator-only and the standardized containers as the only interface presentation code uses.

## Assumptions

- **Assumption:** the three pains are architectural, not interpretive — falsified if the main time sink turns out to be interpretation or cohort/statistics design, which this architecture doesn't touch.
- **Assumption:** collaborators actually iterate via config and never need code edits — falsified if real iteration requests repeatedly require new rule logic.
- **Assumption:** reporting/visualization logic fits behind the same thin-wrapper boundary as analysis logic, consuming standardized containers — falsified if real reporting needs repeatedly require rule DAG changes rather than library-side changes.
- **Assumption:** MEG/iEEG share enough trial/data structure with EEG to fit the same schemas — falsified on first concrete MEG/iEEG ingestion attempt that needs schema changes.

## Open questions

- [x] How extensive may output-creation logic get (marimo/jupyter notebooks, HTML reports, interactive visualization)? → Resolved 2026-11-03: reporting/visualization is not a DAG concern. Its logic lives in p0ly-eeg or a third library; p0ly-flow holds only thin scripts translating configuration into calls plus storage of returned objects (see Non-goals and Decisions). Which library hosts the logic is an architecture-level choice.
