---
id: T-020
type: task
title: Cluster-permutation statistics produce a tested TFR result
status: draft
parent: ST-019
depends-on: []
owns: [Snakefile, scripts/tfr_cluster.py, configs/default.yaml, configs/test.yaml]
tests: []
priority: 3
updated: 2026-11-03
---

# T-020: Cluster-permutation statistics produce a tested TFR result

## Goal

Cluster-permutation statistics produce a tested TFR result.

## Context

- ST-019 (parent story)
- `../p0ly/scrum/01_Backlog/US-026_tfr-cluster-stats.md`
- work commit `6e3cabb`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-019 AC-1, AC-2, AC-3
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Alternate correction methods
- Trial-level inference (see EP-004)

## Done

`uv run snakemake -n -R run_tfr_cluster --configfile configs/test.yaml`

## Progress notes

## Review

