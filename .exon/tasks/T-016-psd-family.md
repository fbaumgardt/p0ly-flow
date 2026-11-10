---
id: T-016
type: task
title: PSD subject and group outputs are wired
status: draft
parent: ST-015
depends-on: []
owns: [Snakefile, scripts/psd_subject.py, scripts/psd_group_average.py, scripts/run_psd.py, configs/default.yaml, configs/test.yaml]
tests: []
priority: 3
updated: 2026-11-03
---

# T-016: PSD subject and group outputs are wired

## Goal

PSD subject and group outputs are wired.

## Context

- ST-015 (parent story)
- `../p0ly/scrum/01_Backlog/US-011_psd-analysis.md`
- work commit `361c6a3`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-015 AC-1, AC-2, AC-3
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Spectral parameter choices beyond what config exposes

## Done

`uv run snakemake -n -R run_psd --configfile configs/test.yaml`

## Progress notes

## Review

