---
id: ST-022
type: story
title: Neural variability across voltage and power is wired
status: draft
parent: EP-002
depends-on: []
tests: []
fixtures: []
priority: 2
updated: 2026-11-03
---

# ST-022: Neural variability across voltage and power is wired

## Narrative

Contributes to EP-002. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-029_neural-variability.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `f598e23`, `831dbfc`.

## Acceptance criteria

- AC-1: When `analysis.run_variability` is enabled, then `variability_subject` and `run_variability` are planned for both configured domains.
- AC-2: Unknown domains, empty or non-list measures shall fail at DAG parse time.
- AC-3: Outputs shall land under `group_analysis/variability/{cohort}/{condition}/`.

## Non-goals

- Alternative variability metrics

## Open questions

