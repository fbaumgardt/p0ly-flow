"""Across-trial variability maps for one subject's condition (US-029).

Pure I/O shim per p0ly-flow/AGENTS.md: loads the US-017 timelock epochs
(``sub-{subject}_{timelock}_desc-epo.fif.gz``, carrying the aligned trial
metadata) and lets ``p0ly_utils.analysis.variability_epochs`` apply the
condition's ``metadata.eval`` query (from ``config.yaml
group_aggregation.condition_splits``; the reserved ``all_trials`` condition
passes ``None``) before reducing over the trial axis. Every configured domain
(``config.yaml variability``) is computed from this one read — voltage -> SD
only, power -> SD/Fano/CV via the ``config.yaml tfr`` settings, which are
independent of ``analysis.run_tfr`` (no TFR artifacts are consumed).

Archive layout (``np.savez_compressed``, no pickled objects, Unicode string
arrays): ``{domain}__{measure}`` maps, ``{domain}__measures``,
``power__positive_mean`` (ratio validity mask), ``ch_names``, ``times``
(voltage axis when the voltage domain is configured, else the power axis),
``freqs`` + ``power__times`` for the power domain, and ``n_trials``.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import mne
import numpy as np
from p0ly_utils.analysis import variability_epochs

p = snakemake.params  # type: ignore[name-defined]
settings = p.variability
condition_query = p.condition_query if p.condition_query else None

epochs = mne.read_epochs(snakemake.input.epochs, preload=True)  # type: ignore[name-defined]

results = {
    domain: variability_epochs(
        epochs,
        domain=domain,
        measures=block["measures"],
        condition_query=condition_query,
        tfr_settings=p.tfr if domain == "power" else None,
    )
    for domain, block in settings.items()
}

# One archive carries one trial count: both domains select the same trials.
n_trials = {result.n_trials for result in results.values()}
if len(n_trials) != 1:
    raise RuntimeError(f"domains disagree on trial counts {sorted(n_trials)}")

first = next(iter(results.values()))
payload: dict[str, object] = {
    "domains": np.array(list(results)),
    "ch_names": np.array(first.ch_names),
    "times": results["voltage"].times if "voltage" in results else results["power"].times,
    "n_trials": np.array(n_trials.pop()),
}
for domain, result in results.items():
    payload[f"{domain}__measures"] = np.array(list(result.maps))
    for measure, array in result.maps.items():
        payload[f"{domain}__{measure}"] = array
    if result.positive_mean is not None:
        payload[f"{domain}__positive_mean"] = result.positive_mean
    if result.freqs is not None:
        payload["freqs"] = result.freqs
        payload[f"{domain}__times"] = result.times

np.savez_compressed(snakemake.output.npz, **payload)  # type: ignore[name-defined]
