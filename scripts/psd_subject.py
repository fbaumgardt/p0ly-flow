"""Write one subject's Welch spectrum for a timelock x condition (US-011).

Pure I/O shim per p0ly-flow/AGENTS.md: loads the US-017 timelock epochs
(``sub-{subject}_{timelock}_desc-epo.fif.gz``, carrying the aligned trial
metadata) and lets ``p0ly_utils.analysis.psd_by_condition`` apply the
condition's ``metadata.eval`` query (from ``config.yaml
group_aggregation.condition_splits``; the reserved ``all_trials`` condition
passes ``None``) before computing the Welch spectrum with ``config.yaml psd``
settings. Fails loud on zero query matches (US-024 philosophy). The spectrum
keeps every channel and is saved as MNE Spectrum HDF5 (h5io — Spectrum.save's
native container; not FIF).

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import mne
from p0ly_utils.analysis import psd_by_condition

p = snakemake.params
psd_settings = p.psd

epochs = mne.read_epochs(snakemake.input.epochs, preload=True)  # type: ignore[name-defined]
spectra = psd_by_condition(
    epochs,
    {str(p.condition): p.condition_query},
    fmin=psd_settings["fmin"],
    fmax=psd_settings["fmax"],
    n_fft=psd_settings["n_fft"],
    n_per_seg=psd_settings.get("n_per_seg"),
    n_overlap=psd_settings.get("n_overlap", 0),
)
spectra[str(p.condition)].save(snakemake.output.psd, overwrite=True)  # type: ignore[name-defined]
