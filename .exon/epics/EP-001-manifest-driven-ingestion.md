---
id: EP-001
type: epic
title: Manifest-driven ingestion
status: approved
parent: VIS-1
depends-on: []
priority: 1
updated: 2026-11-10
---

# EP-001: Manifest-driven ingestion

## Outcome

Ingestion turns manifest rows into merged, persisted per-subject recordings under the
derivatives tree, driven entirely by config and a generated manifest.

## Why now

Every downstream rule reads the `desc-raw.fif.gz` this epic writes, directly or through
EP-005, and nothing plans or runs until the DAG itself scaffolds, lints and locks its
toolchain. It is also
where "which recordings exist for a subject" is decided, so EP-005 starts from whatever
this epic persists, and the merged `.fif.gz` under the derivatives tree is the first
standardized container the ladder produces.
Serves: VIS-1 goal 2, VIS-1 goal 3.

## Scope

- Bootstrap: `rule all`, `uv`-locked toolchain with `p0ly-eeg` pinned, `snakemake --lint`
  clean (ADR-0003)
- Manifest-driven ingestion from a generated TSV: one row per recording segment, one
  `raw_ingestion` job per subject (ADR-0007)
- The manifest is the subject universe: the subject set is derived from manifest rows
  rather than a config list, so adding a subject is a manifest edit and no config edit
- BrainVision and BIDS resolved by one rule, no format switch in code
- Segments of one recording merged at ingestion into a single raw, with `BAD_break`
  boundaries and channel/sfreq validation
- Ingested recordings persisted as `.fif.gz` under the derivatives tree
- Manifest filtering by task for single-task study designs
- Path assembly owned by the DAG, not the library (ADR-0006)

## Non-goals

- Signal processing or merging math: `load_raw` and `merge_recordings` are `p0ly-eeg`
  calls; the rule resolves sources and persists the result (ADR-0001).
- Per-segment intermediate FIFs and per-segment parallelism: the merge collapses at
  ingestion; revisit only if per-segment parallelism is needed (ADR-0007).
- Manifest generation inside the DAG: `scripts/create_tsv.py` is a standalone, out-of-run
  utility (ADR-0013).
- Choosing which subjects a run covers through a config key: the manifest is the
  register, so a `subjects` list in config would let the two drift apart.
- Recorded provenance of a run: EP-004 owns the sidecar.
- Preprocessing, metadata injection and epoching: EP-005, which consumes the
  `.fif.gz` this epic writes.

## Success measures

- `uv run snakemake -n --configfile configs/test.yaml --until raw_ingestion` plans one
  ingestion job per manifest subject with its sources resolved and zero missing rules.
- `uv run snakemake --lint` reports no issues.
- Each story's `Done` command passes in the repository as it stands.
- Adding a subject row to the manifest plans that subject's ingestion job and needs no
  config edit.
- A manifest row naming a missing file fails planning and names the file.

## Open questions

- [x] Is `--until raw_ingestion` the invocation that proves the ingestion-only claim, or is
  a families-off config the better proof? → Resolved 2026-11-03: `--until <last chain
  rule>`; a second config would have to be maintained, while a renamed rule fails the
  measure. Verified: `uv run snakemake -n --configfile configs/test.yaml --until
  raw_ingestion` exits 0 with 2 jobs (one per fixture subject).
- [x] Dropping `subjects` from the config contract changes SCHEMA §`subjects`, which lives
  in the scrum vault (not in this repository). Who updates it: this epic, or a linked
  change in the vault? → Resolved 2026-11-10: neither — the requirement is filed as a raw
  note in `.exon/inbox/` (`.exon/inbox/2026-11-10-schema-subjects-vault.md`) for whoever
  owns the vault, so this repository does not claim an edit it cannot verify.
- [x] Cohort resolution validates cohort members against the configured subject list
  (Snakefile:85-89) and EP-003 reads cohorts from `participants.tsv`. Once the subject
  universe comes from the manifest, does that check compare against manifest subjects —
  and is that EP-003's change or this epic's? → Resolved 2026-11-10: EP-003's. This epic
  removes the subject list and nothing else; ST-002's AC-6 (cohort naming a subject with
  no manifest rows) moved to EP-003's open questions.
