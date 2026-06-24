"""Inject trial metadata from cleaned raw (US-016).

Pure I/O shim per p0ly-flow/AGENTS.md: reads the cleaned raw, extracts the
Psychtoolbox event-marker frame, loads the experiment spec from the path given
by ``config['metadata']['experiment_spec']``, and calls
``p0ly_utils.metadata.parse_metadata`` to build the by-trial DataFrame
(``Block`` / ``Trial`` / ``Onset`` + spec-defined extended columns). The result
is written as a per-subject TSV. No extraction or parsing logic lives here —
algorithms belong in p0ly-eeg.

Metadata only: this rule does not epoch or bind metadata to ``mne.Epochs``
(that is US-017).

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged #2, discovered during US-007).
"""

import mne
from p0ly_utils.metadata import ExperimentSpec, events_from_raw, parse_metadata

p = snakemake.params  # type: ignore[name-defined]

raw = mne.io.read_raw(snakemake.input.raw, preload=False)  # type: ignore[name-defined]
events = events_from_raw(raw)

spec = ExperimentSpec.from_yaml(p.spec_path)
metadata = parse_metadata(
    spec,
    events,
    csv_path=p.csv_columns,
    expand_trials=p.expand_trials,
)

metadata.to_csv(snakemake.output[0], sep="\t", index=False)  # type: ignore[name-defined]
