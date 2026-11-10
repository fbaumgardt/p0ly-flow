---
id: ST-021
type: story
title: Bycycle waveform-cycle outputs are wired
status: draft
parent: EP-002
depends-on: []
tests: []
fixtures: []
priority: 3
updated: 2026-11-03
---

# ST-021: Bycycle waveform-cycle outputs are wired

## Narrative

Contributes to EP-002. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-028_bycycle-waveforms.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work exists on an unmerged branch: `e9fa281`.
Parked 2026-11-10: bycycle is no longer EP-002 scope (its own non-goal names this story),
so this waits for a follow-up epic once the toolchain conflict resolves.

Blocked: the work exists on branch `us028-flow` (commit e9fa281) and cannot merge until the conflicting Python version requirement is resolved. On `main` this criterion currently fails.

## Acceptance criteria

- AC-1: When `analysis.run_bycycle` is enabled, then `bycycle_subject` and `run_bycycle` are planned with their config block.
- AC-2: Outputs shall land under `group_analysis/bycycle/{cohort}/{condition}/`.
- AC-3: The rules shall not require a different Python version than the pinned toolchain.

## Non-goals

- Cycle-detection algorithms (library work)

## Open questions

