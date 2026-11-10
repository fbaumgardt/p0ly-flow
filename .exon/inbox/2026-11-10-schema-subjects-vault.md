SCHEMA section `subjects` is now stale, and the fix lives in the scrum vault, not here.

From EP-001 (manifest-driven ingestion): the manifest became the authoritative subject
universe, so the pipeline config no longer carries a `subjects` key. SCHEMA
(`../p0ly/scrum/04_Specs/SCHEMA.md`) still documents it.

Whoever owns the vault should drop that key from SCHEMA and point the section at
`ingestion.manifest` / `metadata/manifest.tsv` instead.

Filed 2026-11-10 during the EP-001 interview so the epic does not claim an edit in a
repository it cannot verify.
