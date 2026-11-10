---
id: T-028
type: task
title: Unknown config keys fail at parse time
status: draft
parent: ST-026
depends-on: []
owns: [Snakefile, scripts/config_contract.py, tests/test_config_contract.py]
tests: [tests/test_config_contract.py]
priority: 3
updated: 2026-11-03
---

# T-028: Unknown config keys fail at parse time

## Goal

Unknown config keys fail at parse time.

## Context

- ST-026 (parent story)
- ADR-0012

## Acceptance

- Makes pass: ST-026 AC-1, AC-2, AC-3
- Unit tests to write: tests/test_config_contract.py

## Non-goals

- A parallel `config.schema.yaml` (rejected in ADR-0012)
- Runtime type checking beyond key presence

## Done

`uv run pytest tests/test_config_contract.py`

## Progress notes

## Review

