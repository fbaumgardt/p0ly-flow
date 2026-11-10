---
id: T-029
type: task
title: A single subject can be tested on its own
status: draft
parent: ST-027
depends-on: []
owns: [Snakefile, scripts/subject_stats.py, tests/test_subject_stats.py, configs/default.yaml]
tests: [tests/test_subject_stats.py]
priority: 3
updated: 2026-11-03
---

# T-029: A single subject can be tested on its own

## Goal

A single subject can be tested on its own.

## Context

- ST-027 (parent story)
- ADR-0009

## Acceptance

- Makes pass: ST-027 AC-1, AC-2, AC-3
- Unit tests to write: tests/test_subject_stats.py

## Non-goals

- Replacing group inference with subject-level tests
- Trial-level tests for group claims

## Done

`uv run pytest tests/test_subject_stats.py`

## Progress notes

## Review

