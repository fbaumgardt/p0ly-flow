---
id: T-013
type: task
title: Recordings without events or metadata fail loudly
status: done
parent: ST-013
depends-on: []
owns:
- scripts/parse_metadata.py
- scripts/epoch.py
- scripts/create_fixture.py
- configs/test.yaml
tests: []
priority: 3
updated: '2026-11-10'
---

# T-013: Recordings without events or metadata fail loudly

## Goal

Recordings without events or empty metadata fail loudly.

## Context

- ST-013 (parent story)
- `../p0ly/scrum/01_Backlog/US-024_empty-metadata-fix.md`
- work commit `9d5b9f6`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-013 AC-1, AC-2, AC-3, AC-4
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Silent skipping of empty recordings
- Changing the fixture's scientific content

## Done

`uv run snakemake -n -c1 --configfile configs/test.yaml`

## Progress notes

- 2026-11-10 done-check: PASS — `uv run snakemake -n -c1 --configfile configs/test.yaml`

2026-11-10: Done `uv run snakemake -n -c1 --configfile configs/test.yaml` re-ran
clean (all-timelock dry-run, 21 planned jobs at full DAG). AC-1: scripts/epoch.py fails
on 0 epochs naming the timelock, the spec's wanted codes and the codes present in the
raw. AC-2: the event-less dmss fixture (data/raw/sub-001/sub-001_task-dmss.vhdr) is
planned under configs/test.yaml. AC-3: passed. AC-4: scripts/parse_metadata.py fails
on an empty event frame naming the raw and the spec before writing any TSV.
Follow-up carried in the Review section: metadata/manifest.test.tsv gained a sub-002
row in 6e3cabb with no change request — reconcile, does not affect the guard scenario.

## Review

Reviewed 2026-11-10 against ST-013.
- should-fix (protected fixture): `metadata/manifest.test.tsv` (listed under ST-013
  `fixtures:`) gained a sub-002 row in `6e3cabb` (US-015/026 enablement) with no change
  request. The change predates the story's fixture list, so likely an ordering artifact
  of the backfill — confirm the sub-001 guard scenario is unchanged and reconcile
  (retroactive CR or trim the `fixtures:` list).
- Spec fit verified: `scripts/parse_metadata.py` fails naming the raw and spec on 0
  event annotations before writing (AC-4, `f2253e7`); `scripts/epoch.py` fails on 0
  epochs naming the timelock, wanted codes and present codes (AC-1); the event-less
  dmss fixture is planned under `configs/test.yaml` (AC-2). Done command
  `uv run snakemake -n -c1 --configfile configs/test.yaml` re-run 2026-11-10: passes.
No blockers beyond the fixture reconciliation.
