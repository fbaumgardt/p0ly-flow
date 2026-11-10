---
id: ST-014
type: story
title: ERP subject averages, grand averages and contrasts are wired
status: draft
parent: EP-002
depends-on: []
tests: []
fixtures: []
priority: 2
updated: 2026-11-03
---

# ST-014: ERP subject averages, grand averages and contrasts are wired

## Narrative

Contributes to EP-002. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-010_erp-analysis.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `158edc0`.

## Acceptance criteria

- AC-1: When `analysis.run_erp` is enabled, then the plan contains `erp_subject`, `erp_group_average` and `run_erp` and nothing for other families.
- AC-2: Given two or more subjects, then a condition contrast is planned per configured pair.
- AC-3: If a cohort has one subject, then planning shall warn and omit that cohort's
  contrast targets while its grand averages stay plannable.
- AC-4: Outputs shall land under `group_analysis/erp/{cohort}/{condition}/`.

## Non-goals

- Statistics implementations (library work)
- Plotting

## Open questions

