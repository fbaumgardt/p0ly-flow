"""Ingest and merge a subject's raw recording segments (US-007 / US-009).

Thin wrapper per p0ly-flow/AGENTS.md: the manifest rows for the subject
(``snakemake.params.rows`` — ``(segment, source)`` tuples, ordered by
acquisition) drive per-segment ``source`` construction exactly as ADR-005
(amended) prescribes; each segment is loaded via
:func:`p0ly_utils.io.load_raw` and all segments are concatenated via
:func:`p0ly_utils.merge.merge_recordings` (inserts ``BAD_break`` annotations at
boundaries, validates channel/sfreq consistency). The merged recording is saved
to ``sub-{subject}_desc-raw.fif.gz`` (SCHEMA §6). No algorithm logic, no
hardcoded paths — the source list, output path, and config all arrive via
``snakemake``.

Channel types + montage are fixed on every segment by ``load_raw`` and
preserved by ``mne.concatenate_raws`` (info taken from segment 0; the merge
function guarantees channels/sfreq match across segments, so types/montage
match too). A single-segment subject passes through ``merge_recordings``
unchanged (no ``BAD_break``).

BIDS multi-segment is deferred to a follow-up: the BIDS branch builds a single
``BIDSPath`` (no ``run`` entity) and asserts ``len(rows) == 1``. Mapping the
manifest ``segment`` column to the BIDS ``run`` entity + run-aware manifest
generation is the future widening.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement.
"""

from mne_bids import BIDSPath
from p0ly_utils import load_raw, merge_recordings

fmt = snakemake.params.fmt
montage = snakemake.params.montage
rows = snakemake.params.rows  # list[(segment, source)] in acquisition order

raws = []
for _segment, source in rows:
    if fmt == "BrainVision":
        # Concrete .vhdr path from the manifest row; the library composes nothing.
        src = source
    elif fmt == "BIDS":
        if len(rows) != 1:
            raise NotImplementedError(
                "Multi-segment BIDS ingestion is not supported in this first "
                "US-009 step (single BIDSPath, no `run` entity). Map the "
                "manifest `segment` column to the BIDS `run` entity as a "
                "follow-up."
            )
        # Pipeline-owned BIDSPath construction; the library builds no BIDS entities.
        src = BIDSPath(
            subject=snakemake.params.subject,
            task=snakemake.params.task,
            datatype=snakemake.params.datatype,
            root=str(snakemake.params.data_dir),
        )
    else:
        raise ValueError(
            f"Unsupported input_format {fmt!r} (expected 'BrainVision' or 'BIDS')."
        )
    raws.append(load_raw(src, montage=montage))

merged = merge_recordings(raws)
merged.save(snakemake.output[0], overwrite=True)
