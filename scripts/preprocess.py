"""Continuous-data preprocessing wrapper (US-008).

Pure I/O shim per p0ly-flow/AGENTS.md: reads input raw, maps the
``preprocessing`` config block to ``p0ly_utils.preprocessing.preprocess_raw``
keyword arguments, saves the cleaned raw + ``bad_channels.json`` sidecar and,
when ICA ran, the fitted ICA object to ``sub-{subject}_desc-ica.fif.gz``. No
algorithm logic, no hardcoded paths, no config-key knowledge inside the library
(config keys are unpacked here, at the pipeline boundary).

All config keys are optional (``.get`` → ``None`` skips the corresponding step,
see SCHEMA §preprocessing).

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement.
"""

import json

import mne
from p0ly_utils import preprocessing as pp

p = snakemake.params.pp  # type: ignore[name-defined]

raw = mne.io.read_raw(snakemake.input.raw, preload=True)  # type: ignore[name-defined]

raw, bad_channels, ica = pp.preprocess_raw(
    raw,
    l_freq=p.get("l_freq"),
    h_freq=p.get("h_freq"),
    bad_channel_z_thresh=p.get("bad_channel_z_thresh"),
    ica_strategy=p.get("ica_strategy"),
    icalabel_threshold=p.get("icalabel_threshold"),
    epoch_window_ms=p.get("epoch_window_ms"),
    epoch_reject_z_thresh=p.get("epoch_reject_z_thresh"),
)

raw.save(snakemake.output.raw, overwrite=True)  # type: ignore[name-defined]

# Persist the fitted ICA object for reporting/inspection when the step ran.
if ica is not None:
    ica.save(snakemake.output.ica, overwrite=True)  # type: ignore[name-defined]

# Sidecar: bad channels + ICA component-exclusion summary (reportable).
ica_summary = None
if ica is not None:
    ica_summary = {
        "n_components": int(ica.n_components_) if ica.n_components_ is not None else None,
        "exclude": list(ica.exclude),
        "method": ica.method,
    }
with open(snakemake.output.bads, "w") as f:  # type: ignore[name-defined]
    json.dump(
        {"bad_channels": bad_channels, "ica_strategy": p.get("ica_strategy"), "ica": ica_summary},
        f,
        indent=2,
    )
