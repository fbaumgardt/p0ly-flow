---
id: ST-006
type: story
title: Path assembly lives in the DAG, not the library
status: approved
parent: EP-001
depends-on: []
tests: []
fixtures: []
priority: 3
updated: 2026-11-10
---

# ST-006: Path assembly lives in the DAG, not the library

## Narrative

Contributes to EP-001. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-019_io-path-refactor.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `59a4a7c`.

## Acceptance criteria

- AC-1: Every rule shall receive resolved paths through `snakemake.input` and `snakemake.output`; rule scripts derive no paths from config.
- AC-2: `scripts/ingest_raw.py` shall contain no path-assembly logic.
- AC-3: Both shipped configs shall plan successfully, proving the resolution is config-independent.

## Non-goals

- Library-side path APIs (ADR-0006 is the decision, not a library change)

## Open questions
