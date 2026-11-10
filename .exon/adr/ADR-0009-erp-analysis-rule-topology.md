---
id: ADR-0009
type: adr
title: Separate ERP subject, grand-average, and contrast rules
status: approved
parent: ARCH-1
updated: 2026-11-03
---

# ADR-0009: Separate ERP subject, grand-average, and contrast rules

## Context

ERP analysis needs inspectable per-subject condition averages, cohort grand averages, and within-subject condition contrasts. A single group rule with heterogeneous outputs can repeatedly reload the same subject artifacts under Snakemake's per-output scheduling. Cluster permutation contrasts also need at least two subjects per cohort, while grand averages remain meaningful for one subject.

## Decision

Use three rule responsibilities: `erp_subject` averages each subject/timelock/condition, `erp_group_average` computes an equal-subject-weight cohort average, and `run_erp` computes library-owned one-sample cluster permutation contrasts from per-subject difference waves. Contrast targets are omitted explicitly for cohorts with fewer than two subjects and guarded again at runtime; no stub statistics files are written.

## Alternatives considered

- **One group rule for averages and contrasts** — rejected because every requested target reloads all subject inputs and re-runs both computations.
- **Only subject and combined group rules** — rejected because the merged rule needs two subjects for contrasts but one for averages, so small cohorts fail or need in-rule special cases.
- **Empty statistics outputs for small cohorts** — rejected because a stub file is indistinguishable from a real null result.
- **Between-subject condition permutation for the within-subject contrast** — rejected because it destroys the subject pairing and tests between-subject variance.

## Consequences

- Easier: subject averages remain inspectable QC artifacts, and group rules have clear inputs and statistical requirements.
- Harder: changing any contributing subject can invalidate the cohort result, and small cohorts have coarse permutation p-value resolution.
- Now forbidden: computing or fabricating cluster contrasts for a one-subject cohort.
- Follow-up work: other analysis families may reuse this topology only where their computations and statistical requirements actually match. Single-subject (single-case) inferential statistics exist in no rule today; a per-subject statistics family may be added later under this topology with its own targets, subject to the same inference-level requirements.
