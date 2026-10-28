"""Cross-frequency coupling maps for one subject's condition (US-027).

Pure I/O shim per p0ly-flow/AGENTS.md: loads the US-017 timelock epochs
(``sub-{subject}_{timelock}_desc-epo.fif.gz``, carrying the aligned trial
metadata) and lets ``p0ly_utils.analysis.estimate_cfc`` apply the condition's
``metadata.eval`` query (from ``config.yaml group_aggregation.condition_splits``;
the reserved ``all_trials`` condition passes ``None``) before computing every
configured method — PAC (tensorpac) and each integer-ratio n:m phase-phase
map, with ``config.yaml cfc`` grids, bandwidths, ratios and surrogate count.

Archived per method ``<key>`` (``pac`` / ``ppc_2x1`` / ...):
``<key>__observed`` ``(n_channels, n_phase_freqs, n_amp_freqs)``,
``<key>__null`` ``(n_surrogates, n_channels, n_phase_freqs, n_amp_freqs)``,
``<key>__p_values`` and ``<key>__valid_mask`` — plus the shared axes
(``ch_names``, ``phase_freqs``, ``amp_freqs``, ``methods``, ``ratios``) and
provenance (``n_epochs``, ``n_surrogates``, ``seed``, ``subject``,
``condition``, ``evidence_level="subject"``).

Size note: the full subject null is retained on purpose (it *is* the evidence
for the subject-level p-values). It grows as
``n_surrogates x n_channels x n_phase_freqs x n_amp_freqs x 8`` bytes before
compression — keep ``cfc.n_surrogates`` and the grids modest.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import mne
import numpy as np
from p0ly_utils.analysis import estimate_cfc

p = snakemake.params  # type: ignore[name-defined]
settings = p.cfc

epochs = mne.read_epochs(snakemake.input.epochs, preload=True)  # type: ignore[name-defined]
results = estimate_cfc(
    epochs,
    methods=settings["methods"],
    phase_freqs=np.asarray(settings["phase_freqs"], dtype=float),
    amp_freqs=np.asarray(settings["amp_freqs"], dtype=float),
    phase_bandwidth=float(settings["phase_bandwidth"]),
    amp_bandwidth=float(settings["amp_bandwidth"]),
    pac_method=settings["pac_method"],
    ratios=[tuple(int(value) for value in ratio) for ratio in settings["ratios"]],
    ratio_tolerance=float(settings["ratio_tolerance"]),
    n_surrogates=int(settings["n_surrogates"]),
    seed=settings["seed"],
    condition_query=p.condition_query if p.condition_query else None,
    n_jobs=int(settings["n_jobs"]),
)
# Every method carries identical axes by construction; the first one wins.
reference = results[next(iter(results))].observed
payload: dict[str, object] = {
    "ch_names": np.array(reference.ch_names),
    "phase_freqs": reference.phase_freqs,
    "amp_freqs": reference.amp_freqs,
    "methods": np.array(list(results)),
    "ratios": np.array([list(ratio) for ratio in settings["ratios"]], dtype=int).reshape(-1, 2),
    "n_epochs": np.array(reference.n_epochs),
    "n_surrogates": np.array(settings["n_surrogates"]),
    "seed": np.array(-1 if settings["seed"] is None else int(settings["seed"])),
    "subject": np.array(p.subject),
    "condition": np.array(p.condition),
    "evidence_level": np.array("subject"),
}
for key, result in results.items():
    payload[f"{key}__observed"] = result.observed.values
    payload[f"{key}__null"] = result.null
    payload[f"{key}__p_values"] = result.p_values
    payload[f"{key}__valid_mask"] = result.observed.valid_mask
np.savez_compressed(snakemake.output.cfc, **payload)  # type: ignore[name-defined]
