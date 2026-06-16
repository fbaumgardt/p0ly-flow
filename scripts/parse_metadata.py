"""Inject trial metadata into epochs (bootstrap placeholder).

Wired in full during US-008. For now, emits a placeholder TSV so the DAG resolves.
"""
from __future__ import annotations

import pandas as pd

df = pd.DataFrame(
    {
        "Block": [1],
        "Trial": [1],
        "RT": [0.450],
        "Correct": [True],
    }
)
df.to_csv(snakemake.output[0], sep="\t", index=False)
