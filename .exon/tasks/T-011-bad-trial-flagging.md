---
id: T-011
type: task
title: Bad-trial decisions reach the epoch rule
status: done
parent: ST-011
depends-on: []
owns:
- Snakefile
- scripts/epoch.py
- scripts/preprocess.py
tests: []
priority: 3
updated: '2026-11-10'
---

# T-011: Bad-trial decisions reach the epoch rule

## Goal

Bad-trial decisions reach the epoch rule.

## Context

- ST-011 (parent story)
- `../p0ly/scrum/01_Backlog/US-020_epoching-bad-flag-refactor.md`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-011 AC-1, AC-2, AC-3
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Flagging algorithms (library work)

## Done

`uv run snakemake -n -R epoch --configfile configs/test.yaml`

## Progress notes

- 2026-11-10 done-check: PASS — `uv run snakemake -n -R epoch --configfile configs/test.yaml`

2026-11-10: Done `uv run snakemake -n -R epoch --configfile configs/test.yaml` re-ran
clean. AC-1: bad-trial flags ride as `bad_minmax_zscore` annotations inside
`desc-clean-raw.fif.gz` — written by p0ly-eeg (preprocessing.py:185) during preprocess,
read from `raw.annotations` by scripts/epoch.py; nothing recomputed in the pipeline.
AC-2: `sub-{subject}_{timelock}_excluded_trials.csv` is a planned epoch output
(Snakefile:869). AC-3: the flagging decision lives in p0ly-eeg only.

## Review

Reviewed 2026-11-10 against ST-011 (epic open question 2026-11-03 resolution applies:
flags ride as `bad_minmax_zscore` annotations inside `desc-clean-raw.fif.gz`, not a
separate artifact).
- follow-up (process): append Progress notes with the passing Done command; task still
  `draft` although the work landed (`9bb6117` chain).
- Spec fit verified: flags are written by the library under that label
  (`p0ly-eeg` `preprocessing.py:185`), the epoch rule does not recompute them and
  reads `raw.annotations` (`scripts/epoch.py`), and the epoch job plans
  `sub-{subject}_{timelock}_excluded_trials.csv` (Snakefile:869); the decision lives in
  the library. ST-011 AC-1..3 pass.
No blockers.
