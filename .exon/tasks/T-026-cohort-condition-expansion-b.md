---
id: T-026
type: task
title: Expand condition splits and guard single-subject contrasts
status: draft
parent: ST-024
depends-on: []
owns: [Snakefile, configs/default.yaml, configs/test.yaml]
tests: []
priority: 3
updated: 2026-11-03
---

# T-026: Expand condition splits and guard single-subject contrasts

## Goal

Expand each configured condition split into group targets and refuse one-subject contrasts.

## Context

- ST-024 (parent story)
- ADR-0009
- `configs/test.yaml`
- work commit `6e3cabb`

## Acceptance

- Makes pass: ST-024 AC-1, AC-2, AC-3, AC-4
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Cross-cohort comparison outputs
- Cohort definitions computed from data

## Done

`uv run snakemake -n -R run_erp --configfile configs/test.yaml`

## Progress notes

## Review

