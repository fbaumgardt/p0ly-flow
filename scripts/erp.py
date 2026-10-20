"""Cluster permutation contrasts across subjects for one timelock (US-010).

Pure I/O shim per p0ly-flow/AGENTS.md: reads the per-subject condition evokeds
for the contrast's two arms (rule inputs, expanded by Snakemake), forwards them
to ``p0ly_utils.analysis.group_erp`` with the statistics settings from
``config.yaml erp`` (``n_permutations``, ``seed``), and writes the requested
contrast's files. All math — per-subject difference waves, EEG-only picking,
channel adjacency, threshold selection, the permutation test itself — lives in
the library; this script only marshals Evokeds and persists the returns.

Output contract (SCHEMA §6, flat per-timelock layout):
  * ``{cond_first}-vs-{cond_second}_clusterperm.npz``: ``t_obs``
    (n_channels, n_times), per-cluster p-values, sign-flip null maxima (``h0``;
    its length IS the number of unique permutations actually used — for small
    cohorts see the quantization note on ClusterPermStats), plus the erp
    settings echoed back. ``threshold`` is stored as NaN (= MNE's automatic
    t-threshold for p < 0.05).
  * ``{cond_first}-vs-{cond_second}_clusterperm.csv``: one row per detected
    cluster — MNE's cluster index arrays are pixel-wise (one entry per lit
    voxel, values repeat), so ``n_channels``/``n_times`` count the DISTINCT
    values, ``n_pixels`` the total mass, and the index lists stay verbatim.
    Header-only when no cluster formed.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import mne
import numpy as np
import pandas as pd
from p0ly_utils.analysis import group_erp

p = snakemake.params
cond_first, cond_second = p.conditions


def _read_one(path: str) -> mne.Evoked:
    evokeds = mne.read_evokeds(path)
    if len(evokeds) != 1:
        raise RuntimeError(f"expected exactly 1 evoked in {path}, found {len(evokeds)}")
    return evokeds[0]


evoked_first = [_read_one(path) for path in snakemake.input.cond_first]  # type: ignore[name-defined]
evoked_second = [_read_one(path) for path in snakemake.input.cond_second]  # type: ignore[name-defined]
n_subjects = len(evoked_first)

# Defense in depth: the DAG omits contrast targets for smaller cohorts
# (Snakefile _ERP_CONTRASTS_ENABLED); a forced or stale rule run must not
# compute meaningless statistics either.
if n_subjects < 2:
    raise RuntimeError(
        f"run_erp[{snakemake.wildcards.contrast}]: cluster permutation contrasts "  # type: ignore[name-defined]
        f"need >= 2 subjects, found {n_subjects}; grand averages (rule "
        "erp_group_average) remain the valid single-subject output"
    )

result = group_erp(
    [{cond_first: a, cond_second: b} for a, b in zip(evoked_first, evoked_second)],
    [(cond_first, cond_second)],
    n_permutations=p.stats["n_permutations"],
    seed=p.stats["seed"],
)
stats = result.contrasts[(cond_first, cond_second)]

np.savez(
    snakemake.output.npz,  # type: ignore[name-defined]
    t_obs=stats.t_obs,
    cluster_pvals=stats.cluster_pvals,
    h0=stats.h0,
    n_subjects=np.int64(n_subjects),
    n_permutations=np.int64(p.stats["n_permutations"]),
    tail=np.int64(stats.tail),
    # NaN = MNE's automatic p < 0.05 t-threshold (library default)
    threshold=np.nan if stats.threshold is None else np.float64(stats.threshold),
    seed=np.nan if p.stats["seed"] is None else np.int64(p.stats["seed"]),
    conditions=np.array(f"{cond_first}|{cond_second}"),
)

rows = [
    {
        "cluster": i,
        "n_pixels": len(ch_idx),
        "n_channels": len(set(ch_idx.tolist())),
        "n_times": len(set(t_idx.tolist())),
        "channel_indices": " ".join(str(c) for c in ch_idx),
        "time_indices": " ".join(str(t) for t in t_idx),
        "p_value": float(stats.cluster_pvals[i]),
    }
    for i, (ch_idx, t_idx) in enumerate(stats.clusters)
]
pd.DataFrame(
    rows,
    columns=[
        "cluster",
        "n_pixels",
        "n_channels",
        "n_times",
        "channel_indices",
        "time_indices",
        "p_value",
    ],
).to_csv(snakemake.output.csv, index=False)  # type: ignore[name-defined]
