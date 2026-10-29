"""Spectral connectivity matrices for one subject's condition (US-013).

Pure I/O shim per p0ly-flow/AGENTS.md: loads the US-017 timelock epochs
(``sub-{subject}_{timelock}_desc-epo.fif.gz``, carrying the aligned trial
metadata) and lets ``p0ly_eeg.analysis.spectral_connectivity`` apply the
condition's ``metadata.eval`` query (from ``config.yaml
group_aggregation.condition_splits``; the reserved ``all_trials`` condition
passes ``None``) before one ``mne_connectivity`` call computes every
configured method (wPLI / coherence / PLV — ``config.yaml connectivity``
settings). The result keeps every channel (per-subject QC artifact) and is
saved as an ``.npz`` archive — one adjacency array
``(n_channels, n_channels, n_freqs)`` per method (symmetric, zero diagonal)
plus ``ch_names`` and ``freqs`` metadata.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import mne
import numpy as np
from p0ly_eeg.analysis import spectral_connectivity

p = snakemake.params  # type: ignore[name-defined]
settings = p.connectivity

epochs = mne.read_epochs(snakemake.input.epochs, preload=True)  # type: ignore[name-defined]
result = spectral_connectivity(
    epochs,
    methods=settings["methods"],
    fmin=settings["fmin"],
    fmax=settings["fmax"],
    mode=settings["mode"],
    n_jobs=settings["n_jobs"],
    condition_query=p.condition_query if p.condition_query else None,
)
payload: dict[str, object] = {
    "ch_names": np.array(result.ch_names),
    "freqs": result.freqs,
}
for method, matrix in result.matrices.items():
    payload[method] = matrix
np.savez(snakemake.output.conn, **payload)  # type: ignore[name-defined]
