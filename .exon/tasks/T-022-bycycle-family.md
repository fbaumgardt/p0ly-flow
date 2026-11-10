---
id: T-022
type: task
title: Bycycle waveform-cycle outputs are wired
status: draft
parent: ST-021
depends-on: []
owns: [Snakefile, scripts/bycycle_subject.py, scripts/run_bycycle.py, configs/default.yaml, configs/test.yaml]
tests: []
priority: 3
updated: 2026-11-03
---

# T-022: Bycycle waveform-cycle outputs are wired

## Goal

Bycycle waveform-cycle outputs are wired.

## Context

- ST-021 (parent story)
- `../p0ly/scrum/01_Backlog/US-028_bycycle-waveforms.md`
- work commit `e9fa281` (unmerged branch us028-flow)
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-021 AC-1, AC-2, AC-3
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Cycle-detection algorithms (library work)

## Done

`uv run snakemake -n -R run_bycycle --configfile configs/test.yaml`

## Progress notes

## Review

