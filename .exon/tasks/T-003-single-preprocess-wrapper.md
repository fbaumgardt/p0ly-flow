---
id: T-003
type: task
title: One preprocessing rule with optional steps serves every family
status: done
parent: ST-003
depends-on: []
owns:
- Snakefile
- scripts/preprocess.py
- configs/default.yaml
tests: []
priority: 3
updated: '2026-11-10'
---

# T-003: One preprocessing rule with optional steps serves every family

## Goal

One preprocessing rule with optional steps serves every family.

## Context

- ST-003 (parent story)
- `../p0ly/scrum/01_Backlog/US-008_preprocessing-rules.md`
- work commit `c51327c`
- work commit `0761dde`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-003 AC-1, AC-2, AC-3, AC-4
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Signal-processing implementations (ADR-0001)
- Per-analysis preprocessing variants (ADR-0004)

## Done

`uv run snakemake -n -R preprocess --configfile configs/test.yaml`

## Progress notes

- 2026-11-10 done-check: PASS — `uv run snakemake -n -R preprocess --configfile configs/test.yaml`

2026-11-10: Done `uv run snakemake -n -R preprocess --configfile configs/test.yaml`
re-ran clean (zero errors; `--lint` clean in the same session). AC-1..4 verified: single
`preprocess` rule (Snakefile:767); `desc-ica.fif.gz`/`bad_channels.json` only when
`ica_strategy` is set (`_ICA_OUT`/`_ICA_ENABLED`, Snakefile:33/15); every tunable
reaches `pp.preprocess_raw` via `snakemake.params.pp`, no script-side defaults
(scripts/preprocess.py).

## Review

Reviewed 2026-11-10 against ST-003 and ADR-0001/0004.
- follow-up (process): implementer must append Progress notes with a passing
  `uv run snakemake -n -R preprocess --configfile configs/test.yaml` and set `status: done`;
  the task is still `draft` although the work landed (`c51327c`, `0761dde`).
- Spec fit verified in plan and code: single `preprocess` rule (Snakefile:767);
  ICA outputs conditional via `_ICA_OUT` (Snakefile:33, `_ICA_ENABLED` Snakefile:15);
  `scripts/preprocess.py` routes every tunable through `snakemake.params.pp` with no
  script-side defaults — ST-003 AC-1..4 pass. Done command re-run 2026-11-10: passes.
No blockers.
