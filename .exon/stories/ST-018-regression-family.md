---
id: ST-018
type: story
title: Single-trial regression outputs are wired
status: draft
parent: EP-002
depends-on: []
tests: []
fixtures: []
priority: 2
updated: 2026-11-03
---

# ST-018: Single-trial regression outputs are wired

## Narrative

Contributes to EP-002. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-014_single-trial-regression.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `a2ff4a1`.

## Acceptance criteria

- AC-1: When `analysis.run_regression` is enabled, then `regression_subject` and `run_regression` are planned.
- AC-2: Regression terms and domains shall come from config, not from the script.
- AC-3: Outputs shall land under `group_analysis/regression/{cohort}/{condition}/`.

## Non-goals

- Model diagnostics and plotting

## Open questions

