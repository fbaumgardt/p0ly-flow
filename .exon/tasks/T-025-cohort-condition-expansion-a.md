---
id: T-025
type: task
title: Read cohorts from participant metadata
status: draft
parent: ST-024
depends-on: []
owns: [Snakefile, configs/default.yaml, data/metadata/participants.tsv]
tests: []
priority: 3
updated: 2026-11-03
---

# T-025: Read cohorts from participant metadata

## Goal

Replace config cohort lists with `group_aggregation.cohort_file`.

## Context

- ST-024 (parent story)
- `data/metadata/participants.tsv`
- `configs/test.yaml`
- work commit `6e3cabb`

## Acceptance

- Makes pass: ST-024 AC-1, AC-2, AC-3, AC-4
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Cross-cohort comparison outputs
- Cohort definitions computed from data

## Done

`uv run snakemake -n --configfile configs/test.yaml`

## Progress notes

## Review

