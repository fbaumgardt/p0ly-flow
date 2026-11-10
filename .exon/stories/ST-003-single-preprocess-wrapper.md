---
id: ST-003
type: story
title: One preprocessing rule with optional steps serves every family
status: approved
parent: EP-005
depends-on: []
tests: []
fixtures: []
priority: 1
updated: '2026-11-10'
---

# ST-003: One preprocessing rule with optional steps serves every family

## Narrative

Contributes to EP-005. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-008_preprocessing-rules.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `c51327c`, `0761dde`.

## Acceptance criteria

- AC-1: When the DAG is planned, then exactly one `preprocess` rule exists and every family reads its output; no family-specific preprocessing rule is planned.
- AC-2: While a step is disabled in `preprocessing`, its artifacts are absent from that job's outputs and params.
- AC-3: When ICA is enabled, then `desc-ica.fif.gz` and `bad_channels.json` are outputs; when it is disabled, neither is.
- AC-4: Every tunable preprocessing value shall arrive through `snakemake.params`; the script contains no default of its own.

## Non-goals

- Signal-processing implementations (ADR-0001)
- Per-analysis preprocessing variants (ADR-0004)

## Open questions
