---
id: T-007
type: task
title: Epoch windows are configuration, not spec content
status: done
parent: ST-007
depends-on: []
owns:
- Snakefile
- scripts/epoch.py
- scripts/preprocess.py
- configs/default.yaml
- metadata/specs/dmss.yaml
tests: []
priority: 3
updated: '2026-11-10'
---

# T-007: Epoch windows are configuration, not spec content

## Goal

Epoch windows are configuration, not spec content.

## Context

- ST-007 (parent story)
- `../p0ly/scrum/01_Backlog/US-021_epoching-intervals-to-config.md`
- work commit `4d337cc`
- work commit `55eb5f1`
- work commit `116aafc` (AC-4 parse-time cross-check)
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-007 AC-1, AC-2, AC-3, AC-4
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Timelock naming or adding new timelocks (a later story)

## Done

`uv run snakemake -n --configfile configs/test.yaml`

## Progress notes

- 2026-11-10 done-check: PASS — `uv run snakemake -n --configfile configs/test.yaml`
  plus the AC-4 negative checks in `configs/test.yaml`-derived temp copies (details
  below).

`116aafc` (2026-11-10): AC-4 landed in `Snakefile` at parse time — `_SPEC_TIMELOCKS`
cross-checked against `epoching.intervals`; config-extra keys raise a `ValueError`
naming the key, the spec path and the spec's timelocks; unconfigured spec timelocks
are dropped from `_TIMELOCKS` (which also feeds every downstream expansion) with a
stderr `Warning:` (Snakemake 9 swallows `warnings.warn`, verified by probe). The
library's `validate_intervals` call stays as the second guard.

Evidence (2026-11-10):
- Done `uv run snakemake -n --configfile configs/test.yaml`: dry-run passes,
  8 `epoch` jobs (4 timelocks × 2 subjects); `uv run snakemake --lint` clean.
- AC-4 config-extra: a `typo_lock` interval key makes `snakemake -n` exit 1 with
  `ValueError: config epoching.intervals names ['typo_lock'] but the experiment spec
  'metadata/specs/dmss.yaml' declares timelocks ['stim', 'prob', 'resp', 'fdb']`.
- AC-4 spec-extra (isolated copies of both configs, minus `fdb`): dry-run exits 0,
  prints `Warning: spec metadata/specs/dmss.yaml declares timelock 'fdb' but
  epoching.intervals configures none — epoch jobs for it are omitted from this run`,
  and plans 6 `epoch` jobs instead of 8.

## Review

Reviewed 2026-11-10 against ST-007 and ADR-0008.
- blocker: AC-4's parse-time cross-check is unlanded and claimed by no task. Verified
  2026-11-10: a config-extra interval key (`typo_lock`) exits 0 from
  `snakemake -n` (only `validate_intervals` at epoch-job runtime fails, scripts/epoch.py:31);
  a spec timelock with no configured interval is still planned (wildcards expand over
  `_TIMELOCKS`, Snakefile:28) and would KeyError at `p.intervals[p.timelock]`
  (scripts/epoch.py:37) instead of "plan with a warning". AC-1..3 pass (verified in
  plan and specs: no intervals in `metadata/specs/*.yaml`). Accepted in the Claims:
  AC-1..3 only — but the epic scope requires AC-4, so a task must own it before EP-005
  moves to review.
No other blockers; not done until AC-4 lands.
