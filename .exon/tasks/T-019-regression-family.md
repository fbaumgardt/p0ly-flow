---
id: T-019
type: task
title: Single-trial regression outputs are wired
status: draft
parent: ST-018
depends-on: []
owns: [Snakefile, scripts/regression_subject.py, scripts/run_regression.py, configs/default.yaml, configs/test.yaml]
tests: []
priority: 3
updated: 2026-11-03
---

# T-019: Single-trial regression outputs are wired

## Goal

Single-trial regression outputs are wired.

## Context

- ST-018 (parent story)
- `../p0ly/scrum/01_Backlog/US-014_single-trial-regression.md`
- work commit `a2ff4a1`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-018 AC-1, AC-2, AC-3
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Model diagnostics and plotting

## Done

`uv run snakemake -n -R run_regression --configfile configs/test.yaml`

## Progress notes

## Review

