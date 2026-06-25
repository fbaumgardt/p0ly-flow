"""Segment clean raw into per-timelock epochs with metadata alignment (US-017).

Pure I/O shim per p0ly-flow/AGENTS.md: reads the US-008 cleaned raw and the
US-016 metadata TSV, loads the experiment spec from the path given by
``config['metadata']['experiment_spec']``, and calls
``p0ly_utils.epoching.epoch_with_metadata`` to cut ``mne.Epochs`` for the
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
from p0ly_utils.epoching import epoch_with_metadata, validate_intervals
from p0ly_utils.metadata import ExperimentSpec

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

epochs.save(snakemake.output.epochs, overwrite=True)  # type: ignore[name-defined]
excluded.to_csv(snakemake.output.excluded, index=False)  # type: ignore[name-defined]
