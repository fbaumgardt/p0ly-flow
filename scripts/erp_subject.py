"""Write one subject's average evoked for a timelock x condition (US-010).

Pure I/O shim per p0ly-flow/AGENTS.md: loads the US-017 timelock epochs
(``sub-{subject}_{timelock}_desc-epo.fif.gz``, carrying the aligned trial
metadata) and lets ``p0ly_eeg.analysis.average_epochs`` apply the
condition's ``metadata.eval`` query (from ``config.yaml
group_aggregation.condition_splits``; the reserved ``all_trials`` condition
passes ``None``) before averaging. Fails loud on zero epochs or zero query
matches (US-024 philosophy). The subject average keeps every channel —
EEG-only selection happens inside the group analysis.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import mne
from p0ly_eeg.analysis import average_epochs

p = snakemake.params

epochs = mne.read_epochs(snakemake.input.epochs, preload=True)  # type: ignore[name-defined]
average = average_epochs(epochs, p.condition_query)
average.save(snakemake.output.ave, overwrite=True)  # type: ignore[name-defined]
