---
id: T-023
type: task
title: Neural variability across voltage and power is wired
status: draft
parent: ST-022
depends-on: []
owns: [Snakefile, scripts/variability_subject.py, scripts/run_variability.py, configs/default.yaml, configs/test.yaml]
tests: []
priority: 3
updated: 2026-11-03
---

# T-023: Neural variability across voltage and power is wired

## Goal

Neural variability across voltage and power is wired.

## Context

- ST-022 (parent story)
- `../p0ly/scrum/01_Backlog/US-029_neural-variability.md`
- work commit `f598e23`
- work commit `831dbfc`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-022 AC-1, AC-2, AC-3
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Alternative variability metrics

## Done

`uv run snakemake -n -R run_variability --configfile configs/test.yaml`

## Progress notes

## Review

