---
id: ST-002
type: story
title: Manifest rows become planned ingestion jobs
status: approved
parent: EP-001
depends-on: []
tests: []
fixtures: [data/raw/sub-001/sub-001_task-dmss.vhdr, data/raw/sub-001/sub-001_task-rest.vhdr, data/raw/bids]
priority: 1
updated: 2026-11-10
---

# ST-002: Manifest rows become planned ingestion jobs

## Narrative

Contributes to EP-001. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-007_ingestion-rules.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `b409dd8`, `54c96ac`, `54fb296`.

## Acceptance criteria

- AC-1: Given a manifest listing a BrainVision recording, when the DAG is planned, then
  `raw_ingestion` has one job per manifest subject, covering that subject's manifest
  rows. (No session level exists in the manifest schema; parked in the inbox.)
- AC-2: When the manifest names a BIDS directory instead, then the same rule ingests it without a second rule or a code switch.
- AC-3: If a manifest row points at a missing file, then planning fails naming that file instead of planning an empty input.
- AC-4: Ingested recordings shall land under the derivatives tree, not in `data/raw/`.
- AC-5: The subject set shall come from the manifest, not from config: adding a row for a
  new subject plans that subject's job with no config edit, and a row whose subject is
  absent from the manifest plans nothing.

## Non-goals

- Multi-run BIDS layouts: one segment per recording (ADR-0007)
- Library-side file reading
- A `subjects` key in config: the manifest is the register, and a second list would let
  the two drift apart

## Open questions
