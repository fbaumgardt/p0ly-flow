---
id: ST-025
type: story
title: Every run records what produced it
status: draft
parent: EP-004
depends-on: []
tests: [tests/test_provenance.py]
fixtures: []
priority: 4
updated: 2026-11-03
---

# ST-025: Every run records what produced it

## Narrative

Contributes to EP-004. Created from an approved ADR follow-up, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Decision source: ADR-0002, ADR-0011.

Open work: the approved ADRs describe this behavior but no artifact stores it yet.

## Acceptance criteria

- AC-1: A completed run shall write a per-subject provenance sidecar recording the experiment-spec path, its full contents, its hash and the `p0ly-eeg` revision.
- AC-2: The recorded hash shall match the spec file's hash at that commit.
- AC-3: If the sidecar cannot be written, then the run shall fail rather than continue unrecorded.
- AC-4: Provenance shall be recorded on every run, not only when a flag is set.

## Non-goals

- Containers or a provenance service (ADR-0011)
- Cross-run databases

## Open questions

