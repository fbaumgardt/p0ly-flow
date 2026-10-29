"""Equal-weight descriptive cohort CFC map (US-027).

Pure I/O shim per p0ly-flow/AGENTS.md: reads every subject's per-condition
``desc-cfc.npz`` archive (rule cfc_subject — Snakemake expands the subject set,
no Python subject loop here), rebuilds ``p0ly_eeg.analysis.CFCMap`` from the
**observed** arrays only, and calls ``p0ly_eeg.analysis.group_cfc``
(equal-subject-weight mean with channel-set, method, grid and valid-mask
guards).

Only observed maps enter cohort math — subject nulls and p-values stay in the
per-subject archives; they are subject-level descriptive evidence and never a
cohort claim. The output therefore carries **no averaged p-values**
(``evidence_level="cohort_descriptive"``) and is valid at any n >= 1.
Off-ratio PPC cells stay NaN. Shared axes (``ch_names``, ``phase_freqs``,
``amp_freqs``, ``methods``) and the ``ratios`` echo are carried through from
the subject archives; a ratio mismatch between subjects fails loud.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import numpy as np
from p0ly_eeg.analysis import CFCMap, group_cfc


def _read(path: str) -> tuple[dict[str, CFCMap], np.ndarray]:
    """Rebuild observed CFCMaps (plus the PPC ratio echo) from one archive."""
    with np.load(path) as archive:
        ch_names = tuple(str(name) for name in archive["ch_names"])
        phase_freqs = np.asarray(archive["phase_freqs"])
        amp_freqs = np.asarray(archive["amp_freqs"])
        maps = {
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
        return maps, np.asarray(archive["ratios"])


read = [_read(str(path)) for path in snakemake.input.subject_maps]  # type: ignore[name-defined]
subject_maps = [maps for maps, _ in read]
ratios = read[0][1]
if any(not np.array_equal(other, ratios) for _, other in read[1:]):
    raise RuntimeError(
        "cfc group average inputs were computed with different PPC ratios — "
        "recompute every subject with one config"
    )
average = group_cfc(subject_maps)
reference = average.averages[next(iter(average.averages))]
payload: dict[str, object] = {
    "ch_names": np.array(reference.ch_names),
    "phase_freqs": reference.phase_freqs,
    "amp_freqs": reference.amp_freqs,
    "methods": np.array(list(average.averages)),
    "ratios": ratios,
    "n_subjects": np.array(average.n_subjects),
    "evidence_level": np.array(average.evidence_level),
    "timelock": np.array(snakemake.wildcards.timelock),  # type: ignore[name-defined]
    "cohort": np.array(snakemake.wildcards.cohort),  # type: ignore[name-defined]
    "condition": np.array(snakemake.wildcards.condition),  # type: ignore[name-defined]
}
for key, averaged in average.averages.items():
    payload[f"{key}__mean"] = averaged.values
    payload[f"{key}__valid_mask"] = averaged.valid_mask
np.savez_compressed(snakemake.output.ave, **payload)  # type: ignore[name-defined]
