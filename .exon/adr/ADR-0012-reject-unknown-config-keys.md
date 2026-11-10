---
id: ADR-0012
type: adr
title: Reject unknown configuration keys
status: approved
parent: ARCH-1
updated: 2026-11-03
---

# ADR-0012: Reject unknown configuration keys

## Context

Known optional preprocessing keys may be omitted intentionally. Without validation, however, a misspelled key is indistinguishable from intentional omission and can silently disable processing. This violates explicit failure behavior and can change scientific outputs while appearing to produce a successful run.

## Decision

Validate configuration before execution against the keys each active configuration section supports. Omitting a known optional key remains valid; an unrecognized key must produce a clear error naming its location. Validation runs at DAG parse time (so `snakemake -n` fails before execution) and must cover optional as well as required settings. The known-key set is derived from the rule scripts — the consumers of `snakemake.params`/`snakemake.config` are the ground truth for parameter names. Dynamic-key subtrees (e.g. `epoching.intervals` maps, `psd.bands`) remain open-ended at key level; their values validate where they are consumed (ADR-0008).

## Alternatives considered

- **Silently ignore unknown keys** — rejected because misspellings can silently alter or skip analysis.
- **Require every optional key explicitly** — rejected because it adds boilerplate and weakens the clear omission-to-skip model.
- **Validate only values for keys that are present** — rejected because it cannot detect the dangerous unknown-key case.
- **Parallel declarative schema file (`config.schema.yaml`)** — rejected because the rule scripts are ground truth for parameter names; a hand-maintained parallel file can drift from what scripts actually read.

## Consequences

- Easier: configuration typos fail before computation and optional processing stays concise.
- Harder: the known-key definition must evolve with configuration features and active-module selection.
- Now forbidden: silently accepting an unrecognized configuration key.
- Follow-up work: implement script-derived known-key aggregation with a parse-time validation gate and tests using misspelled optional keys, including a static drift check that rejects keys declared-but-never-read in a script; current configuration handling does not yet provide comprehensive coverage.
