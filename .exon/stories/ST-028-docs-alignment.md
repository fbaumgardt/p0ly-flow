---
id: ST-028
type: story
title: Agent guidance matches the validation that exists
status: draft
parent: EP-004
depends-on: []
tests: []
fixtures: []
priority: 5
updated: 2026-11-03
---

# ST-028: Agent guidance matches the validation that exists

## Narrative

Contributes to EP-004. Created from an approved ADR follow-up, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Decision source: ADR-0013.

Open work: AGENTS.md still points at `config.schema.yaml`, `config.test.yaml` and `../scrum`.

## Acceptance criteria

- AC-1: `AGENTS.md` shall name the validation actually shipped and shall not reference a `config.schema.yaml` gate.
- AC-2: The described gates shall be runnable as written (dry-run, lint, tests).
- AC-3: A reader following the document shall find no stale path (vault location, config file names).

## Non-goals

- Restructuring the directives beyond the validation section

## Open questions

