---
id: ST-023
type: story
title: Temporal-generalization decoding is wired
status: draft
parent: EP-002
depends-on: []
tests: []
fixtures: []
priority: 2
updated: 2026-11-03
---

# ST-023: Temporal-generalization decoding is wired

## Narrative

Contributes to EP-002. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-030_temporal-decoding.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `dc845a1`.

## Acceptance criteria

- AC-1: When `analysis.run_decoding` is enabled, then `decoding_subject` and `run_decoding` are planned with their config block.
- AC-2: Label guards and the group `n_splits`/`seed` consistency check shall fail at parse time when violated.
- AC-3: Outputs shall land under `group_analysis/decoding/{cohort}/{condition}/`.

## Non-goals

- Classifier implementations (library work)

## Open questions

