"""Graph metrics of the per-contrast difference connectivity (US-013).

Pure I/O shim per p0ly-flow/AGENTS.md: reads the two grand-average
``desc-conn_ave.npz`` archives of a contrast pair (rule
connectivity_group_average), rebuilds ``p0ly_eeg.analysis.ConnectivityMatrices``
from each, and calls ``p0ly_eeg.analysis.difference_connectivity`` — the
plain ``first - second`` condition difference (the wildcard order in the
contrast name is the sign convention — condition *first* minus *second*).
The difference adjacency is band-averaged (``config.yaml
connectivity.bands``) and thresholded, then ``graph_metrics`` writes one
long-format CSV ``(method, band, node)`` per contrast. The noise floor
applies to the difference **magnitude** (``abs``) — a strong difference is
an edge whichever sign it carries; the coupling-unit ``min_edge_weight``
lever is kept as-is. No statistical test (defined for any n — a difference
of grand means, mirroring run_connectivity/PSD/TFR; the one-sample
per-subject machinery is US-026's).

Caution (documented bias): difference adjacencies compound sign flips of
near-zero couplings — label these graphs as condition differences, not
physical coupling strengths.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import numpy as np
import pandas as pd
from p0ly_eeg.analysis import (
    ConnectivityMatrices,
    band_average,
    difference_connectivity,
    graph_metrics,
)

p = snakemake.params  # type: ignore[name-defined]
methods = list(p.methods)
bands = {name: (float(lo), float(hi)) for name, (lo, hi) in p.bands.items()}
min_edge_weight = float(p.min_edge_weight)


def _read(path: str) -> ConnectivityMatrices:
    """Rebuild a ConnectivityMatrices from a ``desc-conn_ave.npz`` archive."""
    with np.load(path) as archive:
        if set(methods) - set(archive.files):
            missing = sorted(set(methods) - set(archive.files))
            raise RuntimeError(f"{path} is missing method arrays {missing}")
        return ConnectivityMatrices(
            ch_names=tuple(str(name) for name in archive["ch_names"]),
            freqs=np.asarray(archive["freqs"]),
            matrices={method: np.asarray(archive[method]) for method in methods},
        )


difference = difference_connectivity(_read(str(snakemake.input.ave_first)), _read(str(snakemake.input.ave_second)))  # type: ignore[name-defined]
rows: list[dict[str, object]] = []
for method, matrix in difference.matrices.items():
    averaged = band_average(matrix, difference.freqs, bands)
    for band, band_matrix in averaged.items():
        # magnitude is the edge criterion for a difference graph; signed
        # differences would strand most bands below the coupling noise floor
        metrics = graph_metrics(np.abs(band_matrix), min_edge_weight=min_edge_weight)
        for node, ch_name in enumerate(difference.ch_names):
            rows.append(
                {
                    "method": method,
                    "band": band,
                    "node": node,
                    "ch_name": ch_name,
                    "clustering": float(metrics.clustering[node]),
                    "strength": float(metrics.strength[node]),
                    "path_length": metrics.path_length,
                    "n_edges": metrics.n_edges,
                    "n_components": metrics.n_components,
                }
            )
pd.DataFrame(rows).to_csv(str(snakemake.output.graph), index=False)  # type: ignore[name-defined]
