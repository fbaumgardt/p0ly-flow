---
id: ARCH-1
type: architecture
title: p0ly-flow orchestration architecture
status: approved
parent: VIS-1
updated: 2026-11-03
---

# Architecture

## Context

p0ly-flow is a local Snakemake application used by scientific programmers, collaborators, and students. It reads BrainVision or BIDS recordings, declarative experiment specs, recording manifests, and participant cohort metadata; loads analysis parameters from YAML configuration; and writes subject-level and group-level artifacts beneath the configured derivatives directory. It calls the sibling `p0ly-eeg` Python library for EEG processing and analysis, but this architecture governs only the p0ly-flow repository.

## Components

- **`Snakefile`** — declares DAG topology, wildcard expansion, conditional targets, resources, and artifact paths; analysis families (erp, psd, tfr, connectivity, regression, cfc, variability, decoding) are each gated by an `analysis.run_*` switch.
- **`configs/*.yaml`** — selects inputs and analyses and supplies all tunable parameters to rules.
- **`metadata/manifest*.tsv` and cohort metadata** — enumerate recording segments before DAG construction; cohort membership comes from `data/metadata/participants.tsv`, selected by `group_aggregation.cohort_file`.
- **`metadata/specs/*.yaml`** — declaratively describe experiment markers, timelocks, and trial metadata without experiment-specific rule code.
- **`scripts/*.py`** — thin rule adapters that translate Snakemake inputs and parameters into library calls and persist returned objects.
- **`p0ly-eeg` (external component)** — owns EEG processing, analysis algorithms, statistics, reusable parsing logic, and EEG-specific reporting/visualization functions. Its internal choice of supporting libraries is outside this architecture.
- **Derivatives tree** — stores subject artifacts and `group_analysis/{timelock}/{cohort}/{condition}/` outputs for downstream consumers.

## Non-goals

- Implementing EEG signal processing, statistics, or other analysis algorithms in this repository.
- Implementing reporting or visualization logic rather than thin adapters to library-owned functionality, or deciding how provider libraries decompose their own internals.
- Real-time or online processing; the architecture supports offline batch analysis.
- Becoming a general-purpose workflow engine for data without EEG trial/data structure.
- Requiring manual human-in-the-loop artifact inspection for a normal run.

## Boundaries

- Rule scripts may translate configuration, resolve declared inputs, call library functions, and persist results; they must not implement EEG processing or statistical algorithms — check: architecture review of `scripts/*.py`, with an import/dependency lint if a practical rule set is established.
- p0ly-flow owns workflow filesystem layout and path composition; library calls receive resolved sources rather than config-derived path fragments — check: inspect p0ly-eeg call signatures used by `scripts/*.py` and reject config/path-building logic added to the library solely for workflow layout.
- Runtime tunables enter rules through Snakemake configuration and `snakemake.params`, not hardcoded script constants. Known optional keys may be omitted; unrecognized keys must fail before execution. The known-key set is derived from the rule scripts (the consumers are ground truth), not a parallel schema file — check: at DAG parse time, validate the configuration against the script-derived known-key set so `snakemake -n` fails on misspelled optional keys, with a static drift check rejecting declared-but-never-read keys.
- The exact YAML file named by `metadata.experiment_spec` is canonical for that run; no synchronization with similarly named files inside dependencies is assumed. Every run records per-subject provenance — the resolved spec's path, full contents, and content hash, plus the p0ly-eeg revision — in a sidecar JSON alongside that subject's artifacts — check: rerun a subject after editing the spec and confirm the sidecar changes.
- Normal processing and analysis execution must be reachable from Snakemake rules. Only utilities that generate parse-time inputs or support development/provenance inspection may run standalone — check: classify new executable scripts during review and document their exception; keep artifact-transforming analysis steps in the DAG.
- This repository's architecture must not prescribe p0ly-eeg-internal APIs or implementation choices beyond the interface p0ly-flow consumes — check: architecture and ADR review.
- Editable sibling dependencies are permitted for co-development, but a reproducible/shared analysis environment must identify an immutable p0ly-eeg revision or release rather than relying on a mutable checkout — check: inspect dependency source and recorded source revision for the environment; the exact provenance mechanism is an implementation choice.

## Quality priorities

1. **Scientific correctness** — outputs must represent the requested computation faithfully; no convenience or performance gain may compromise results.
2. **Reproducibility/provenance** — inputs, parameters, and artifact transformations must remain traceable so runs can be explained and repeated.
3. **Explicit failure behavior** — invalid or impossible analyses must fail loudly or be omitted explicitly from targets, never disguised as successful empty outputs.
4. **Configuration-only extensibility** — routine experiment and analysis changes should require configuration or declarative metadata, not DAG or algorithm edits.
5. **Execution efficiency** — avoid redundant work where doing so does not weaken the higher priorities.

Trade-off check: tests should include known-result scientific cases, rerun/provenance checks, and invalid-input cases; performance optimizations require evidence that those checks still pass.

## Active ADRs

- ADR-0001 — Separate orchestration from the EEG library (independent testing and explicit repository responsibilities).
- ADR-0002 — Declarative YAML experiment specs (new experiments without experiment-specific pipeline code).
- ADR-0003 — uv for dependency and run management (one locked Python toolchain).
- ADR-0004 — Optional preprocessing steps (explicit partial chains without hidden no-ops).
- ADR-0005 — Persist fitted ICA only when ICA runs (component provenance without misleading placeholders).
- ADR-0006 — Pipeline owns source path resolution (one owner for workflow layout).
- ADR-0007 — Manifest-driven segment ingestion (deterministic variable segment sets at DAG-parse time).
- ADR-0008 — Epoch windows live in pipeline config (analysis tuning stays separate from experiment structure).
- ADR-0009 — Separate ERP subject, grand-average, and contrast rules (clear QC artifacts and scheduling).
- ADR-0010 — Library-backed reporting through thin adapters (presentation behavior stays reusable and tested).
- ADR-0011 — Immutable library source for reproducible runs (mutable editable checkouts are development-only).
- ADR-0012 — Reject unknown configuration keys (typos cannot silently skip processing).
- ADR-0013 — Limit standalone utilities to out-of-run roles (parse-time and development tools do not bypass analysis provenance).

## Open questions

- [x] Components state `group_analysis/{timelock}/{cohort}/` but VIS-1 and every implemented DAG path use `{timelock}/{cohort}/{condition}` → Decided 2026-11-03: add `{condition}`; Components updated.
- [x] What artifact holds run provenance → Decided 2026-11-03: per-subject sidecar JSON alongside the subject's artifacts, recording the spec path + full contents + hash and the p0ly-eeg revision, on every run. Implementation pending (ADR-0002/ADR-0011 follow-ups).
- [x] Where does unknown-key validation run → Decided 2026-11-03: DAG parse time; known-key set derived from the rule scripts (scripts are ground truth; a parallel `config.schema.yaml` was rejected as a drift risk the same day). Implementation pending (ADR-0012 follow-up).
- [x] Components precision → Decided 2026-11-03: cohort metadata pointed at `data/metadata/participants.tsv` + `group_aggregation.cohort_file`; analysis families and `analysis.run_*` gates added to the Snakefile bullet.

Code validation found implementation gaps for immutable library-source capture, configured-spec hashing, comprehensive unknown-key validation, and AGENTS.md wording; these are recorded as follow-up work in the relevant ADRs rather than unresolved architectural choices.
