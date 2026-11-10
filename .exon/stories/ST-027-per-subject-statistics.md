---
id: ST-027
type: story
title: A single subject can be tested on its own
status: draft
parent: EP-004
depends-on: []
tests: [tests/test_subject_stats.py]
fixtures: []
priority: 4
updated: 2026-11-03
---

# ST-027: A single subject can be tested on its own

## Narrative

Contributes to EP-004. Created from an approved ADR follow-up, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Decision source: ADR-0009.

Open work: ADR-0009 records the seam and requires an inference-level decision before implementation.

## Acceptance criteria

- AC-1: Given a one-subject cohort, when per-subject statistics are enabled, then a result is produced for that subject.
- AC-2: A group-level claim that needs two subjects shall still fail with fewer than two.
- AC-3: The story shall state which unit is exchangeable and why, before the rule is implemented.

## Non-goals

- Replacing group inference with subject-level tests
- Trial-level tests for group claims

## Open questions

