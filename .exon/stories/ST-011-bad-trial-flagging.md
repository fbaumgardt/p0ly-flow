---
id: ST-011
type: story
title: Bad-trial decisions reach the epoch rule
status: approved
parent: EP-005
depends-on: []
tests: []
fixtures: []
priority: 4
updated: '2026-11-10'
---

# ST-011: Bad-trial decisions reach the epoch rule

## Narrative

Contributes to EP-005. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-020_epoching-bad-flag-refactor.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.

Reconstructed from the vault story; verified at plan level only, since no flow commit carries the tag.

## Acceptance criteria

- AC-1: When preprocessing flags bad trials, then the epoch rule shall receive those flags as an input artifact rather than recomputing them.
- AC-2: The flag artifact shall be present in the planned outputs of the epoch job.
- AC-3: The flagging decision itself stays in the library.

## Non-goals

- Flagging algorithms (library work)

## Open questions
