---
id: T-015
type: task
title: Wire ERP condition contrast with the two-subject guard
status: draft
parent: ST-014
depends-on: []
owns: [Snakefile, scripts/erp.py, configs/default.yaml, configs/test.yaml]
tests: []
priority: 3
updated: 2026-11-03
---

# T-015: Wire ERP condition contrast with the two-subject guard

## Goal

Plan `run_erp` for configured condition pairs and refuse a one-subject cohort.

## Context

- ST-014 (parent story)
- ADR-0009
- `scripts/erp.py`
- work commit `158edc0`

## Acceptance

- Makes pass: ST-014 AC-1, AC-2, AC-3, AC-4
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Statistics implementations (library work)
- Plotting

## Done

`uv run snakemake -n -R run_erp --configfile configs/test.yaml`

## Progress notes

## Review

