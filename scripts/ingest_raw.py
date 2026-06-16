"""Ingest raw EEG data (bootstrap placeholder).

Full BrainVision/BIDS implementation in US-007. For now, creates an empty
placeholder file so the DAG resolves.
"""
from __future__ import annotations

from pathlib import Path

Path(snakemake.output[0]).touch()
