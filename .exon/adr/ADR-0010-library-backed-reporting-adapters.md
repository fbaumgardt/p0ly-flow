---
id: ADR-0010
type: adr
title: Library-backed reporting through thin adapters
status: approved
parent: ARCH-1
updated: 2026-11-03
---

# ADR-0010: Library-backed reporting through thin adapters

## Context

Reporting and visualization need to consume standardized analysis artifacts without turning p0ly-flow into a presentation-code repository. They should follow the same configuration-driven model as other analyses: reusable behavior is callable, while the workflow selects inputs and parameters and stores returned objects.

## Decision

EEG-specific reporting and visualization functions live in `p0ly-eeg` by default. p0ly-flow may add thin rule adapters that translate configuration into those calls and persist returned figures, reports, or data. How the provider library organizes or supports its own implementation is outside p0ly-flow's architecture.

## Alternatives considered

- **Implement plotting, report composition, or visualization logic in rule scripts** — rejected because it bypasses library-level testing and makes presentation behavior workflow-specific.
- **Exclude reporting outputs entirely** — rejected because library-backed reporting is compatible with the orchestration boundary and standardized artifact consumers.
- **Let notebooks or interactive presentation code become DAG rules with embedded logic** — rejected because it obscures reproducible function calls and duplicates behavior outside a tested library API.

## Consequences

- Easier: reporting follows the same adapter, provenance, and artifact-storage patterns as numerical analyses.
- Harder: new reporting capabilities may require provider-library API work before pipeline rules can expose them.
- Now forbidden: presentation algorithms embedded in p0ly-flow scripts or rules.
- Follow-up work: define concrete reporting rule and artifact contracts when the first reporting capability is introduced.
