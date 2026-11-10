---
id: ADR-0006
type: adr
title: Pipeline owns source path resolution
status: approved
parent: ARCH-1
updated: 2026-11-03
---

# ADR-0006: Pipeline owns source path resolution

## Context

Only the pipeline knows the configured data root, subject and task wildcards, manifest rows, and number of recording segments. If the library composes paths from those values, workflow naming conventions are duplicated across repositories and multi-file ingestion becomes dependent on library-side layout assumptions.

## Decision

p0ly-flow resolves all recording sources before calling the library. BrainVision inputs are concrete `.vhdr` paths; BIDS inputs are `BIDSPath` objects constructed by the pipeline. The library receives these resolved sources and does not construct workflow paths from configuration-derived fragments.

## Alternatives considered

- **Library composes paths from data directory, subject, and task** — rejected because it duplicates naming conventions and prevents the pipeline from independently determining recording segments.
- **Pass a relative-path builder into the library** — rejected because it hides rather than removes library ownership of workflow layout.
- **Treat BIDS resolution as an exception inside the library** — rejected because the pipeline still needs consistent ownership of source selection across formats.

## Consequences

- Easier: one component owns source layout, and the same library API can consume paths resolved from manifests or other pipeline inputs.
- Harder: adapters must construct the correct source type for each supported format.
- Now forbidden: adding pipeline-specific directory or filename composition to library ingestion APIs.
- Follow-up work: multi-segment BIDS support must map manifest segments to BIDS run entities in the pipeline.
