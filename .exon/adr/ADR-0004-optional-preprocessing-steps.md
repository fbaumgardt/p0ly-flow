---
id: ADR-0004
type: adr
title: Optional preprocessing steps
status: approved
parent: ARCH-1
updated: 2026-11-03
---

# ADR-0004: Optional preprocessing steps

## Context

Different recordings and the analyses planned for a run need different preprocessing settings: ICA may be inappropriate, one-sided filters may be useful, a wide or omitted bandpass may be needed to preserve spectral information for downstream PSD and TFR, or sliding-window rejection may be unwanted. Requiring every parameter would encourage hidden no-ops and make the requested chain unclear. The current `preprocess` rule passes the config block through a thin adapter, where omitted known keys become `None`.

## Decision

Known preprocessing keys are optional. Omission skips the associated library-owned step: both bandpass keys omitted skips filtering, one-sided filters remain valid, bad-channel detection/interpolation is one indivisible optional step, ICA is skipped without `ica_strategy`, and interval rejection requires both its window and threshold. Invalid non-null values still fail.

## Alternatives considered

- **Mandatory parameters with internal no-op behavior** — rejected because it hides intent and obstructs legitimate partial chains.
- **Moving per-step orchestration into the rule script** — rejected because the script would acquire processing logic and lose the single tested library chain.
- **Separate DAG rules for every optional preprocessing step** — rejected for the default chain because it multiplies intermediate artifacts and invalidation points without a demonstrated need.

## Consequences

- Easier: filter-only, no-ICA, and other partial chains are explicit configuration choices.
- Harder: omitted-key semantics require strict unknown-key validation so misspellings cannot silently disable processing.
- Now forbidden: silently ignoring an invalid non-null strategy or treating a one-sided filter as absent.
- Follow-up work: implement the known-key validation required by ADR-0012.
