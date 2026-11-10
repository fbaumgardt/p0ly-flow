---
id: ADR-0001
type: adr
title: Separate orchestration from the EEG library
status: approved
parent: ARCH-1
updated: 2026-11-03
---

# ADR-0001: Separate orchestration from the EEG library

## Context

p0ly-flow needs Snakemake DAG construction, configuration injection, wildcard expansion, and artifact management. EEG processing and analysis require a separately testable scientific Python library with different dependencies and release concerns. Combining them would couple workflow execution to algorithm development and make the thin-wrapper boundary difficult to enforce.

## Decision

p0ly-flow owns orchestration and workflow filesystem concerns; `p0ly-eeg` owns reusable EEG processing, analysis, statistics, parsing, and reporting/visualization functions. p0ly-flow rule scripts call the library but do not implement its algorithms.

## Alternatives considered

- **One repository and package with optional Snakemake dependencies** — rejected because it mixes test environments and encourages algorithm and orchestration code to bleed into one another.
- **Workflow-specific implementations inside rule scripts** — rejected because they are harder to unit test, reuse, and validate scientifically.

## Consequences

- Easier: library behavior can be tested independently; pipeline changes can focus on DAG and configuration behavior.
- Harder: library API changes may require synchronized wrapper updates and explicit cross-repository coordination.
- Now forbidden: signal-processing or statistical algorithm implementations in p0ly-flow, and Snakemake orchestration inside the library.
- Follow-up work: keep consumed library APIs and dependency revisions explicit in `pyproject.toml` and rule adapters.
