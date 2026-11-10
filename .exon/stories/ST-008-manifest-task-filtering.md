---
id: ST-008
type: story
title: Manifest rows can be filtered by task
status: approved
parent: EP-001
depends-on: []
tests: [tests/test_create_tsv.py]
fixtures: []
priority: 2
updated: 2026-11-10
---

# ST-008: Manifest rows can be filtered by task

## Narrative

Contributes to EP-001. Reconstructed from the scrum story `../p0ly/scrum/01_Backlog/US-025_task-filtered-manifest.md`, this repository's slice only; library-side work belongs to the p0ly-eeg port.
Work that landed: `f40043a`, `43f661b`, `1cdf4d7`.

## Acceptance criteria

- AC-1: Given a manifest mixing tasks, when `create_tsv` runs with a task filter, then only that task's rows are emitted.
- AC-2: A null task shall be allowed, and `--exclude` shall drop named rows.
- AC-3: `uv run pytest tests/test_create_tsv.py` shall pass.

## Non-goals

- Other manifest columns than task/subject/session/recording

## Open questions
