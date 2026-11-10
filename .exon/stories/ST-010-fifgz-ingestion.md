---
id: ST-010
type: story
title: Ingested recordings are persisted as .fif.gz
status: approved
parent: EP-001
depends-on: []
tests: []
fixtures: []
priority: 4
updated: 2026-11-10
---

# ST-010: Ingested recordings are persisted as .fif.gz

## Narrative

Contributes to EP-001. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-018_ingestion-fifgz-retrofit.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.

Reconstructed from the vault story; the retrofit is not separately tagged in flow commits.

## Acceptance criteria

- AC-1: Ingestion output shall be a `.fif.gz` recording under the derivatives tree.
- AC-2: Preprocessing shall read `.fif.gz` and need no BrainVision reader of its own.
- AC-3: Both the dry-run and `--lint` shall pass with this layout.

## Non-goals

- Changing the raw input format
- Compression tuning

## Open questions
