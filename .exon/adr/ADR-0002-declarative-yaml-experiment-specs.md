---
id: ADR-0002
type: adr
title: Declarative YAML experiment specs
status: approved
parent: ARCH-1
updated: 2026-11-03
---

# ADR-0002: Declarative YAML experiment specs

## Context

Experiments use different marker codes, trial columns, and timelocks, while the pipeline's metadata and epoching stages are generic. Adding an experiment should not require new Snakemake rules or experiment-specific Python wrappers. Current rules load the YAML path configured by `metadata.experiment_spec` and pass it to the library's generic parser.

## Decision

Declarative YAML files describe experiment markers, timelocks, and trial metadata. The exact configured file is canonical for a run; similarly named copies inside dependencies are not implicitly synchronized or consulted. Generic library code interprets the spec, while p0ly-flow resolves its path and uses its timelock declarations during DAG construction.

## Alternatives considered

- **Per-experiment rule scripts or parser branches in the pipeline** — rejected because they duplicate generic flow logic and require code edits for new experiments.
- **Hardcoded marker and timelock definitions in the Snakefile or main config** — rejected because experiment structure would become entangled with orchestration and run tuning.
- **Treating a dependency's packaged copy as canonical regardless of the configured path** — rejected because it makes the actual run input indirect and couples pipeline behavior to another repository's file layout.

## Consequences

- Easier: a new experiment can be described by a readable YAML file and selected through configuration.
- Harder: the spec must exist at DAG-parse time, and consumers must preserve which file contents were used.
- Now forbidden: silently substituting a same-named spec from another location.
- Follow-up work: every run records the configured spec's path, full contents, and content hash in per-subject provenance sidecars (decided 2026-11-03; implementation pending).
