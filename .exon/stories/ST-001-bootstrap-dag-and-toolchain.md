---
id: ST-001
type: story
title: The DAG scaffolds, lints and resolves a locked toolchain
status: approved
parent: EP-001
depends-on: []
tests: []
fixtures: []
priority: 1
updated: 2026-11-10
---

# ST-001: The DAG scaffolds, lints and resolves a locked toolchain

## Narrative

Contributes to EP-001. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-006_pipeline-bootstrap.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `d088603`, `88fa370`, `e6dc234`, `6b20afd`.

## Acceptance criteria

- AC-1: Given a fresh checkout, when `uv run snakemake -n --configfile configs/test.yaml` runs, then the plan contains `rule all` and at least one real rule and exits 0.
- AC-2: When `uv run snakemake --lint` runs, then it reports zero issues.
- AC-3: The project shall declare `p0ly-eeg` as a dependency in `pyproject.toml`, resolved through `uv.lock`; no unpinned install step exists.
- AC-4: While `configs/test.yaml` extended by `configs/test-bootstrap.yaml` (all analysis
  families off) is active, the plan shall not require analysis-family rules.

## Non-goals

- Analysis rules and real-data behavior
- Container or environment provisioning beyond `uv`

## Open questions
