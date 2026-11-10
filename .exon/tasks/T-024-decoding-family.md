---
id: T-024
type: task
title: Temporal-generalization decoding is wired
status: draft
parent: ST-023
depends-on: []
owns: [Snakefile, scripts/decoding_subject.py, scripts/run_decoding.py, configs/default.yaml, configs/test.yaml]
tests: []
priority: 3
updated: 2026-11-03
---

# T-024: Temporal-generalization decoding is wired

## Goal

Temporal-generalization decoding is wired.

## Context

- ST-023 (parent story)
- `../p0ly/scrum/01_Backlog/US-030_temporal-decoding.md`
- work commit `dc845a1`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-023 AC-1, AC-2, AC-3
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Classifier implementations (library work)

## Done

`uv run snakemake -n -R run_decoding --configfile configs/test.yaml`

## Progress notes

## Review

