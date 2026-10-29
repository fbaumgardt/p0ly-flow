"""Single-trial OLS beta maps for one subject's timelock (US-014).

Pure I/O shim per p0ly-flow/AGENTS.md: loads the US-017 timelock epochs
(``sub-{subject}_{timelock}_desc-epo.fif.gz``, carrying the aligned trial
metadata) and calls ``p0ly_eeg.analysis.regression_epochs`` with the
``config.yaml regression:`` predictor declaration — ``signal_domain``
(``voltage`` | ``power``), ``continuous`` numeric columns and ``categorical``
reference-coded columns. Design-matrix construction, complete-case exclusion,
rank/row-count validation and the OLS solve all live in the library; the
power domain receives the existing ``tfr:`` block via ``params.tfr`` (the
same settings ``analysis.run_tfr`` uses — no second transform
implementation).

The archive is written with ``np.savez_compressed`` and stores every string
as a Unicode array (no pickled objects): ``betas`` with the domain-specific
leading term axis — ``(n_terms, n_channels, n_times)`` for voltage,
``(n_terms, n_channels, n_freqs, n_times)`` for power — plus ``terms``
(ordered ``intercept`` → continuous → ``column[level]`` dummies), ``ch_names``,
``times``, ``freqs`` (power only), ``domain``, ``reference_levels_json``,
``n_input``, ``n_used``, ``n_excluded`` and ``excluded_rows``.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import json

import mne
import numpy as np
from p0ly_eeg.analysis import regression_epochs

p = snakemake.params  # type: ignore[name-defined]
settings = p.regression
domain = settings.get("signal_domain", "voltage")

epochs = mne.read_epochs(str(snakemake.input.epochs), preload=True)  # type: ignore[name-defined]
result = regression_epochs(
    epochs,
    continuous=settings.get("continuous") or [],
    categorical=settings.get("categorical") or [],
    domain=domain,
    tfr_settings=p.tfr if domain == "power" else None,
)
terms = list(result.beta_maps)
payload: dict[str, object] = {
    "betas": np.stack([result.beta_maps[term] for term in terms]),
    "terms": np.array(terms),
    "ch_names": np.array(result.ch_names),
    "times": result.times,
    "domain": np.array(result.domain),
    "reference_levels_json": np.array(json.dumps(result.reference_levels, sort_keys=True)),
    "n_input": np.array(result.n_input),
    "n_used": np.array(result.n_used),
    "n_excluded": np.array(result.n_excluded),
    "excluded_rows": result.excluded_rows,
}
if result.freqs is not None:
    payload["freqs"] = result.freqs
np.savez_compressed(str(snakemake.output.npz), **payload)  # type: ignore[name-defined]
