---
id: ST-024
type: story
title: Cohorts and conditions expand as wildcard dimensions
status: draft
parent: EP-003
depends-on: []
tests: []
fixtures: [data/metadata/participants.tsv, metadata/manifest.test.tsv]
priority: 2
updated: 2026-11-03
---

# ST-024: Cohorts and conditions expand as wildcard dimensions

## Narrative

Contributes to EP-003. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-015_cohort-condition-expansion.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `6e3cabb`.

## Acceptance criteria

- AC-1: Cohort membership shall come from `group_aggregation.cohort_file` (`data/metadata/participants.tsv`), not from config lists.
- AC-2: Each configured condition split shall produce its own target set under `group_analysis/{timelock}/{cohort}/{condition}`.
- AC-3: Adding a cohort row to the participants file shall expand the plan with no code or config edit beyond the file.
- AC-4: A one-subject cohort shall warn at plan time and omit its contrast targets instead of emitting an empty archive, while its grand averages still plan.

## Non-goals

- Cross-cohort comparison outputs
- Cohort definitions computed from data

## Open questions

