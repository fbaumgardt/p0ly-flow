---
id: T-018
type: task
title: Connectivity graphs and a subject-unit contrast are wired
status: draft
parent: ST-017
depends-on: []
owns: [Snakefile, scripts/connectivity_subject.py, scripts/connectivity_group_average.py, scripts/connectivity_contrast.py, scripts/run_connectivity.py, configs/default.yaml, configs/test.yaml]
tests: []
priority: 3
updated: 2026-11-03
---

# T-018: Connectivity graphs and a subject-unit contrast are wired

## Goal

Connectivity graphs and a subject-unit contrast are wired.

## Context

- ST-017 (parent story)
- `../p0ly/scrum/01_Backlog/US-013_connectivity.md`
- work commit `8756e03`
- work commit `3219441`
- work commit `705743b`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-017 AC-1, AC-2, AC-3
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Graph-theoretic metric implementations (library work)

## Done

`uv run snakemake -n -R run_connectivity --configfile configs/test.yaml`

## Progress notes

## Review

