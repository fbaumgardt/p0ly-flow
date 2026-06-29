"""Generate metadata/manifest.tsv by scanning the raw data directory (US-009).

Standalone CLI utility — NOT a Snakemake `script:` (it has no `snakemake`
object). Run it whenever raw data is added or rearranged:

    uv run python scripts/create_tsv.py

The manifest is the single source of truth for *which recording segments exist
per subject* (ADR-005 §3 amendment). One row per segment with columns:

    subject  segment  source

* ``subject``  — bare numeric ID (matches `config.yaml subjects` / `sub-{id}`).
* ``segment``  — 1-based acquisition order within the subject/session.
* ``source``   — concrete recording path (BrainVision `.vhdr` for BV; the BIDS
  EEG recording file for BIDS), relative to the pipeline root, used both for
  DAG resolution and (BV) as the `load_raw` source.

Per-subject segments are ordered lexicographically by filename — the best
ordering available without explicit acquisition metadata; rename files so the
sort reflects acquisition order if needed.
"""

import csv
import re
import sys
from pathlib import Path

import yaml

_CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"
_DEFAULT_OUT = Path(__file__).resolve().parent.parent / "metadata" / "manifest.tsv"

_SUB_RE = re.compile(r"sub-(\d+)")


def _load_config(config_path: Path) -> dict:
    with config_path.open() as f:
        return yaml.safe_load(f)


def _scan_brainvision(data_dir: Path) -> list[tuple[str, int, str]]:
    """One row per sub-{id}/sub-{id}_task-*.vhdr, ordered by filename."""
    rows: list[tuple[str, int, str]] = []
    for vhdr in sorted(data_dir.glob("sub-*/sub-*_task-*.vhdr")):
        m = _SUB_RE.search(vhdr.parent.name)
        if not m:
            continue
        rows.append((m.group(1), 0, str(vhdr)))
    return _index_segments(rows)


def _scan_bids(data_dir: Path) -> list[tuple[str, int, str]]:
    """One row per sub-{id}/eeg/sub-{id}_task-*_eeg.<ext>, ordered by filename."""
    rows: list[tuple[str, int, str]] = []
    # BIDS EEG recording: the .vhdr sidecar (BrainVision-backed) or .edf.
    for ext in ("vhdr", "edf", "bdf", "set"):
        for rec in sorted(data_dir.glob(f"sub-*/eeg/sub-*_task-*_eeg.{ext}")):
            m = _SUB_RE.search(rec.parent.parent.name)
            if not m:
                continue
            rows.append((m.group(1), 0, str(rec)))
    return _index_segments(rows)


def _index_segments(
    rows: list[tuple[str, int, str]],
) -> list[tuple[str, int, str]]:
    """Assign 1-based per-subject segment indices in acquisition (sorted) order."""
    by_subject: dict[str, list[str]] = {}
    for subj, _, src in rows:
        by_subject.setdefault(subj, []).append(src)
    indexed: list[tuple[str, int, str]] = []
    for subj in sorted(by_subject):
        for idx, src in enumerate(by_subject[subj], start=1):
            indexed.append((subj, idx, src))
    return indexed


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    config_path = Path(argv[0]) if argv else _CONFIG
    cfg = _load_config(config_path)
    ps = cfg["project_settings"]
    root = config_path.resolve().parent
    data_dir = (root / ps["data_directory"]).resolve()
    fmt = ps["input_format"]

    def _rel(p: Path) -> str:
        try:
            return str(p.resolve().relative_to(root))
        except ValueError:
            return str(p)

    if fmt == "BrainVision":
        rows = [(s, i, _rel(Path(src))) for s, i, src in _scan_brainvision(data_dir)]
    elif fmt == "BIDS":
        rows = [(s, i, _rel(Path(src))) for s, i, src in _scan_bids(data_dir)]
    else:
        print(f"Unsupported input_format {fmt!r}", file=sys.stderr)
        return 2

    out = _DEFAULT_OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["subject", "segment", "source"])
        for subj, seg, src in rows:
            w.writerow([subj, seg, src])

    print(f"Wrote {len(rows)} segment row(s) to {out}")
    for subj, seg, src in rows:
        print(f"  sub-{subj}\tseg {seg}\t{src}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
