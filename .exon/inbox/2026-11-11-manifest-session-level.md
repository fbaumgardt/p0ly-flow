# Parked: session level in the ingestion manifest

- 2026-11-10 — parked from the EP-001 pre-approval review (user, on ST-002 AC-1).
- Type: idea
- Status: idea, unrefined

The manifest schema (ADR-0007) is `(subject, segment, source)` with no session
level, and no pipeline code handles sessions today. If multi-session (e.g.
test/retest) studies arrive, the manifest would need a `session` column,
`raw_ingestion` would key on (subject, session), and derivatives paths would
gain a session wildcard. Until then, deliberately not built.

Capture and refine via `/exon-interview` if/when a multi-session study is on
the roadmap; would likely touch EP-001's ADR-0007 and the SCHEMA manifest
contract.
