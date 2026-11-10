---
id: ADR-0007
type: adr
title: Manifest-driven segment ingestion
status: approved
parent: ARCH-1
updated: 2026-11-03
---

# ADR-0007: Manifest-driven segment ingestion

## Context

Subjects can have different numbers of recording segments, and the DAG must know every source file before execution. Filename globbing is fragile and provides no explicit acquisition order or segment metadata. A manifest can represent variable segment counts deterministically, but it must exist before Snakemake parses the DAG.

## Decision

A configured TSV manifest contains one ordered row per recording segment `(subject, segment, source)` and is the source of truth for ingestion. `raw_ingestion` resolves a subject's rows at parse time, loads and merges the segments in one rule, and writes one subject raw FIF without per-segment intermediates. Manifest generation is a pre-DAG operation. Current BIDS ingestion accepts one segment; multi-segment BIDS requires explicit run mapping.

## Alternatives considered

- **A segment wildcard with per-subject counts in config** — rejected because variable file identities still need an external mapping and duplicate manifest information.
- **Recursive filename globbing during DAG parsing** — rejected because naming assumptions and acquisition order remain implicit.
- **Generate and consume the manifest in the same DAG run** — rejected because its contents are needed to determine that run's inputs.
- **Per-segment ingestion rules by default** — rejected for current workloads because intermediate FIFs add I/O without needed parallelism; this remains a possible future scaling change.

## Consequences

- Easier: segment identity and order are inspectable, and one- and multi-segment BrainVision subjects share downstream processing.
- Harder: users must regenerate the manifest after changing raw inputs; BIDS multi-segment ingestion is explicitly unsupported for now.
- Now forbidden: silently discovering a different segment set at runtime than the manifest declared at parse time.
- Follow-up work: preserve manifest provenance and add run-aware BIDS mapping only when required.
