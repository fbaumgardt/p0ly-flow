---
id: ST-019
type: story
title: Cluster-permutation statistics produce a tested TFR result
status: draft
parent: EP-002
depends-on: []
tests: []
fixtures: [data/raw/sub-002/sub-002_task-dmss.vhdr, metadata/manifest.test.tsv]
priority: 2
updated: 2026-11-03
---

# ST-019: Cluster-permutation statistics produce a tested TFR result

## Narrative

Contributes to EP-002. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-026_tfr-cluster-stats.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `6e3cabb`.

## Acceptance criteria

- AC-1: When cluster stats are enabled, then `run_tfr_cluster` is planned with its threshold and iteration count from config.
- AC-2: The rule shall refuse a cohort with fewer than two subjects, because the test is a one-sample group test.
- AC-3: Outputs shall record the observed statistic and the sign-flip null.

## Non-goals

- Alternate correction methods
- Trial-level inference (see EP-004)

## Open questions

