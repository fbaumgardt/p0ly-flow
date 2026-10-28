"""Equal-subject-weight cohort variability maps (US-029).

Pure I/O shim per p0ly-flow/AGENTS.md: reads every subject's per-condition
``desc-variability.npz`` archive (rule variability_subject — Snakemake expands
the subject set, no Python subject loop over subjects here), rebuilds one
``p0ly_utils.analysis.VariabilityResult`` per (subject, domain) and calls
``p0ly_utils.analysis.group_variability`` per domain — SD averages every
subject, Fano/CV average only the subjects whose mean power was positive at
that cell (equal weight, never pooled trials). No reduction happens here.

Archive layout mirrors the subject files: ``{domain}__{measure}`` cohort maps,
``{domain}__{measure}__n_contributing`` per-cell contributor counts,
``{domain}__measures``, ``ch_names``, ``times`` (voltage axis when the voltage
domain is configured, else the power axis), ``freqs`` + ``power__times`` for
the power domain, and ``n_subjects`` (the full cohort, even where fewer
subjects contributed a ratio cell).

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import numpy as np
from p0ly_utils.analysis import VariabilityResult, group_variability

p = snakemake.params  # type: ignore[name-defined]
domains = list(p.domains)
paths = [str(path) for path in snakemake.input.subject_variability]  # type: ignore[name-defined]


def _read(path: str, domain: str) -> VariabilityResult:
    """Rebuild one subject/domain VariabilityResult from a subject archive."""
    with np.load(path) as archive:
        if domain not in set(archive["domains"]):
            raise RuntimeError(
                f"{path} carries no {domain!r} domain "
                f"(has {list(archive['domains'])})"
            )
        power = domain == "power"
        measures = [str(name) for name in archive[f"{domain}__measures"]]
        return VariabilityResult(
            maps={name: np.asarray(archive[f"{domain}__{name}"]) for name in measures},
            ch_names=tuple(str(name) for name in archive["ch_names"]),
            times=np.asarray(archive["power__times"] if power else archive["times"]),
            freqs=np.asarray(archive["freqs"]) if power else None,
            domain=domain,
            n_trials=int(archive["n_trials"]),
            positive_mean=(
                np.asarray(archive["power__positive_mean"]) if power else None
            ),
        )


grouped = {
    domain: group_variability([_read(path, domain) for path in paths])
    for domain in domains
}
first = next(iter(grouped.values()))
payload: dict[str, object] = {
    "domains": np.array(domains),
    "ch_names": np.array(first.ch_names),
    "times": grouped["voltage"].times if "voltage" in grouped else grouped["power"].times,
    "n_subjects": np.array(first.n_subjects),
}
for domain, result in grouped.items():
    payload[f"{domain}__measures"] = np.array(list(result.maps))
    for measure, array in result.maps.items():
        payload[f"{domain}__{measure}"] = array
        payload[f"{domain}__{measure}__n_contributing"] = result.n_contributing[measure]
    if result.freqs is not None:
        payload["freqs"] = result.freqs
        payload[f"{domain}__times"] = result.times

np.savez_compressed(snakemake.output.ave, **payload)  # type: ignore[name-defined]
