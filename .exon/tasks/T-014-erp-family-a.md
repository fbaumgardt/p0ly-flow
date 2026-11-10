---
id: T-014
type: task
title: Wire ERP subject and group-average rules
status: draft
parent: ST-014
depends-on: []
owns: [Snakefile, scripts/erp_subject.py, scripts/erp_group_average.py, configs/default.yaml]
tests: []
priority: 3
updated: 2026-11-03
---

# T-014: Wire ERP subject and group-average rules

## Goal

Plan `erp_subject` and `erp_group_average` end to end from epoched inputs.

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

`uv run snakemake -n -R erp_group_average --configfile configs/test.yaml`

## Progress notes

## Review

