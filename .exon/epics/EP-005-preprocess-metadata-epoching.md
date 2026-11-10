---
id: EP-005
type: epic
title: Ingested recordings become preprocessed, annotated epochs
status: approved
parent: VIS-1
depends-on:
- EP-001
priority: 2
updated: '2026-11-10'
---

# EP-005: Ingested recordings become preprocessed, annotated epochs

## Outcome

A subject's ingested recording becomes a preprocessed recording carrying trial
metadata and, per timelock the run's config supplies an interval for, an epoch file
(ADR-0008: the spec declares timelocks, config selects which are cut) — with optional
preprocessing steps and epoch windows selected from `configs/` and no analysis family
required.

## Why now

It is the second half of the foundation EP-001 starts: ingestion produces
`sub-{subject}_desc-raw.fif.gz`, this epic turns it into the epoch files every analysis
family reads, so EP-002 and EP-003 have nothing to consume until it lands. It also owns
the largest part of the parameter surface — filter bands, ICA strategy and fit window,
bad-trial thresholds, epoch intervals and baseline — which is where the vision's headline
config-only measure is won or lost.
Serves: VIS-1 goal 1, VIS-1 goal 2.

## Scope

- One preprocessing wrapper with optional steps: a config key that is absent skips that
  step (ADR-0004), including the channel and interval Z-score thresholds
- ICA fit window as a config knob (`preprocessing.ica_fit_window`), with the fitted
  solution persisted only when ICA runs (ADR-0005)
- Metadata rule: the experiment spec plus the cleaned raw's event annotations become the
  per-subject trial table (`sub-{subject}_metadata.tsv`), which the epoch rule binds onto
  the epochs
- Epoching rule per subject and per timelock, with intervals and baseline supplied by
  config, not spec content (ADR-0008)
- Bad-interval decisions ride as `bad_minmax_zscore` annotations on the preprocessed
  recording; the epoch rule drops overlapping epochs and logs them to
  `sub-{subject}_{timelock}_excluded_trials.csv` (reason `bad_interval`)
- Fail-loud behavior when the by-trial metadata or the event annotations are empty
- The DAG cross-checks `epoching.intervals` keys against the spec's timelocks at parse
  time (ST-007 AC-4, landed in `116aafc`), dropping unconfigured spec
  timelocks from the epoch expansion with a warning and keeping the library's
  `validate_intervals` call at the epoch boundary as a second guard
- Path resolution for the preprocessed, metadata and epoch artifacts owned by the DAG

## Non-goals

- Signal-processing implementations: filtering, ICA, metadata parsing and epoching math
  are `p0ly-eeg` calls; these rules only translate config and persist results (ADR-0001).
- Per-analysis preprocessing variants: one preprocessing chain serves every family
  (ADR-0004).
- Analysis families and their outputs: that is EP-002.
- Per-subject or group statistics: EP-002 and EP-004.
- Choosing which segments exist for a subject: the manifest is EP-001's input and
  `scripts/create_tsv.py` owns its generation (ADR-0013).
- Per-timelock baseline windows: `epoching.baseline` stays one shared window applied to
  every timelock; per-timelock overrides are a later addition.
- Montage changes: the montage is fixed at ingestion from `project_settings.montage`
  (EP-001), and preprocessing never re-applies or overrides it.
- Manual ICA review: components are rejected by `preprocessing.ica_strategy` and its
  threshold; no interactive or visual component-selection step enters the DAG.

## Success measures

- `uv run snakemake -n --configfile configs/test.yaml --until epoch` plans the
  preprocessing, metadata and epoching chain for every manifest subject and every
  timelock the config supplies an interval for, with zero missing rules.
- `uv run snakemake --lint` reports no issues.
- Each story's `Done` command passes in the repository as it stands.
- Changing an entry under `epoching.intervals` changes the planned `epoch` params and no
  code.
- Removing a key under `preprocessing` removes that step from the planned `preprocess`
  params and no code.
- A configured interval whose timelock the spec does not declare fails
  `uv run snakemake -n`, naming both the key and the spec; a spec timelock with no
  configured interval plans with a warning.

## Open questions

- [x] Scope says bad-trial flagging is carried to the epoch rule; in fact it rides as
  `bad_minmax_zscore` annotations inside the preprocessed `.fif` (written by the preprocess
  step, read from `raw.annotations` by the epoch rule) and never becomes a separate
  artifact. Is "annotations on the preprocessed recording" the intended wording?
  → Resolved 2026-11-03: the scope bullet names the annotation label and the
  `excluded_trials.csv` audit trail; bad channels stay in `bad_channels.json`.
- [x] Is `--until epoch` the invocation that proves the chain-only claim, or should there
  be a families-off config? → Resolved 2026-11-03: `--until <last chain rule>`;
  `configs/test.yaml` keeps its family toggles. Verified:
  `uv run snakemake -n --configfile configs/test.yaml --until epoch` exits 0 with 14 jobs
  (2 raw_ingestion + 2 preprocess + 2 inject_metadata + 8 epoch).
- [x] ST-004 is titled "Experiment specs become an injected metadata frame" and its ACs
  say the frame is injected onto the recording, which the resolved scope contradicts (a
  TSV written by the metadata rule, bound by the epoch rule). Does that story get renamed
  and re-accepted at story level, or is the epic's wording the only correction?
  → Resolved 2026-11-03: renamed to ST-004 "A cleaned recording becomes a by-trial
  metadata table" (`scripts/parse_metadata.py`, one job per subject, TSV out); AC-1 was
  also wrong (claimed a timelock wildcard and the epoch input). T-004 renamed to match
  and now claims AC-4.
- [x] Critique 2026-11-10: the Outcome promised "per timelock the spec declares, an epoch
  file", but ADR-0008 (and ST-007's non-goals) make running a subset of declared timelocks
  valid — a spec timelock with no configured interval is legitimately skipped. Reword the
  Outcome to "per timelock the run configures an interval for"?
  → Resolved 2026-11-10: Outcome and success measure 1 reworded to timelocks the config
  supplies an interval for; ADR-0008 cited in the Outcome.
- [x] Critique 2026-11-10: the scope bullet "Fail-loud behavior when the by-trial metadata
  or the event annotations are empty" has no owning story AC — ST-013 covers only
  recordings whose events don't match the spec. Which rule fails on an empty by-trial
  metadata table (`inject_metadata` on write, or `epoch` on read), and should ST-004 or
  ST-013 carry that AC?
  → Resolved 2026-11-10: ST-013 owns both guards. `inject_metadata`
  (`scripts/parse_metadata.py`) already fails on empty event annotations before writing
  the TSV (new ST-013 AC-4); `epoch` fails on an empty epoch set (ST-013 AC-1).
- [x] Critique 2026-11-10: verified against the repo — a config-extra interval key does
  not fail `snakemake -n` (exit 0; the check only runs at epoch-job runtime in
  `scripts/epoch.py`), and removing a spec timelock's interval still plans that epoch job
  (wildcards expand over all spec timelocks via `_TIMELOCKS`), so it would KeyError at
  runtime rather than "plan with a warning". The parse-time cross-check is unlanded work,
  yet ST-007 claims "Work that landed: 4d337cc, 55eb5f1". Should the epic state that the
  parse-time cross-check (ST-007 AC-4) is the one outstanding item, with unconfigured spec
  timelocks dropped from the epoch wildcard expansion at parse time — and should that
  story also fix the stale `ADR-006` comments in `Snakefile` (~lines 838/858) and
  `scripts/epoch.py`, which cite the wrong ADR for epoch windows (ADR-0008)?
  → Resolved 2026-11-10: yes — the parse-time cross-check (ST-007 AC-4) is the epic's one
  outstanding item; unconfigured spec timelocks are dropped from the epoch wildcard
  expansion at parse time with a warning (scope bullet updated). ST-007's narrative
  annotated; the stale `ADR-006` comments in `Snakefile`, `scripts/epoch.py` and
  `p0ly_eeg/epoching.py` fixed directly (2026-11-10).

## Review

Independent review 2026-11-10 over the EP-005 commit range (`c51327c`…`9d5b9f6`),
against the story ACs and ADR-0001/0004/0005/0008.

- blocker: ST-007 AC-4 parse-time cross-check is unlanded and claimed by no task.
  → Resolved 2026-11-10: landed in `116aafc`, claimed by T-007 (AC-4 added to its
  Acceptance; Progress notes carry the dry-run evidence for all three AC-4 behaviors).
  Verified: a config-extra interval key exits 0 from `snakemake -n` (runtime-only
  `validate_intervals`, `scripts/epoch.py:31`); an unconfigured spec timelock is still
  planned (wildcards over `_TIMELOCKS`, `Snakefile:28`) and KeyErrors at runtime
  (`scripts/epoch.py:37`). The epic's own success measure 6 does not hold today.
- process: all 7 tasks are `draft` with empty Progress notes although the work landed;
  the ladder ran backwards (commits first, exon backfill later). Every task needs
  Progress notes + human approval + `status: done` with the Done evidence before EP-005
  can leave `draft`.
- should-fix: `metadata/manifest.test.tsv` (ST-013 `fixtures:`) gained a sub-002 row in
  `6e3cabb` with no change request; confirm the guard scenario is unchanged and
  reconcile retroactively.
- follow-up (task): all 7 task files carry per-task review entries; the only artifact
  fix is widening T-004's `owns` to the six `metadata/specs/*.yaml` files (ST-004 AC-2
  mandates all six; `f2253e7` wrote four beyond the listed `owns`).

Spec fit that passed verification (re-run 2026-11-10):
`snakemake -n --until epoch --configfile configs/test.yaml` plans exactly the verified
14 jobs (2 ingestion + 2 preprocess + 2 inject_metadata + 8 epoch), `--lint` clean;
all six specs carry no interval/baseline; single-`preprocess` and optional-ICA
outputs hold; fail-loud guards present in both `parse_metadata.py` and `epoch.py`.

Human attention: the fixture change above; nothing novel in dependencies, data model
or concurrency.
