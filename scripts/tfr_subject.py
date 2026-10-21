"""Complex TFR -> two-entry [power, ITPC] HDF5 for one subject's condition
(US-012).

Pure I/O shim per p0ly-flow/AGENTS.md: loads the US-017 timelock epochs
(``sub-{subject}_{timelock}_desc-epo.fif.gz``, carrying the aligned trial
metadata) and lets ``p0ly_utils.analysis.tfr_epochs`` apply the condition's
``metadata.eval`` query (from ``config.yaml
group_aggregation.condition_splits``; the reserved ``all_trials`` condition
passes ``None``) before the single Morlet/multitaper convolution with
``config.yaml tfr`` settings. The large complex transient is reduced
in-memory — epoch-mean power (:func:`average_power`) and ITPC (:func:`itpc`)
— and never written per-epoch. Fails loud on zero query matches (US-024
philosophy). The result keeps every channel (per-subject QC artifact) and is
saved as a two-entry AverageTFR HDF5 (h5io family via
``mne.time_frequency.write_tfrs``) — positional convention:
entry [0] = power, entry [1] = ITPC.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import mne
from mne.time_frequency import write_tfrs
from p0ly_utils.analysis import average_power, freq_grid, itpc, tfr_epochs

p = snakemake.params  # type: ignore[name-defined]
tfr_settings = p.tfr

epochs = mne.read_epochs(snakemake.input.epochs, preload=True)  # type: ignore[name-defined]
complex_tfr = tfr_epochs(
    epochs,
    freq_grid(tfr_settings["fmin"], tfr_settings["fmax"], tfr_settings["step"]),
    n_cycles=tfr_settings["n_cycles"],
    method=tfr_settings["method"],
    time_bandwidth=tfr_settings["time_bandwidth"],
    decim=tfr_settings["decim"],
    condition_query=p.condition_query if p.condition_query else None,
)
write_tfrs(
    snakemake.output.tfr,  # type: ignore[name-defined]
    [average_power(complex_tfr), itpc(complex_tfr)],
    overwrite=True,
)
