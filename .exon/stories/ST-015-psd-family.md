---
id: ST-015
type: story
title: PSD subject and group outputs are wired
status: draft
parent: EP-002
depends-on: []
tests: []
fixtures: []
priority: 2
updated: 2026-11-03
---

# ST-015: PSD subject and group outputs are wired

## Narrative

Contributes to EP-002. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-011_psd-analysis.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `361c6a3`.

## Acceptance criteria

- AC-1: When `analysis.run_psd` is enabled, then `psd_subject`, `psd_group_average` and `run_psd` are planned.
- AC-2: Disabling the toggle shall remove exactly those rules from the plan.
- AC-3: Outputs shall land under `group_analysis/psd/{cohort}/{condition}/`.

## Non-goals

- Spectral parameter choices beyond what config exposes

## Open questions

