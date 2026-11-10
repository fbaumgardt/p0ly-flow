---
id: T-021
type: task
title: CFC subject maps, cohort description and contrast are wired
status: draft
parent: ST-020
depends-on: []
owns: [Snakefile, scripts/cfc_subject.py, scripts/cfc_group_average.py, scripts/run_cfc.py, configs/default.yaml, configs/test.yaml]
tests: []
priority: 3
updated: 2026-11-03
---

# T-021: CFC subject maps, cohort description and contrast are wired

## Goal

CFC subject maps, cohort description and contrast are wired.

## Context

- ST-020 (parent story)
- `../p0ly/scrum/01_Backlog/US-027_cfc-comodulograms.md`
- work commit `8cf5442`
- work commit `aff4492`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-020 AC-1, AC-2, AC-3
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Comodulogram plotting

## Done

`uv run snakemake -n -R run_cfc --configfile configs/test.yaml`

## Progress notes

## Review

