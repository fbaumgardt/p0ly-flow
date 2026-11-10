---
id: ST-020
type: story
title: CFC subject maps, cohort description and contrast are wired
status: draft
parent: EP-002
depends-on: []
tests: []
fixtures: []
priority: 2
updated: 2026-11-03
---

# ST-020: CFC subject maps, cohort description and contrast are wired

## Narrative

Contributes to EP-002. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-027_cfc-comodulograms.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `8cf5442`, `aff4492`.

## Acceptance criteria

- AC-1: When `analysis.run_cfc` is enabled, then `cfc_subject`, `cfc_group_average` and `run_cfc` are planned.
- AC-2: The subject-unit contrast shall be computed on whole difference maps, with ratios echoed into the descriptive and contrast archives.
- AC-3: Outputs shall land under `group_analysis/cfc/{cohort}/{condition}/`.

## Non-goals

- Comodulogram plotting

## Open questions

