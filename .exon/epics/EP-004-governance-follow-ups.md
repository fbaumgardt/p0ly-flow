---
id: EP-004
type: epic
title: Recorded provenance, enforced config contracts and per-subject statistics
status: draft
parent: VIS-1
depends-on: [EP-003]
priority: 5
updated: 2026-11-03
---

# EP-004: Recorded provenance, enforced config contracts and per-subject statistics

## Outcome

A run states what produced it — spec contents and hash, library revision — in a
per-subject sidecar; a config key that no rule reads is rejected at parse time instead of
silently doing nothing; and a subject can be tested on its own, not only averaged into a
cohort.

## Why now

Every accepted ADR left an implementation gap behind it, and each gap is a promise the
architecture currently cannot keep: provenance is described but stored nowhere
(ADR-0002, ADR-0011), validation is described as derived from scripts but not implemented
(ADR-0012), single-subject statistics are a recorded seam with no rule (ADR-0009), and the
agent guidance still points at a `config.schema.yaml` gate and a `../scrum` vault that neither exist (ADR-0013).
They come last because they describe the whole surface, which is only stable once
EP-001, EP-005, EP-002 and EP-003 have landed.
Serves: VIS-1 goal 3, VIS-1 goal 4.

## Scope

- Per-subject provenance sidecar: spec path, spec contents, spec hash, `p0ly-eeg` revision,
  written by each subject rule; a group rule writes its own sidecar naming the subject
  sidecars it consumed plus the manifest hash, without re-deriving spec or library identity
- Unknown-key validation at DAG parse time, derived from what rule scripts actually read,
  including the declared-but-never-read direction
- Per-subject inferential statistics as their own rule family, reusing the existing
  subject→group topology
- Alignment of `AGENTS.md`: the config paths corrected to `configs/default.yaml` and
  `configs/test.yaml`, and every `../scrum` link dropped because `.exon/` is the authority
  on intent and work — the pipeline topology stays, it just stops citing the PRD by path

## Non-goals

- Container-based isolation or a provenance service — the sidecar is a file next to the
  run's outputs (ADR-0011).
- A hand-maintained `config.schema.yaml`: the key set is derived from scripts, and a
  parallel declaration was explicitly rejected (ADR-0012).
- Any change to existing rule topology: the follow-ups add seams, they do not restructure
  the DAG.

## Success measures

- A completed run leaves a provenance sidecar per subject whose recorded spec hash
  matches the spec file, and each group output's sidecar names the subject sidecars it
  consumed; the run fails loudly if a sidecar cannot be written.
- A config key that no script reads fails the parse; a key a script reads and config omits
  fails there too, with the script named.
- Per-subject statistics produce a result for a one-subject cohort and refuse a
  group-level claim that would need two subjects.
- `AGENTS.md` names the validation that exists, points at the real config paths
  (`configs/default.yaml`, `configs/test.yaml`) instead of `config.yaml`, and mentions
  neither a `config.schema.yaml` gate nor the `../scrum` folder.

## Open questions
- [x] Success measure 4 checks only for `config.schema.yaml` in `AGENTS.md`, but the file also names `config.test.yaml` and `../scrum`, neither of which exists (the configs are `configs/*.yaml`, the vault is `../p0ly/scrum`). Should the measure cover all stale references, or stay scoped to the schema gate? → Resolved 2026-11-10: all stale references, and decoupling rather than re-pointing — the config paths become `configs/*.yaml` and every `../scrum` link goes, because `.exon/` is now the authority on intent and work.
- [x] The provenance sidecar is "per-subject" and "written on every run", but group-level rules have no subject wildcard. Does the sidecar follow the subject rules only, or does each group output also record its inputs' provenance? ADR-0011 defers placement, so implementation needs the answer. → Resolved 2026-11-10: subject rules write the sidecar; group rules write their own sidecar naming the subject sidecars consumed plus the manifest hash, so no group job re-derives identity.
