---
id: EP-003
type: epic
title: Cohort and condition aggregation as wildcard dimensions
status: draft
parent: VIS-1
depends-on: [EP-002]
priority: 4
updated: 2026-11-03
---

# EP-003: Cohort and condition aggregation as wildcard dimensions

## Outcome

Any wired analysis family can be asked for any cohort listed in
`group_aggregation.aggregate_by_cohorts` and present in `data/metadata/participants.tsv`,
and any condition split defined in config, and the DAG expands the targets itself — no
per-cohort code, no manual file copying.

## Why now

It multiplies the families rather than adding one, so its value is a function of how many
families exist; running it first would multiply almost nothing. It also introduces the
cohort×condition axis that every downstream presentation tool reads.
Serves: VIS-1 goal 3.

## Scope

- Cohort membership read from `group_aggregation.cohort_file` and enumerated by
  `group_aggregation.aggregate_by_cohorts`; a cohort naming a subject with no manifest
  rows fails planning instead of shrinking silently
- Condition splits read from `group_aggregation.condition_splits`
- Target paths under `group_analysis/{timelock}/{cohort}/{condition}`
- Subject-unit group contrast that requires at least two subjects and refuses one
- Two-subject smoke coverage so the aggregation path is exercised by `configs/test.yaml`

## Non-goals

- New statistics: aggregation reuses the family-level rules.
- Cohort membership inside the pipeline: which subject belongs to which cohort lives in
  participant metadata, not in `configs/`; config only names which cohorts to aggregate.
- Cross-cohort comparison as a first-class output — cohorts are separate dimensions.

## Success measures

- Adding a cohort row to the participants file and a condition split to config expands
  the plan without any code change.
- `uv run snakemake -n --configfile configs/test.yaml` plans both fixture cohorts and
  every configured condition.
- A one-subject cohort plans with a warning and omits that cohort's contrast targets
  while its grand averages stay plannable, instead of failing the whole run.
- `uv run snakemake --lint` reports no issues.

## Open questions
- [x] Outcome says "any cohort defined in `data/metadata/participants.tsv`", but cohorts are enumerated by `group_aggregation.aggregate_by_cohorts` and merely validated against that file (Snakefile:69-92); a participants row with no config entry plans nothing, and `all_combined` is reserved. Should the outcome read "a cohort listed in config and present in participants.tsv"? → Resolved 2026-11-10: yes, config enumerates and the TSV validates; the outcome is reworded.
- [x] ST-002's cohort check moved here with the manifest subject universe: once `subjects`
  leaves config, does cohort resolution compare members against manifest subjects (failing
  planning when a cohort names a subject with no manifest rows), and does that happen
  before or after cohorts are read from `participants.tsv`? → Resolved 2026-11-10: cohort
  members are checked against manifest subjects at plan time, before membership in the
  participants file is consulted.
- [x] Success measure 3 (and ST-014 AC-3, ST-024 AC-4) says a one-subject cohort "fails loudly at plan time", but the DAG prints a warning and omits only that cohort's contrast targets, keeping its grand averages plannable (Snakefile:128-137). Which behavior is the target: hard failure, or omit-plus-message? Hard failure would make a single-subject cohort unplannable entirely. → Resolved 2026-11-10: warn and omit the contrast targets; grand averages stay plannable, and the measure plus ST-014/ST-024 ACs are reworded to match.
