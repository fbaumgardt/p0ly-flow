---
id: ST-004
type: story
title: A cleaned recording becomes a by-trial metadata table
status: approved
parent: EP-005
depends-on: []
tests: []
fixtures: []
priority: 1
updated: '2026-11-10'
---

# ST-004: A cleaned recording becomes a by-trial metadata table

## Narrative

Contributes to EP-005. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-016_compute-metadata-rule.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `f2253e7`.

## Acceptance criteria

- AC-1: Given a cleaned recording, when the DAG is planned, then `inject_metadata` has one
  job per subject — no timelock wildcard — reads
  `sub-{subject}_desc-clean-raw.fif.gz` and writes `sub-{subject}_metadata.tsv`.
- AC-2: Every file in `metadata/specs/` shall parse as a spec with column codes and event codes; the six shipped specs do.
- AC-3: Event codes shall be read from the spec, not from the rule script or a hardcoded map.
- AC-4: The table shall carry one row per trial (`Block`, `Trial`, `Onset` plus the
  spec-defined columns) and the rule shall not touch `mne.Epochs`; binding the table onto
  epochs belongs to the epoch rule (ST-005).

## Non-goals

- Metadata parsing algorithms (library work)
- Spec authoring UI
- Binding the table onto `mne.Epochs` — the epoch rule's job (ST-005)

## Open questions
