---
id: ROAD-1
type: roadmap
title: Roadmap
status: approved
parent: VIS-1
updated: 2026-11-10
---

# Roadmap

## Order

1. EP-001 — first, because every analysis rule runs on the DAG it scaffolds, its
   ingestion resolves the recordings everything else reads, and its config contract is
   the one the rest extends; nothing else is observable until the DAG plans.
2. EP-005 — second, because it turns EP-001's `desc-raw.fif.gz` into the epoch files
   every analysis family consumes; it also owns most of the parameter surface, so the
   config-only measure is decided here.
3. EP-002 — before EP-003, because cohort expansion only becomes meaningful once families
   produce subject-level outputs that can be averaged and contrasted.
4. EP-003 — after at least one family exists; it multiplies whatever families exist
   across cohorts and conditions, so it is worth little on its own.
5. EP-004 — last, because provenance and config-contract enforcement describe the whole
   surface; their checks are cheapest and most stable once the families are settled.

## Not now

- p0ly-eeg's own port (US-001–US-005, library-side preprocessing and metadata) — a
  separate `exon` ladder in that repository, linked by story ID rather than copied here.
- US-028 bycycle — its rules exist on an unmerged branch and cannot merge until the
  Python toolchain conflict is resolved; it left EP-002 (non-goal) and needs a follow-up
  epic, with ST-021 and T-022 parked.
- Reporting and visualization — a vision non-goal for this DAG; it belongs to a library.
