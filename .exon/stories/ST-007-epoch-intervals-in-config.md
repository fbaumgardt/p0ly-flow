---
id: ST-007
type: story
title: Epoch windows are configuration, not spec content
status: approved
parent: EP-005
depends-on: []
tests: []
fixtures: []
priority: 3
updated: '2026-11-10'
---

# ST-007: Epoch windows are configuration, not spec content

## Narrative

Contributes to EP-005. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-021_epoching-intervals-to-config.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `4d337cc`, `55eb5f1`.
AC-4 landed 2026-11-10 in `116aafc`: config-extra interval keys fail `snakemake -n`
naming the key, the spec path and the spec's timelocks; unconfigured spec timelocks
are dropped from the epoch expansion at parse time with a stderr warning (Snakemake 9
swallows `warnings.warn`, so the nag is a stderr write). The library's
`validate_intervals` epoch-boundary call stays as the second guard.

## Acceptance criteria

- AC-1: `epoching.intervals` shall define one interval per timelock in config; the epoch rule reads it via params.
- AC-2: No spec file shall contain an episode or baseline interval.
- AC-3: Changing one interval in config shall change that timelock's planned params and nothing else.
- AC-4: If `epoching.intervals` names a timelock the spec does not declare, then
  `uv run snakemake -n` shall fail naming both the key and the spec's timelocks; a spec
  timelock with no configured interval shall plan with a warning instead of failing.

## Non-goals

- Timelock naming or adding new timelocks (a later story)
- The asymmetry itself: running a subset of the spec's timelocks stays valid, so only
  config-extra keys fail (ADR-0008)

## Open questions
