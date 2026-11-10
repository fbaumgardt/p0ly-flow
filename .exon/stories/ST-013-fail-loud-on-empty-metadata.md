---
id: ST-013
type: story
title: Recordings without events or metadata fail loudly
status: approved
parent: EP-005
depends-on: []
tests: []
fixtures:
- data/raw/sub-001/sub-001_task-dmss.vhdr
- metadata/manifest.test.tsv
priority: 3
updated: '2026-11-10'
---

# ST-013: Recordings without events or metadata fail loudly

## Narrative

Contributes to EP-005. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-024_empty-metadata-fix.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `9d5b9f6`.

## Acceptance criteria

- AC-1: If a recording has no events matching its spec, then the run shall fail with a message naming the subject and event family, not emit an empty epoch set.
- AC-2: A fixture with an event-less recording shall exercise that guard under `configs/test.yaml`.
- AC-3: `uv run snakemake -n -c1 --configfile configs/test.yaml` shall pass.
- AC-4: If the cleaned recording yields no event annotations, `inject_metadata`
  (`scripts/parse_metadata.py`) shall fail naming the subject and spec, and no
  `sub-{subject}_metadata.tsv` shall be written (guard landed in commit `f2253e7`).

## Non-goals

- Silent skipping of empty recordings
- Changing the fixture's scientific content

## Open questions
