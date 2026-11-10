---
id: T-030
type: task
title: Agent guidance matches the validation that exists
status: draft
parent: ST-028
depends-on: []
owns: [AGENTS.md]
tests: []
priority: 3
updated: 2026-11-03
---

# T-030: Agent guidance matches the validation that exists

## Goal

Agent guidance matches the validation that exists.

## Context

- ST-028 (parent story)
- ADR-0013

## Acceptance

- Makes pass: ST-028 AC-1, AC-2, AC-3
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Restructuring the directives beyond the validation section

## Done

`! grep -q 'config.schema.yaml' AGENTS.md`

## Progress notes

## Review

