"""Cohort condition contrast with full-map max-statistic control (US-027).

Pure I/O shim per p0ly-flow/AGENTS.md. Inputs are the cohort's per-subject
``desc-cfc.npz`` archives for both contrast arms (rule cfc_subject) — the
subject-unit test needs the per-subject maps, not the descriptive averages.
The script verifies that both arms list the **same subject IDs in the same
order** (a silent reordering would pair the wrong subjects), rebuilds observed
``p0ly_utils.analysis.CFCMap`` objects only, and calls
``p0ly_utils.analysis.cfc_condition_contrast``.

Subject nulls/p-values are never read: the library signature takes observed
maps only, so trial-level or surrogate p-values cannot enter the cohort
statistic. Distribution: sign flips of each subject's whole difference map
(first subject fixed to +1), one full-map family per method key, corrected
p-values from the max-|statistic| null.

Resolution: exact enumeration yields at most ``2 ** (n_subjects - 1)`` null
maxima, so with the ``+1`` convention n=2 has minimum p = 1/3 and n=6 has
minimum p = 1/33 — small cohorts cannot necessarily reach p < 0.05. The DAG
omits these targets below 2 subjects (see _CFC_CONTRAST_COHORTS).

Archived per method ``<key>``: ``<key>__difference``,
``<key>__pvalues_corrected``, ``<key>__null_max``, ``<key>__valid_mask``, plus
shared axes and the settings echo.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import numpy as np
from p0ly_utils.analysis import CFCMap, cfc_condition_contrast

p = snakemake.params  # type: ignore[name-defined]
settings = p.stats


def _read(paths: list[str]) -> tuple[list[dict[str, CFCMap]], list[str]]:
    """Rebuild one arm's observed CFCMaps plus its ordered subject IDs."""
    arm: list[dict[str, CFCMap]] = []
    subject_ids: list[str] = []
    for path in paths:
        with np.load(path) as archive:
            ch_names = tuple(str(name) for name in archive["ch_names"])
            phase_freqs = np.asarray(archive["phase_freqs"])
            amp_freqs = np.asarray(archive["amp_freqs"])
            subject_ids.append(str(archive["subject"]))
            arm.append(
                {
                    str(key): CFCMap(
                        values=np.asarray(archive[f"{key}__observed"]),
                        ch_names=ch_names,
                        phase_freqs=phase_freqs,
                        amp_freqs=amp_freqs,
                        method=str(key),
                        n_epochs=int(archive["n_epochs"]),
                        valid_mask=np.asarray(archive[f"{key}__valid_mask"]),
                    )
                    for key in (str(name) for name in archive["methods"])
                }
            )
    return arm, subject_ids


first, first_ids = _read([str(path) for path in snakemake.input.maps_first])  # type: ignore[name-defined]
second, second_ids = _read([str(path) for path in snakemake.input.maps_second])  # type: ignore[name-defined]
if first_ids != second_ids:
    raise RuntimeError(
        f"cfc contrast arms must pair the same subjects — {first_ids} vs {second_ids}"
    )

results = cfc_condition_contrast(
    first,
    second,
    conditions=p.conditions,
    n_permutations=int(settings["n_permutations"]),
    seed=settings["seed"],
)
reference = results[next(iter(results))].difference
payload: dict[str, object] = {
    "ch_names": np.array(reference.ch_names),
    "phase_freqs": reference.phase_freqs,
    "amp_freqs": reference.amp_freqs,
    "methods": np.array(list(results)),
    "conditions": np.array([str(name) for name in p.conditions]),
    "n_subjects": np.array(results[next(iter(results))].n_subjects),
    "n_permutations": np.array(results[next(iter(results))].n_permutations),
    "n_resamples": np.array(results[next(iter(results))].n_resamples),
    "seed": np.array(-1 if settings["seed"] is None else int(settings["seed"])),
    "correction": np.array(results[next(iter(results))].correction),
    "evidence_level": np.array(results[next(iter(results))].evidence_level),
    "timelock": np.array(snakemake.wildcards.timelock),  # type: ignore[name-defined]
    "cohort": np.array(snakemake.wildcards.cohort),  # type: ignore[name-defined]
}
for key, result in results.items():
    payload[f"{key}__difference"] = result.difference.values
    payload[f"{key}__pvalues_corrected"] = result.p_values_corrected
    payload[f"{key}__null_max"] = result.null_max
    payload[f"{key}__valid_mask"] = result.difference.valid_mask
np.savez_compressed(snakemake.output.perm, **payload)  # type: ignore[name-defined]
