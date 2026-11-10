---
id: ST-005
type: story
title: Epoching runs per subject and timelock from spec-driven events
status: approved
parent: EP-005
depends-on: []
tests: []
fixtures: []
priority: 5
updated: '2026-11-10'
---

# ST-005: Epoching runs per subject and timelock from spec-driven events

## Narrative

Contributes to EP-005. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-017_epoching-by-spec-rule.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `9bb6117`.

## Acceptance criteria

- AC-1: When the DAG is planned, then `epoch` has one job per subject and timelock, reading the metadata frame from `inject_metadata`.
- AC-2: Epoch parameters (interval, baseline, rejection) shall reach the script through `snakemake.params`.
- AC-3: The epoch script shall contain no event-code table of its own.

## Non-goals

- Epoching math (library work)
- Trial rejection policy changes

## Open questions
