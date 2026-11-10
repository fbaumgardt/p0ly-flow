---
id: T-004
type: task
title: A cleaned recording becomes a by-trial metadata table
status: done
parent: ST-004
depends-on: []
owns:
- Snakefile
- scripts/parse_metadata.py
- metadata/specs/dmss.yaml
- metadata/specs/dotprobe.yaml
tests: []
priority: 3
updated: '2026-11-10'
---

# T-004: A cleaned recording becomes a by-trial metadata table

## Goal

A cleaned recording becomes a by-trial metadata table.

## Context

- ST-004 (parent story)
- `../p0ly/scrum/01_Backlog/US-016_compute-metadata-rule.md`
- work commit `f2253e7`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-004 AC-1, AC-2, AC-3, AC-4
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Metadata parsing algorithms (library work)
- Spec authoring UI

## Done

`uv run snakemake -n -R inject_metadata --configfile configs/test.yaml`

## Progress notes

- 2026-11-10 done-check: PASS — `uv run snakemake -n -R inject_metadata --configfile configs/test.yaml`

2026-11-10: Done `uv run snakemake -n -R inject_metadata --configfile configs/test.yaml`
re-ran clean. AC-1: one `inject_metadata` job per subject, no timelock wildcard, reads
`desc-clean-raw.fif.gz`, writes `sub-{subject}_metadata.tsv` (Snakefile:802). AC-2/3:
all six `metadata/specs/*.yaml` parse and event codes come from `ExperimentSpec.from_yaml`
(scripts/parse_metadata.py). AC-4: one row per trial via `parse_metadata`, no
`mne.Epochs` touch. Follow-up carried in the Review section: T-004 `owns` should list
all six spec files.

## Review

Reviewed 2026-11-10 against ST-004 and ADR-0001.
- follow-up (artifact): `f2253e7` added four spec files outside this task's
  `owns`: `metadata/specs/igt.yaml`, `intwm.yaml`, `mgsearch.yaml`, `simonfb.yaml`
  (only dmss/dotprobe are listed), yet ST-004 AC-2 requires all six shipped specs to
  `owns` (only dmss/dotprobe listed), yet ST-004 AC-2 requires all six shipped specs to
  parse. Widen `owns` to the six spec files (task is draft, may be edited).
- Spec fit verified: one `inject_metadata` job per subject, no timelock wildcard
  (Snakefile:802); reads `desc-clean-raw`, writes `sub-{subject}_metadata.tsv`;
  event codes come from `ExperimentSpec` (`scripts/parse_metadata.py`), no
  `mne.Epochs` touch. ST-004 AC-1..4 pass; empty-annotation fail-loud is ST-013 AC-4.
No blockers.
