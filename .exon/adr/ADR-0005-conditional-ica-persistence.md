---
id: ADR-0005
type: adr
title: Persist fitted ICA only when ICA runs
status: approved
parent: ARCH-1
updated: 2026-11-03
---

# ADR-0005: Persist fitted ICA only when ICA runs

## Context

A fitted ICA object contains component exclusions, labels, and decomposition state needed for later inspection and reporting. Discarding it loses provenance and forces refitting. Conversely, an ICA artifact for a run where ICA was disabled would misleadingly suggest that processing occurred.

## Decision

When ICA is enabled, persist the fitted object as the subject's `desc-ica.fif.gz` artifact and summarize its component count, exclusions, and method in `bad_channels.json`. When ICA is disabled, omit the ICA file and its DAG targets and record null ICA fields in the sidecar.

## Alternatives considered

- **Discard the fitted object after applying it** — rejected because component-exclusion provenance would be lost and reporting would require refitting.
- **Always write an ICA artifact, including an empty placeholder** — rejected because placeholder processing artifacts obscure which steps actually ran and clutter the derivatives tree.
- **Persist only a human-readable summary** — rejected because it cannot reconstruct the fitted decomposition for later inspection.

## Consequences

- Easier: downstream QA can inspect the exact fitted ICA without repeating preprocessing.
- Harder: the DAG must construct conditional outputs and targets at parse time.
- Now forbidden: requiring or emitting an ICA result for a configuration where ICA did not run.
- Follow-up work: reporting adapters can consume the persisted object and JSON summary without re-entering preprocessing.
