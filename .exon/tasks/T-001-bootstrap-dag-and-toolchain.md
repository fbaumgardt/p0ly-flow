---
id: T-001
type: task
title: The DAG scaffolds, lints and resolves a locked toolchain
status: approved
parent: ST-001
depends-on: []
owns: [Snakefile, pyproject.toml, uv.lock, configs/default.yaml, configs/test.yaml, configs/test-bootstrap.yaml, profiles/local/config.yaml, envs/snakemake.yaml]
tests: []
priority: 3
updated: 2026-11-10
---

# T-001: The DAG scaffolds, lints and resolves a locked toolchain

## Goal

The DAG scaffolds, lints and resolves a locked toolchain.

## Context

- ST-001 (parent story)
- `../p0ly/scrum/01_Backlog/US-006_pipeline-bootstrap.md`
- work commit `d088603`
- work commit `88fa370`
- work commit `e6dc234`
- work commit `6b20afd`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-001 AC-1, AC-2, AC-3, AC-4
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Analysis rules and real-data behavior
- Container or environment provisioning beyond `uv`

## Done

`uv run snakemake -n --configfile configs/test.yaml`

## Progress notes

2026-11-10 — added `configs/test-bootstrap.yaml` (analysis toggles off, chained after
`configs/test.yaml`) so AC-4 is checkable against the current tree:
`uv run snakemake -n --configfile configs/test.yaml configs/test-bootstrap.yaml` plans
only raw_ingestion/preprocess/inject_metadata/epoch — zero analysis-family rules.

## Review

Reviewed 2026-11-10 (EP-001 branch review, `ingestion` merged to main at 116aafc).
- Done command re-run: `uv run snakemake -n --configfile configs/test.yaml` exits 0.
- AC-2: `uv run snakemake --lint` clean.
- AC-3: `p0ly-eeg` in `pyproject.toml` deps, editable path dep, resolved via `uv.lock`.
- should-fix (spec, not code): AC-4 is stale — `configs/test.yaml` now sets all
  `analysis.run_*: true` (EP-002 work), so the full plan *does* require analysis-family
  rules. Amend AC-4 (draft) to the intent that motivated it, e.g. a families-off plan
  exists, or scope it to pre-EP-002.
