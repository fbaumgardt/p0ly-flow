---
id: ST-016
type: story
title: TFR and ITPC outputs are wired
status: draft
parent: EP-002
depends-on: []
tests: []
fixtures: []
priority: 2
updated: 2026-11-03
---

# ST-016: TFR and ITPC outputs are wired

## Narrative

Contributes to EP-002. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-012_tfr-itpc.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `58da231`.

## Acceptance criteria

- AC-1: When `analysis.run_tfr` is enabled, then `tfr_subject`, `tfr_group_average` and `run_tfr` are planned.
- AC-2: ITPC shall be produced by the same family without a second config block.
- AC-3: Outputs shall land under `group_analysis/tfr/{cohort}/{condition}/`.

## Non-goals

- Cluster statistics (separate story)

## Open questions

