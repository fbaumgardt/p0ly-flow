"""Segment clean raw into per-timelock epochs with metadata alignment (US-017).

Pure I/O shim per p0ly-flow/AGENTS.md: reads the US-008 cleaned raw and the
US-016 metadata TSV, loads the experiment spec from the path given by
``config['metadata']['experiment_spec']``, and calls
``p0ly_eeg.epoching.epoch_with_metadata`` to cut ``mne.Epochs`` for the
requested timelock and reconcile the metadata against them. The aligned epochs
are saved to ``sub-{subject}_{timelock}_desc-epo.fif.gz`` (SCHEMA §6) and the
mismatch log to ``sub-{subject}_{timelock}_excluded_trials.csv``. No
segmentation or alignment math lives here — algorithms belong in p0ly-eeg.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged #2, discovered during US-007).
"""

import mne
import pandas as pd
from p0ly_eeg.epoching import epoch_with_metadata, validate_intervals
from p0ly_eeg.metadata import ExperimentSpec

p = snakemake.params  # type: ignore[name-defined]

raw = mne.io.read_raw(snakemake.input.raw, preload=True)  # type: ignore[name-defined]
metadata = pd.read_csv(snakemake.input.metadata, sep="\t")  # type: ignore[name-defined]
spec = ExperimentSpec.from_yaml(p.spec_path)

# ADR-006: epoch windows come from config epoching.intervals (analysis-run
# config), the spec carries the timelock event-code map only. Cross-check the
# keys asymmetrically: warn on spec-extra (legitimate skip), error on
# config-extra (likely typo).
validate_intervals(spec.timelocks, p.intervals, timelock=p.timelock)
interval = p.intervals[p.timelock]

epochs, excluded = epoch_with_metadata(
    raw,
    spec,
    p.timelock,
    metadata,
    p.baseline,
    interval=interval,
    subject=snakemake.wildcards.subject,  # type: ignore[name-defined]
)

# Fail loud, not empty (US-024): zero epochs means either the recording carries
# none of this timelock's markers, or every candidate fell in a bad interval.
# Both are silent data loss if written out as an empty ``desc-epo`` file — name
# the timelock, the codes the spec wants, and the codes actually present.
if len(epochs) == 0:
    wanted = spec.timelocks[p.timelock]
    present = sorted(
        {
            desc.replace("Stimulus", "Stim")
            for desc in raw.annotations.description
            if not desc.startswith("bad") and desc != "New Segment/"
        }
    )
    raise RuntimeError(
        f"epoch[{p.timelock}]: 0 epochs from {snakemake.input.raw}.\n"  # type: ignore[name-defined]
        f"  spec {p.spec_path} maps timelock {p.timelock!r} -> {wanted}.\n"
        f"  marker codes present in the raw: {present or 'none'}\n"
        "  If the codes match, all candidate epochs were dropped as bad intervals."
    )

epochs.save(snakemake.output.epochs, overwrite=True)  # type: ignore[name-defined]
excluded.to_csv(snakemake.output.excluded, index=False)  # type: ignore[name-defined]
