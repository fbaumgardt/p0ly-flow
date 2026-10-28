"""Equal-subject-weight cohort regression beta maps (US-014).

Pure I/O shim per p0ly-flow/AGENTS.md: reads every subject's per-timelock
``desc-regression.npz`` archive (rule regression_subject — Snakemake expands
the cohort's subject set, no Python subject loop here), rebuilds
``p0ly_utils.analysis.RegressionResult`` from it without pickle, and calls
``p0ly_utils.analysis.group_regression`` — the equal-subject-weight
arithmetic mean with domain / term-order / reference-level / channel /
response-grid guards. Original epochs are never read here, so a cohort value
cannot silently become a pooled-trial estimate.

Writes ``group_analysis/{timelock}/{cohort}/desc-regression_ave.npz`` in the
same layout (``betas``, ``terms``, ``ch_names``, ``times``, ``freqs`` for the
power domain, ``domain``, ``reference_levels_json``) plus ``n_subjects`` and
``n_trials_used_total`` (informational only). No inferential output: standard
errors, contrasts and cluster corrections are out of scope for this story.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import json

import numpy as np
from p0ly_utils.analysis import RegressionResult, group_regression


def _read(path: str) -> RegressionResult:
    """Rebuild a RegressionResult from a subject ``desc-regression.npz``."""
    with np.load(path, allow_pickle=False) as archive:
        terms = [str(term) for term in archive["terms"]]
        betas = np.asarray(archive["betas"])
        if betas.shape[0] != len(terms):
            raise RuntimeError(
                f"{path}: {betas.shape[0]} beta maps for {len(terms)} terms {terms}"
            )
        return RegressionResult(
            beta_maps={term: np.asarray(betas[index]) for index, term in enumerate(terms)},
            ch_names=tuple(str(name) for name in archive["ch_names"]),
            times=np.asarray(archive["times"]),
            freqs=np.asarray(archive["freqs"]) if "freqs" in archive.files else None,
            domain=str(archive["domain"]),
            n_input=int(archive["n_input"]),
            n_used=int(archive["n_used"]),
            n_excluded=int(archive["n_excluded"]),
            excluded_rows=np.asarray(archive["excluded_rows"], dtype=np.int64),
            reference_levels={
                str(column): str(level)
                for column, level in json.loads(
                    str(archive["reference_levels_json"])
                ).items()
            },
        )


grouped = group_regression(  # type: ignore[name-defined]
    [_read(str(path)) for path in snakemake.input.subject_npzs]
)
terms = list(grouped.beta_maps)
payload: dict[str, object] = {
    "betas": np.stack([grouped.beta_maps[term] for term in terms]),
    "terms": np.array(terms),
    "ch_names": np.array(grouped.ch_names),
    "times": grouped.times,
    "domain": np.array(grouped.domain),
    "reference_levels_json": np.array(json.dumps(grouped.reference_levels, sort_keys=True)),
    "n_subjects": np.array(grouped.n_subjects),
    "n_trials_used_total": np.array(grouped.n_trials_used_total),
}
if grouped.freqs is not None:
    payload["freqs"] = grouped.freqs
np.savez_compressed(str(snakemake.output.ave), **payload)  # type: ignore[name-defined]
