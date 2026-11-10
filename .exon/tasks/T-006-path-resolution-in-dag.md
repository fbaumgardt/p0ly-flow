---
id: T-006
type: task
title: Path assembly lives in the DAG, not the library
status: approved
parent: ST-006
depends-on: []
owns: [Snakefile, scripts/ingest_raw.py]
tests: []
priority: 3
updated: 2026-11-10
---

# T-006: Path assembly lives in the DAG, not the library

## Goal

Path assembly lives in the DAG, not the library.

## Context

- ST-006 (parent story)
- `../p0ly/scrum/01_Backlog/US-019_io-path-refactor.md`
- work commit `59a4a7c`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-006 AC-1, AC-2, AC-3
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Library-side path APIs (ADR-0006 is the decision, not a library change)

## Done

`uv run snakemake -n --configfile configs/test.yaml`

## Progress notes

## Review

Reviewed 2026-11-10 (EP-001 branch review).
- Done command re-run clean; both shipped configs plan (exit 0) — AC-3.
- AC-2: `scripts/ingest_raw.py` assembles no paths; BV gets a concrete `.vhdr` from the
  manifest, BIDS gets a pipeline-constructed `BIDSPath` (ADR-0006-conformant), output
  path via `snakemake.output`.
- AC-1: spot-checked raw_ingestion/preprocess — inputs/outputs via snakemake.
