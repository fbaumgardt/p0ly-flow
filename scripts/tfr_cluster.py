"""Cluster permutation contrasts over TFR difference grids (US-026).

Pure I/O shim per p0ly-flow/AGENTS.md: reads the cohort's per-subject
condition TFR files for the contrast's two arms (rule inputs, expanded by
Snakemake), EEG-picks and stacks them, and runs an independent one-sample
cluster permutation test per product via ``p0ly_utils.analysis`` — raw power
difference for the power entry, Fisher-z-transformed difference
(:func:`itpc_z`) for the ITPC entry. All math — the difference design, the
3-D (channel x freq x time) adjacency, threshold selection, the permutation
test itself — lives in the library (``tfr_cluster_permutation``); this script
only marshals AverageTFRs and persists the returns.

Output contract (SCHEMA §9, cohort-tier layout):
  * ``{condA}-vs-{condB}_tfrcluster.npz``: per statistic, keys prefixed
    ``power_`` / ``itpc_`` — ``t_obs`` (n_channels, n_freqs, n_times),
    ``cluster_pvals``, ``h0``, ``n_clusters``, plus ``n_subjects`` and the
    tfr settings echo. ``threshold`` is stored as NaN (= MNE's automatic
    t-threshold for p < 0.05).
  * ``{condA}-vs-{condB}_tfrcluster.csv``: one row per (statistic, cluster)
    — distinct channel/freq/time counts, pixel-wise index lists, p_value.
    Header-only when no cluster formed.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import numpy as np
import pandas as pd
from mne.time_frequency import read_tfrs
from p0ly_utils.analysis import eeg_adjacency, itpc_z, tfr_cluster_permutation

p = snakemake.params
cond_first, cond_second = p.conditions


def _read_entries(path):
    entries = read_tfrs(path)
    if len(entries) != 2 or entries[0].comment != "power" or entries[1].comment != "itpc":
        raise RuntimeError(
            f"expected a two-entry [power, ITPC] TFR file in {path}, got "
            f"{len(entries)} entries with comments "
            f"{[e.comment for e in entries]}"
        )
    return entries[0], entries[1]


first_entries = [_read_entries(path) for path in snakemake.input.cond_first]  # type: ignore[name-defined]
second_entries = [_read_entries(path) for path in snakemake.input.cond_second]  # type: ignore[name-defined]
n_subjects = len(first_entries)

# Defense in depth: the DAG omits cluster targets for cohorts with < 2
# subjects (_TFR_CLUSTER_COHORTS); a forced or stale rule run must not
# compute meaningless statistics either.
if n_subjects < 2:
    raise RuntimeError(
        f"run_tfr_cluster[{snakemake.wildcards.contrast}]: cluster permutation "  # type: ignore[name-defined]
        f"contrasts need >= 2 subjects, found {n_subjects}; difference maps "
        "(rule run_tfr) remain the valid single-subject output"
    )

# Grid guards across subjects (I/O-level consistency, mirroring the two-entry
# verification above): every subject must share the same EEG channel set,
# frequency grid and time grid. Non-EEG channels are dropped before stacking.
picked = []
for arm in (first_entries, second_entries):
    arm_picked = []
    for power, itpc_map in arm:
        power = power.copy().pick("eeg")
        itpc_map = itpc_map.copy().pick("eeg")
        if len(power.ch_names) == 0:
            raise RuntimeError(
                f"run_tfr_cluster[{snakemake.wildcards.contrast}]: no EEG "  # type: ignore[name-defined]
                "channels in the subject TFRs"
            )
        arm_picked.append((power, itpc_map))
    reference = arm_picked[0]
    for power, itpc_map in arm_picked[1:]:
        if power.ch_names != reference[0].ch_names:
            raise RuntimeError("subject TFRs have inconsistent EEG channel sets")
        if not np.allclose(power.freqs, reference[0].freqs) or not np.allclose(
            power.times, reference[0].times
        ):
            raise RuntimeError("subject TFRs have inconsistent freq/time grids")
    picked.append(arm_picked)

adjacency = eeg_adjacency(picked[0][0][0].info)


def _identity(data):
    return data


def _stack(arm, index, transform):
    return np.stack([transform(entry[index].data) for entry in arm])


power_stats = tfr_cluster_permutation(
    _stack(picked[0], 0, _identity) - _stack(picked[1], 0, _identity),
    adjacency,
    n_permutations=p.stats["n_permutations"],
    seed=p.stats["seed"],
)
itpc_stats = tfr_cluster_permutation(
    _stack(picked[0], 1, itpc_z) - _stack(picked[1], 1, itpc_z),
    adjacency,
    n_permutations=p.stats["n_permutations"],
    seed=p.stats["seed"],
)

np.savez(
    snakemake.output.npz,  # type: ignore[name-defined]
    n_subjects=np.int64(n_subjects),
    n_permutations=np.int64(p.stats["n_permutations"]),
    seed=np.nan if p.stats["seed"] is None else np.int64(p.stats["seed"]),
    conditions=np.array(f"{cond_first}|{cond_second}"),
    power_t_obs=power_stats.t_obs,
    power_cluster_pvals=power_stats.cluster_pvals,
    power_h0=power_stats.h0,
    itpc_t_obs=itpc_stats.t_obs,
    itpc_cluster_pvals=itpc_stats.cluster_pvals,
    itpc_h0=itpc_stats.h0,
)

rows = []
for statistic, stats in (("power", power_stats), ("itpc", itpc_stats)):
    for i, (ch_idx, freq_idx, time_idx) in enumerate(stats.clusters):
        rows.append(
            {
                "statistic": statistic,
                "cluster": i,
                "n_pixels": len(ch_idx),
                "n_channels": len(set(ch_idx.tolist())),
                "n_freqs": len(set(freq_idx.tolist())),
                "n_times": len(set(time_idx.tolist())),
                "channel_indices": " ".join(str(c) for c in ch_idx),
                "freq_indices": " ".join(str(f) for f in freq_idx),
                "time_indices": " ".join(str(t) for t in time_idx),
                "p_value": float(stats.cluster_pvals[i]),
            }
        )
pd.DataFrame(
    rows,
    columns=[
        "statistic",
        "cluster",
        "n_pixels",
        "n_channels",
        "n_freqs",
        "n_times",
        "channel_indices",
        "freq_indices",
        "time_indices",
        "p_value",
    ],
).to_csv(snakemake.output.csv, index=False)  # type: ignore[name-defined]
