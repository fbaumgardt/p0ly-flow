---
id: ST-026
type: story
title: Unknown config keys fail at parse time
status: draft
parent: EP-004
depends-on: []
tests: [tests/test_config_contract.py]
fixtures: []
priority: 4
updated: 2026-11-03
---

# ST-026: Unknown config keys fail at parse time

## Narrative

Contributes to EP-004. Created from an approved ADR follow-up, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Decision source: ADR-0012.

Open work: ADR-0012 requires script-derived validation; only per-family ad-hoc checks exist today.

## Acceptance criteria

- AC-1: A config key that no rule script reads shall fail DAG parsing, naming the key.
- AC-2: A key a script reads but config omits shall fail at the consuming rule, naming the script and key.
- AC-3: The known-key set shall be derived from the rule scripts themselves; no hand-maintained schema file is introduced.

## Non-goals

- A parallel `config.schema.yaml` (rejected in ADR-0012)
- Runtime type checking beyond key presence

## Open questions

