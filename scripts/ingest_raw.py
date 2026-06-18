"""Ingest raw EEG via p0ly_utils.io.load_raw and save BIDS-named FIF.

Thin wrapper per p0ly-flow/AGENTS.md: no algorithm logic, no hardcoded paths
(the output path comes from ``snakemake.output``). All tunables arrive via
``snakemake.params`` from config.yaml.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement.
"""

from p0ly_utils import io

raw = io.load_raw(
    fmt=snakemake.params.fmt,
    subject=snakemake.params.subject,
    data_dir=snakemake.params.data_dir,
    task=snakemake.params.task,
    montage=snakemake.params.montage,
)
raw.save(snakemake.output[0], overwrite=True)
