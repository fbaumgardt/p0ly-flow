---
id: T-002
type: task
title: Manifest rows become planned ingestion jobs
status: approved
parent: ST-002
depends-on: []
owns: [Snakefile, scripts/ingest_raw.py, configs/default.yaml]
tests: []
priority: 3
updated: 2026-11-10
---

# T-002: Manifest rows become planned ingestion jobs

## Goal

Manifest rows become planned ingestion jobs.

## Context

- ST-002 (parent story)
- `../p0ly/scrum/01_Backlog/US-007_ingestion-rules.md`
- work commit `b409dd8`
- work commit `54c96ac`
- work commit `54fb296`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-002 AC-1, AC-2, AC-3, AC-4
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Multi-run BIDS layouts: one segment per recording (ADR-0007)
- Library-side file reading

## Done

`uv run snakemake -n -R raw_ingestion --configfile configs/test.yaml`

## Progress notes

2026-11-10 — implemented manifest-derived subject universe (ST-002 AC-5):
- Manifest block (pandas import, `_MANIFEST`, `_MANIFEST_ROWS`, `_MANIFEST_SUBJECTS`,
  `_subject_sources`) moved above the cohort resolver; `rule all` ICA targets follow it.
- All six `config["subjects"]` references replaced by `_MANIFEST_SUBJECTS`; cohort
  membership check repointed mechanically (semantics stay EP-003's, error message now
  says "manifest subjects").
- `subjects:` removed from configs/default.yaml and configs/test.yaml; README configure
  step updated.

Evidence (all re-run after the change):
- `uv run snakemake -n --configfile configs/test.yaml --until raw_ingestion` → exit 0,
  2 raw_ingestion jobs (one per manifest subject).
- Manifest row for a new subject (`003`) added via config override → `rule all` plans
  `data/derivatives_test/sub-003/sub-003_desc-raw.fif.gz` with no config edit.
- `uv run snakemake -n` exit 0 on both shipped configs; `--lint` clean.
- `uv run pytest tests/` — 17 passed.

## Review

Reviewed 2026-11-10 (EP-001 branch review, `ingestion` merged to main at 116aafc).
- blocker — ST-002 AC-5 not implemented: the subject universe is still
  `config["subjects"]` (Snakefile `rule all` expands desc-raw targets from it;
  `subjects:` lists in configs/default.yaml:12 and configs/test.yaml:48). Verified:
  appending a manifest row for sub-003 plans nothing via `rule all`; the epic's success
  measure ("adding a subject row plans that subject's job with no config edit") fails.
  EP-001 scope and its resolved open question both require removing the config subject
  list and deriving the universe from manifest rows. Note: no task owns AC-5 (T-002
  lists AC-1..AC-4) — add it here when fixing.
- AC-1..AC-4 verified: Done command re-run exits 0 (2 raw_ingestion jobs, one per
  manifest subject); missing-file row fails planning naming the file
  (MissingInputException: `data/raw/sub-003/NOPE.vhdr`); outputs under the derivatives
  tree; BIDS ingested by the same rule (single BIDSPath, multi-segment BIDS guarded).
- should-fix (spec): AC-1 says "one job per manifest row with subject and session" —
  conflicts with the design (one job per subject; manifest schema has no session
  column). Amend to match EP-001 scope.
- should-fix (spec): story fixture `data/raw/sub-001/sub-001.vhdr` does not exist;
  actual fixtures are `sub-001_task-dmss.vhdr` / `sub-001_task-rest.vhdr` + `data/raw/bids`.
