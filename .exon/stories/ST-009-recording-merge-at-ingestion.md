---
id: ST-009
type: story
title: Segments of one recording merge at ingestion
status: approved
parent: EP-001
depends-on: []
tests: []
fixtures: []
priority: 3
updated: 2026-11-10
---

# ST-009: Segments of one recording merge at ingestion

## Narrative

Contributes to EP-001. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-009_recording-merge.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.

Reconstructed from the vault story; the flow commits do not tag it, so the slice is the ingestion hook only.

## Acceptance criteria

- AC-1: Given several BrainVision segments for one subject and session, when the DAG is planned, then one ingestion job covers them and produces one recording.
- AC-2: Preprocessing shall receive the merged recording as its only input for that subject and session.
- AC-3: Merging shall be a library call; the rule script passes segments and writes the result.

## Non-goals

- Cross-session merging
- Reordering segments by content

## Open questions
