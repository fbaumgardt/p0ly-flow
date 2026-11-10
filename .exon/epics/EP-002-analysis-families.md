---
id: EP-002
type: epic
title: Analysis families wired into per-subject and group outputs
status: draft
parent: VIS-1
depends-on: [EP-005]
priority: 3
updated: 2026-11-03
---

# EP-002: Analysis families wired into per-subject and group outputs

## Outcome

Nine analysis families (ERP, PSD, TFR/ITPC, connectivity, single-trial regression,
cluster-permutation statistics, CFC, variability, decoding) plan and run from epoched
inputs, each switchable through an existing `analysis.run_*` gate, writing discoverable
containers under `data/derivatives/group_analysis/`.

## Why now

Families are what collaborators actually ask for, and each one is an independent slice
of work that can land without touching the others. Ahead of EP-003 because cohort
expansion has nothing to expand until families emit subject-level results, and behind
EP-005 because families read the epoch files it writes.
Serves: VIS-1 goal 3, VIS-1 goal 4.

## Scope

- ERP: subject averages, cohort grand averages, condition contrasts
- PSD and TFR/ITPC with cluster-permutation statistics
- Connectivity graphs with a subject-unit contrast
- Single-trial regression
- CFC (subject maps, cohort description, subject-unit contrast)
- Neural variability across voltage and power domains
- Temporal-generalization decoding

## Non-goals

- Analysis algorithms and statistics: `p0ly-eeg` implements them; rules here wire
  inputs, params and outputs (ADR-0001, ADR-0009).
- Per-subject inferential statistics — the current families deliver subject averages and
  group inference; single-subject testing is EP-004 scope (ADR-0009 follow-up).
- Reporting and plotting — a vision non-goal.
- Bycycle waveform cycles: the rules exist only on an unmerged branch (`e9fa281`) and
  cannot merge until the Python toolchain conflict is resolved, so it leaves this epic
  for a follow-up one; ST-021 and T-022 stay parked until then (roadmap “Not now”).

## Success measures

- For each family, a dry-run restricted to its `run_*` rule succeeds on `configs/test.yaml`
  (`uv run snakemake -n -R run_<family> --configfile configs/test.yaml`).
- Disabling `analysis.run_<family>` removes that family's rules from the plan; enabling it
  restores them, with no other rule changing.
- Group outputs for a configured family land under
  `data/derivatives/group_analysis/<timelock>/<cohort>/<condition>/` without manual file
  handling.
- `uv run snakemake --lint` reports no issues.

## Open questions
- [x] Scope says every family sits behind an `analysis.run_*` toggle, but only eight toggles exist (erp, psd, tfr, connectivity, regression, cfc, variability, decoding). Cluster-permutation statistics ride `analysis.run_tfr` plus the `tfr:` block, and bycycle's toggle exists only on the unmerged branch. Does the epic require one toggle per family (two new toggles), or only that each family is switchable through some existing gate? → Resolved 2026-11-10: only that each family is switchable through an existing gate; cluster-permutation stays under `run_tfr`, no new toggles.
- [x] Success measure 1 requires each family's `-n -R run_<family>` to succeed, but `run_bycycle` has no rule on `main` until the toolchain conflict is resolved, so EP-002 cannot reach its own success measures as long as bycycle is in scope. Does bycycle stay in EP-002 and block its closure, or move to a later epic as an in-flight item? → Resolved 2026-11-10: moves out; bycycle is now a non-goal with a branch pointer, so the epic can close on `main`.
