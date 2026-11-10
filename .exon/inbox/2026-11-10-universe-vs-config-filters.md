Idea, parked 2026-11-10 while critiquing EP-005. Not yet an artifact; nothing below is decided.

**The idea.** The pipeline has two kinds of input. *Universe files* describe what exists: the
manifest (subjects, segments), `participants.tsv` (cohorts), the experiment spec (timelocks,
marker codes, trial columns), and the by-trial metadata TSV (trials with properties).
*Config describes selections on those dimensions*: which subjects, which timelocks, which
cohorts, which conditions/trial filters.

**Where this is stated today: nowhere as a principle.** It exists as one decision per
dimension:

| Dimension | Universe file | Config's role | Stated in |
| --- | --- | --- | --- |
| Subjects | `manifest.tsv` | none — a `subjects` key is forbidden | EP-001 scope + non-goals, ADR-0007 |
| Cohorts | `participants.tsv` | `group_aggregation.aggregate_by_cohorts` names them | EP-003 scope + non-goals, ST-024 AC-1 |
| Timelocks | experiment spec | `epoching.intervals` keys (window and selection) | ADR-0008 |
| Trials | by-trial metadata TSV | `group_aggregation.condition_splits` | EP-003 scope only |
| Manifest rows | `manifest.tsv` | task filter | ST-008 |

`.exon/contracts/` is empty and no ADR covers the split, so a reader cannot find the whole
picture in one place. The words "universe" and "dimension" appear only in EP-001 and EP-003
prose, and "filter" is used inconsistently.

**Open questions this raises.**

- [ ] The model is contradicted by the code: `configs/default.yaml:12` still carries
  `subjects:` and `Snakefile:41,70` read it, while EP-001's non-goal forbids a config
  subject list and its success measure ("adding a subject row needs no config edit") does
  not hold yet. Is removing `subjects` part of EP-001's work, or a separate change?
- [ ] Cohorts do not fit the model cleanly. EP-003's non-goal says config "only names which
  cohorts to aggregate", but `Snakefile:69-92` makes `aggregate_by_cohorts` the enumerator
  and `participants.tsv` the validator (resolved open question, 2026-11-10). Is the rule
  "config selects, file is ground truth" — which differs from the subject rule where
  config may not select at all?
- [ ] There is no stated rule for a selection that matches nothing, and the current
  behavior differs per dimension: config-extra timelock fails, spec-extra timelock warns
  and skips (ADR-0008); a configured cohort with no participants fails, a one-subject
  cohort warns and drops its contrast targets (EP-003); a configured subject absent from
  the manifest silently contributes no jobs (`Snakefile:53-55`); an empty epoch set fails
  loud (ST-013). Should the model carry one explicit fail-vs-warn policy per dimension, or
  is each case deliberately separate?
- [ ] If this is worth keeping, should it become an ADR under ARCH-1, or a CON contract
  pinning the universe files and which config keys select on each dimension? Parked here
  until the fail-vs-warn policy above is decided.
