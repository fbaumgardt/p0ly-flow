---
id: T-009
type: task
title: Segments of one recording merge at ingestion
status: approved
parent: ST-009
depends-on: []
owns: [Snakefile, scripts/ingest_raw.py]
tests: []
priority: 3
updated: 2026-11-10
---

# T-009: Segments of one recording merge at ingestion

## Goal

Segments of one recording merge at ingestion.

## Context

- ST-009 (parent story)
- `../p0ly/scrum/01_Backlog/US-009_recording-merge.md`
- `configs/default.yaml`
- `configs/test.yaml`

## Acceptance

- Makes pass: ST-009 AC-1, AC-2, AC-3
- Unit tests to write: none — the Done command is the proof

## Non-goals

- Cross-session merging
- Reordering segments by content

## Done

`uv run snakemake -n -R raw_ingestion --configfile configs/test.yaml`

## Progress notes

## Review

Reviewed 2026-11-10 (EP-001 branch review).
- Done command re-run clean.
- AC-3: merge is a `p0ly_eeg.merge_recordings` call with `BAD_break` boundaries and
  channel/sfreq validation; the script only loads, merges, saves (ADR-0001/0007 hold).
- AC-1: one raw_ingestion job per subject covers all that subject's manifest rows.
- AC-2: `preprocess` takes only `desc-raw.fif.gz` as input.
