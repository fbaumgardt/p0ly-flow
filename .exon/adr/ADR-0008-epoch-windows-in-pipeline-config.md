---
id: ADR-0008
type: adr
title: Epoch windows live in pipeline config
status: approved
parent: ARCH-1
updated: 2026-11-03
---

# ADR-0008: Epoch windows live in pipeline config

## Context

Timelock event codes describe an experiment, while `(tmin, tmax)` windows are analysis-run tuning that may change for the same recording. Keeping windows in experiment specs forces spec edits for routine analysis changes. Moving timelock codes into run config would instead mix intrinsic experiment structure into analysis tuning.

## Decision

Experiment specs own timelock names and event-code maps; `epoching.intervals` in pipeline config owns each cut window, with no spec fallback. The epoch boundary warns when the spec declares a timelock the run does not cut, but rejects a configured interval whose timelock is absent from the spec.

## Alternatives considered

- **Keep windows in the experiment spec** — rejected because it treats analysis tuning as immutable experiment structure.
- **Move both event codes and windows into run config** — rejected because metadata parsing needs the experiment's marker definitions and would become ambiguous.
- **Allow a spec fallback when config omits a window** — rejected because it obscures which source supplied the effective value.
- **Error on both directions of key mismatch** — rejected because running a subset of declared timelocks is valid; only config-extra keys indicate an unusable request.

## Consequences

- Easier: epoch windows can be tuned without changing the experiment definition.
- Harder: switching experiments requires a compatible interval block, and consistency is checked at the epoch boundary.
- Now forbidden: silent fallback between config and spec windows or epochs for an unknown configured timelock.
- Follow-up work: startup validation can surface config-extra timelocks earlier without changing the asymmetric semantics.
