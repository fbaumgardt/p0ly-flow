---
id: ST-017
type: story
title: Connectivity graphs and a subject-unit contrast are wired
status: draft
parent: EP-002
depends-on: []
tests: []
fixtures: []
priority: 2
updated: 2026-11-03
---

# ST-017: Connectivity graphs and a subject-unit contrast are wired

## Narrative

Contributes to EP-002. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-013_connectivity.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `8756e03`, `3219441`, `705743b`.

## Acceptance criteria

- AC-1: When `analysis.run_connectivity` is enabled, then `connectivity_subject`, `connectivity_group_average` and `run_connectivity` are planned.
- AC-2: A subject-unit contrast rule shall exist and take its mode, job count and Fisher-z setting from config.
- AC-3: Outputs shall land under `group_analysis/connectivity/{cohort}/{condition}/`.

## Non-goals

- Graph-theoretic metric implementations (library work)

## Open questions

