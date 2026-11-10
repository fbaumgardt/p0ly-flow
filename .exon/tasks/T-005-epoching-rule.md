---
id: T-005
type: task
title: Epoching runs per subject and timelock from spec-driven events
status: done
parent: ST-005
depends-on: []
owns:
- Snakefile
- scripts/epoch.py
- configs/default.yaml
tests: []
priority: 3
updated: '2026-11-10'
---

# T-005: Epoching runs per subject and timelock from spec-driven events

## Goal

Epoching runs per subject and timelock from spec-driven events.

## Context

- ST-005 (parent story)
- `../p0ly/scrum/01_Backlog/US-017_epoching-by-spec-rule.md`
- work commit `9bb6117`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-005 AC-1, AC-2, AC-3
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Epoching math (library work)
- Trial rejection policy changes

## Done

`uv run snakemake -n -R epoch --configfile configs/test.yaml`

## Progress notes

- 2026-11-10 done-check: PASS — `uv run snakemake -n -R epoch --configfile configs/test.yaml`

2026-11-10: Done `uv run snakemake -n -R epoch --configfile configs/test.yaml` re-ran
clean (8 epoch jobs, 4 timelocks x 2 subjects). AC-1: `epoch` plans per subject and
`_TIMELOCKS` from the spec, reading the metadata TSV (Snakefile:834). AC-2:
interval/baseline/rejection arrive via `snakemake.params` (`config['epoching']`).
AC-3: no event-code table in scripts/epoch.py.

## Review

Reviewed 2026-11-10 against ST-005 and ADR-0008.
- follow-up (process): append Progress notes with the passing Done command and set
  `status: done`; work landed in `9bb6117` but the task is still `draft`.
- Spec fit verified: `epoch` plans one job per subject × `_TIMELOCK` from the spec
  (Snakefile:834, `_TIMELOCKS` Snakefile:28); interval/baseline/rejection arrive via
  `snakemake.params` (`config['epoching']`, Snakefile:870-875); no event-code table in
  `scripts/epoch.py`. ST-005 AC-1..3 pass. Done command re-run 2026-11-10: passes.
No blockers.
