---
id: T-012
type: task
title: ICA fitting window is a config knob
status: done
parent: ST-012
depends-on: []
owns:
- scripts/preprocess.py
- configs/default.yaml
tests: []
priority: 3
updated: '2026-11-10'
---

# T-012: ICA fitting window is a config knob

## Goal

ICA fitting window is a config knob.

## Context

- ST-012 (parent story)
- `../p0ly/scrum/01_Backlog/US-022_ica-fit-window.md`
- work commit `373d966`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-012 AC-1, AC-2, AC-3
- Unit tests to write: none — the Done command is the proof

## Non-goals

- ICA algorithm parameters beyond the fit window

## Done

`uv run snakemake -n -R preprocess --configfile configs/test.yaml`

## Progress notes

- 2026-11-10 done-check: PASS — `uv run snakemake -n -R preprocess --configfile configs/test.yaml`

2026-11-10: Done `uv run snakemake -n -R preprocess --configfile configs/test.yaml`
re-ran clean. AC-1: `preprocessing.ica_fit_window` flows
`config['preprocessing']` -> `params.pp` -> `pp.preprocess_raw(...,
ica_fit_window=p.get('ica_fit_window'))` (Snakefile:794, scripts/preprocess.py:31).
AC-2: only the `preprocess` rule maps `params: pp`, so no other rule changes.
AC-3: `configs/test.yaml` ships `ica_fit_window: null`; the library applies the
documented default.

## Review

Reviewed 2026-11-10 against ST-012.
- follow-up (process): append Progress notes with the passing Done command; task still
  `draft` although the work landed (`373d966`).
- Spec fit verified: `preprocessing.ica_fit_window` reaches
  `pp.preprocess_raw(..., ica_fit_window=p.get("ica_fit_window"))`
  (scripts/preprocess.py:31) via `params: pp=config["preprocessing"]` (Snakefile:794),
  which only the `preprocess` rule maps, so AC-2 holds structurally; `configs/test.yaml`
  ships `ica_fit_window: null` and the documented default applies in the library
  (AC-3). AC-1..3 pass. Done command re-run 2026-11-10: passes.
No blockers.
