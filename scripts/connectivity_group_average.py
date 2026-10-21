"""Cross-subject grand average of per-method connectivity matrices (US-013).

Pure I/O shim per p0ly-flow/AGENTS.md: reads every subject's per-condition
``desc-conn.npz`` archive (rule connectivity_subject — Snakemake expands the
subject set, no Python subject loop here), rebuilds
``p0ly_utils.analysis.ConnectivityMatrices`` from it, and calls
``p0ly_utils.analysis.group_connectivity`` (equal-weight cross-subject mean
with channel-set + method + frequency-grid guards), writing
``group_analysis/{timelock}/{condition}_desc-conn_ave.npz`` in the same
archive layout (one adjacency array per method + ``ch_names`` + ``freqs``).

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import numpy as np
from p0ly_utils.analysis import ConnectivityMatrices, group_connectivity

methods = list(snakemake.params.methods)  # type: ignore[name-defined]


def _read(path: str) -> ConnectivityMatrices:
    """Rebuild a ConnectivityMatrices from a subject ``desc-conn.npz``."""
    with np.load(path) as archive:
        if set(methods) - set(archive.files):
            missing = sorted(set(methods) - set(archive.files))
            raise RuntimeError(f"{path} is missing method arrays {missing}")
        return ConnectivityMatrices(
            ch_names=tuple(str(name) for name in archive["ch_names"]),
            freqs=np.asarray(archive["freqs"]),
            matrices={method: np.asarray(archive[method]) for method in methods},
        )


average = group_connectivity([_read(str(path)) for path in snakemake.input.subject_conns])  # type: ignore[name-defined]
payload: dict[str, object] = {
    "ch_names": np.array(average.ch_names),
    "freqs": average.freqs,
}
for method, matrix in average.matrices.items():
    payload[method] = matrix
np.savez(snakemake.output.ave, **payload)  # type: ignore[name-defined]
