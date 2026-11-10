---
id: T-017
type: task
title: TFR and ITPC outputs are wired
status: draft
parent: ST-016
depends-on: []
owns: [Snakefile, scripts/tfr_subject.py, scripts/tfr_group_average.py, scripts/run_tfr.py, configs/default.yaml, configs/test.yaml]
tests: []
priority: 3
updated: 2026-11-03
---

# T-017: TFR and ITPC outputs are wired

## Goal

TFR and ITPC outputs are wired.

## Context

- ST-016 (parent story)
- `../p0ly/scrum/01_Backlog/US-012_tfr-itpc.md`
- work commit `58da231`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-016 AC-1, AC-2, AC-3
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Cluster statistics (separate story)

## Done

`uv run snakemake -n -R run_tfr --configfile configs/test.yaml`

## Progress notes

## Review

