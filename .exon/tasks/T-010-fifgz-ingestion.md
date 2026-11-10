---
id: T-010
type: task
title: Ingested recordings are persisted as .fif.gz
status: approved
parent: ST-010
depends-on: []
owns: [Snakefile, scripts/ingest_raw.py]
tests: []
priority: 3
updated: 2026-11-10
---

# T-010: Ingested recordings are persisted as .fif.gz

## Goal

Ingested recordings are persisted as .fif.gz.

## Context

- ST-010 (parent story)
- `../p0ly/scrum/01_Backlog/US-018_ingestion-fifgz-retrofit.md`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-010 AC-1, AC-2, AC-3
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Changing the raw input format
- Compression tuning

## Done

`uv run snakemake -n --configfile configs/test.yaml`

## Progress notes

## Review

Reviewed 2026-11-10 (EP-001 branch review).
- Done command re-run clean; lint clean — AC-3.
- AC-1: output `sub-{subject}_desc-raw.fif.gz` under the derivatives tree.
- AC-2: `preprocess` reads `desc-raw.fif.gz`; no BrainVision reader downstream.
