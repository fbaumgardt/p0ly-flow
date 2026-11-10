---
id: ADR-0011
type: adr
title: Immutable library source for reproducible runs
status: approved
parent: ARCH-1
updated: 2026-11-03
---

# ADR-0011: Immutable library source for reproducible runs

## Context

An editable `../p0ly-eeg` checkout supports rapid co-development, but `uv.lock` records its package version rather than the working tree's contents. Two runs with the same lockfile can therefore execute different scientific code. Shared and reproducible analyses need a stronger source identity without giving up editable local development.

## Decision

Editable sibling dependencies are permitted for development. A reproducible or shared analysis environment must identify an immutable p0ly-eeg revision or release and retain that identity in run provenance. The packaging, revision-capture, and release mechanism is an implementation choice.

## Alternatives considered

- **Treat the editable checkout and lockfile as sufficient provenance** — rejected because mutable source contents are not identified by either the path or package version.
- **Forbid editable dependencies entirely** — rejected because it would obstruct the established cross-repository development workflow despite being unnecessary for development-only runs.

## Consequences

- Easier: co-development remains lightweight while reproducible runs gain a verifiable scientific-code identity.
- Harder: shared analysis setup must capture or resolve an immutable revision instead of relying only on `uv sync`.
- Now forbidden: describing an arbitrary editable working tree as fully reproduced by `uv.lock` alone.
- Follow-up work: choose and implement revision capture and immutable dependency resolution; current editable-only configuration does not yet satisfy the shared-run requirement.
