---
id: ST-012
type: story
title: ICA fitting window is a config knob
status: approved
parent: EP-005
depends-on: []
tests: []
fixtures: []
priority: 4
updated: '2026-11-10'
---

# ST-012: ICA fitting window is a config knob

## Narrative

Contributes to EP-005. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-022_ica-fit-window.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `373d966`.

## Acceptance criteria

- AC-1: `preprocessing.ica_fit_window` shall be read by the preprocess rule and passed as a param.
- AC-2: Changing it shall change the planned params of `preprocess` and no other rule.
- AC-3: When the key is absent, the documented default shall apply.

## Non-goals

- ICA algorithm parameters beyond the fit window

## Open questions
