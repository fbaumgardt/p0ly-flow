---
id: ADR-0003
type: adr
title: uv for dependency and run management
status: approved
parent: ARCH-1
updated: 2026-11-03
---

# ADR-0003: uv for dependency and run management

## Context

p0ly-flow runs a Python scientific stack with Snakemake and a sibling library dependency. Development and verification need one consistent way to resolve dependencies and execute commands; `pyproject.toml`, `uv.lock`, and the `uv run` workflow already provide it.

## Decision

Use uv for p0ly-flow dependency resolution, locking, synchronization, and command execution. Declare runtime and development dependencies in `pyproject.toml`, retain `uv.lock`, and use `uv run` for pipeline and test commands. This does not make p0ly-flow a packaged library or prescribe another repository's build backend.

## Alternatives considered

- **Poetry** — rejected in favor of uv's faster resolution and single install/run workflow for this project.
- **pip-tools and requirements files** — rejected because they split dependency declaration and locking across additional tooling.
- **Unlocked virtual environments** — rejected because third-party dependency resolution would be less repeatable.

## Consequences

- Easier: one toolchain covers environment setup, execution, and lockfile-based dependency resolution.
- Harder: contributors must install uv and keep lockfile changes under review.
- Now forbidden: treating an unrecorded ad hoc environment as a reproducible pipeline environment.
- Follow-up work: editable library checkouts still require the immutable-source provenance in ADR-0011 for reproducible/shared runs.
