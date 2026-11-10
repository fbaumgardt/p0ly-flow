---
id: T-008
type: task
title: Manifest rows can be filtered by task
status: approved
parent: ST-008
depends-on: []
owns: [scripts/create_tsv.py, tests/test_create_tsv.py, metadata/manifest.tsv]
tests: [tests/test_create_tsv.py]
priority: 3
updated: 2026-11-10
---

# T-008: Manifest rows can be filtered by task

## Goal

Manifest rows can be filtered by task.

## Context

- ST-008 (parent story)
- `../p0ly/scrum/01_Backlog/US-025_task-filtered-manifest.md`
- work commit `f40043a`
- work commit `43f661b`
- work commit `1cdf4d7`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-008 AC-1, AC-2, AC-3
- Unit tests to write: tests/test_create_tsv.py

## Non-goals

- Other manifest columns than task/subject/session/recording

## Done

`uv run pytest tests/test_create_tsv.py`

## Progress notes

## Review

Reviewed 2026-11-10 (EP-001 branch review).
- Done command re-run: `uv run pytest tests/test_create_tsv.py` — 17 passed.
- AC-1/AC-2 covered by tests (task filter, null task, `--exclude`).
