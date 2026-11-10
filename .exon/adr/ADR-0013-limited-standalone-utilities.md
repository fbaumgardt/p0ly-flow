---
id: ADR-0013
type: adr
title: Limit standalone utilities to out-of-run roles
status: approved
parent: ARCH-1
updated: 2026-11-03
---

# ADR-0013: Limit standalone utilities to out-of-run roles

## Context

Normal artifact transformations belong in the Snakemake DAG so provenance, invalidation, and parallelism are managed consistently. Some utilities cannot or should not participate in an individual run: manifest generation supplies parse-time inputs, fixture generation prepares development data, and provenance inspection can operate on existing outputs.

## Decision

Normal processing and analysis execution must be reachable from Snakemake rules. Standalone execution is allowed only for utilities that generate pre-DAG inputs or support development and provenance inspection. These exceptions must not implement an artifact-transforming analysis step that belongs to the run DAG.

## Alternatives considered

- **Require every executable script to be a Snakemake rule** — rejected because parse-time inputs would require a separate bootstrap DAG and development/provenance tools would acquire artificial workflow dependencies.
- **Allow arbitrary standalone processing scripts** — rejected because they bypass DAG provenance and recreate unmanaged analysis paths.

## Consequences

- Easier: manifest and fixture preparation stay simple while normal analyses retain DAG-managed execution.
- Harder: new executable scripts need explicit role classification and documentation.
- Now forbidden: standalone implementations of processing or analysis transformations that are part of a normal run.
- Follow-up work: align AGENTS.md's absolute standalone-script wording with this limited exception.
