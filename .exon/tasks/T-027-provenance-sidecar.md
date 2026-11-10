---
id: T-027
type: task
title: Every run records what produced it
status: draft
parent: ST-025
depends-on: []
owns: [Snakefile, scripts/provenance.py, tests/test_provenance.py, configs/default.yaml]
tests: [tests/test_provenance.py]
priority: 3
updated: 2026-11-03
---

# T-027: Every run records what produced it

## Goal

Every run records what produced it.

## Context

- ST-025 (parent story)
- ADR-0002
- ADR-0011

## Acceptance

- Makes pass: ST-025 AC-1, AC-2, AC-3, AC-4
- Unit tests to write: tests/test_provenance.py

## Non-goals

- Containers or a provenance service (ADR-0011)
- Cross-run databases

## Done

`uv run pytest tests/test_provenance.py`

## Progress notes

## Review

