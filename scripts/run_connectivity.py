"""Graph metrics of the band-averaged group connectivity (US-013).

Pure I/O shim per p0ly-flow/AGENTS.md: reads the grand-average
``desc-conn_ave.npz`` (rule connectivity_group_average — one read, not N
subject re-reads), then calls ``p0ly_utils.analysis`` helpers —
``band_average`` (inclusive ``(fmin, fmax)`` windows from
``config.yaml connectivity.bands``) and ``graph_metrics`` (thresholded
undirected weighted graph via networkx: weighted clustering, characteristic
path length on the largest connected component with effective distance
``1 / weight``, strength centrality, edge + component counts; the
``min_edge_weight`` noise floor comes from config). Writes
``group_analysis/{timelock}/{condition}_desc-conn_graph.csv`` — one row per
(method, band, node); the graph-level columns (``path_length``,
``n_edges``, ``n_components``) repeat per row. No statistical test lives
here (defined at n=1, mirroring PSD/TFR).

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import numpy as np
import pandas as pd
from p0ly_utils.analysis import band_average, graph_metrics

p = snakemake.params  # type: ignore[name-defined]
bands = {name: (float(lo), float(hi)) for name, (lo, hi) in p.bands.items()}
min_edge_weight = float(p.min_edge_weight)

with np.load(str(snakemake.input.ave)) as archive:  # type: ignore[name-defined]
    ch_names = [str(name) for name in archive["ch_names"]]
    freqs = np.asarray(archive["freqs"])
    rows: list[dict[str, object]] = []
    for method in p.methods:  # configured order, not archive order
        if method not in archive.files:
            raise RuntimeError(f"{snakemake.input.ave} is missing the {method!r} adjacency")
        averaged = band_average(np.asarray(archive[method]), freqs, bands)
        for band, band_matrix in averaged.items():
            metrics = graph_metrics(band_matrix, min_edge_weight=min_edge_weight)
            for node in range(len(ch_names)):
                rows.append(
                    {
                        "method": method,
                        "band": band,
                        "node": node,
                        "ch_name": ch_names[node],
                        "clustering": float(metrics.clustering[node]),
                        "strength": float(metrics.strength[node]),
                        "path_length": metrics.path_length,
                        "n_edges": metrics.n_edges,
                        "n_components": metrics.n_components,
                    }
                )
pd.DataFrame(rows).to_csv(str(snakemake.output.graph), index=False)  # type: ignore[name-defined]
