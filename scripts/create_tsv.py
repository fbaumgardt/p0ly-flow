"""Generate the manifest TSV by scanning the raw data directory (US-009, US-025).

Standalone CLI utility — NOT a Snakemake `script:` (it has no `snakemake`
object). Run it whenever raw data is added or rearranged:

    uv run python scripts/create_tsv.py
    uv run python scripts/create_tsv.py config.test.yaml

The manifest is the single source of truth for *which recording segments exist
per subject* (ADR-005 §3 amendment). One row per segment with columns:

    subject  segment  source

* ``subject``  — bare numeric ID (matches `config.yaml subjects` / `sub-{id}`).
* ``segment``  — 1-based acquisition order within the subject/session.
* ``source``   — concrete recording path (BrainVision `.vhdr` for BV; the BIDS
  EEG recording file for BIDS), relative to the pipeline root, used both for
  DAG resolution and (BV) as the `load_raw` source.

Task axis (US-025): the pipeline is single-task — `config.project_settings.task`
labels every output and must not be demoted to a segment. Recordings whose
`task-{}` token differs from the configured task (or that carry no task token
at all) are listed and the run hard-errors without writing a manifest — the
same fail-fast shape as the US-024 guards. The manifest deliberately has no
task column; task becomes a DAG wildcard when cohort/condition expansion lands
(US-015).

Segment order (US-025): per subject, segments order by acquisition start taken
from the earliest `New Segment` marker timestamp in the companion `.vmrk`
sidecar. BrainVision only *conventionally* carries that timestamp; when any
segment of a subject lacks one (missing `.vmrk`, no `New Segment` marker, no
date field), the whole subject falls back to lexicographic filename order and
a warning names the affected sidecars and asks the user to verify — possibly
hand-fix — the `segment` column in the manifest. A timestamped/untimestamped
mix is never merged into one ordering: two different sort keys would be
arbitrating, not sorting.

BIDS (US-025): the scanner considers `vhdr/edf/bdf/set` spellings of the same
recording; extension duplicates collapse to one logical recording (canonical
order `.vhdr` > `.edf` > `.bdf` > `.set`) with a warning naming what it
dropped.
"""

from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

_CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"
_DEFAULT_OUT = _CONFIG.parent / "metadata" / "manifest.tsv"

_SUB_RE = re.compile(r"sub-(\d+)")
_TASK_RE = re.compile(r"_task-([^_.]+)")
_VMRK_DATE_RE = re.compile(r"^\d{20}$")

# One logical BIDS recording has several sidecar spellings; the first wins.
_BIDS_EXT_CANONICAL: tuple[str, ...] = ("vhdr", "edf", "bdf", "set")
_BIDS_EXT_RANK = {ext: rank for rank, ext in enumerate(_BIDS_EXT_CANONICAL)}


@dataclass
class _Refusal:
    """A scanned recording excluded from the manifest, with the reason."""

    source: str
    reason: str


@dataclass
class _Scan:
    """Result of one raw-directory scan: manifest sources + refusals + warnings."""

    sources: list[tuple[str, str]] = field(default_factory=list)  # (subject, path)
    refusals: list[_Refusal] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _load_config(config_path: Path) -> dict:
    with config_path.open() as f:
        return yaml.safe_load(f)


def _subject_of(path: Path) -> str | None:
    """Bare numeric subject ID from the containing `sub-{id}` directory."""
    for parent in (path.parent, path.parent.parent):
        m = _SUB_RE.search(parent.name)
        if m:
            return m.group(1)
    return None


def _task_token_of(path: Path) -> str | None:
    """Task token from the `task-{}` entity in the file stem, or None."""
    m = _TASK_RE.search(path.stem)
    return m.group(1) if m else None


def _refuse_if_wrong_task(path: Path, task: str, scan: _Scan) -> bool:
    """Shared task-axis gate. Returns True when the recording was refused."""
    token = _task_token_of(path)
    if token is None:
        scan.refusals.append(
            _Refusal(str(path), "no task token — cannot match the configured task")
        )
        return True
    if token != task:
        scan.refusals.append(
            _Refusal(
                str(path), f"configured task is {task!r}; recording is task-{token}"
            )
        )
        return True
    return False


def _first_new_segment_timestamp(vmrk: Path) -> float | None:
    """Acquisition start (POSIX seconds) from the earliest `New Segment` marker.

    BrainVision marker rows have the shape
    ``Mk<n>=<Type>,<Description>,<Position>,<Size>,<Channel>[,<Date>]`` where
    ``Date`` is ``YYYYMMDDhhmmssuuuuuu`` — a convention, not a requirement
    (pybv, for one, writes no date). Returns None when the sidecar is missing,
    has no `New Segment` marker, or carries no parseable date; the caller
    warns and falls back rather than guessing.
    """
    try:
        text = vmrk.read_text(encoding="cp1252", errors="replace")
    except OSError:
        return None
    earliest: datetime | None = None
    for line in text.splitlines():
        if not line.startswith("Mk") or "=" not in line or "," not in line:
            continue
        fields = line.split("=", 1)[1].split(",")
        if len(fields) < 6 or fields[0].strip() != "New Segment":
            continue
        date = fields[5].strip()
        if not _VMRK_DATE_RE.match(date):
            continue
        try:
            dt = datetime.strptime(date[:14], "%Y%m%d%H%M%S")
        except ValueError:
            continue
        if earliest is None or dt < earliest:
            earliest = dt
    return earliest.timestamp() if earliest is not None else None


def _index_segments(
    scan: _Scan, vmrk_lookup: bool
) -> list[tuple[str, int, str]]:
    """Assign 1-based per-subject segment indices in acquisition order.

    Per subject: timestamp order when **every** source has a `.vmrk`-derived
    `New Segment` timestamp, else lexicographic fallback with a warning naming
    the un-timestamped sidecars so the manifest can be hand-fixed.
    """
    by_subject: dict[str, list[str]] = {}
    for subj, src in scan.sources:
        by_subject.setdefault(subj, []).append(src)

    indexed: list[tuple[str, int, str]] = []
    for subj in sorted(by_subject):
        paths = [Path(p) for p in by_subject[subj]]
        stamps = (
            {p: _first_new_segment_timestamp(p.with_suffix(".vmrk")) for p in paths}
            if vmrk_lookup
            else {p: None for p in paths}
        )
        if len(paths) > 1 and all(v is not None for v in stamps.values()):
            ordered = sorted(paths, key=lambda p: (stamps[p], str(p)))
        else:
            ordered = sorted(paths, key=lambda p: str(p))
            if len(paths) > 1 and any(v is None for v in stamps.values()):
                missing = ", ".join(str(p.with_suffix(".vmrk")) for p in paths if stamps[p] is None)
                scan.warnings.append(
                    f"sub-{subj}: no timestamped `New Segment` marker for {missing} — "
                    "segments ordered lexicographically; verify or manually fix the "
                    "segment column in the manifest TSV."
                )
        indexed.extend((subj, idx, str(src)) for idx, src in enumerate(ordered, 1))
    return indexed


def _scan_brainvision(data_dir: Path, task: str) -> _Scan:
    """One row per `sub-{id}_task-{configured}.vhdr`; other tasks refused loud."""
    scan = _Scan()
    for vhdr in sorted(data_dir.glob("sub-*/sub-*.vhdr")):
        subj = _subject_of(vhdr)
        if subj is None:
            continue
        if _refuse_if_wrong_task(vhdr, task, scan):
            continue
        scan.sources.append((subj, str(vhdr)))
    return scan


def _scan_bids(data_dir: Path, task: str) -> _Scan:
    """One row per task-matched BIDS EEG recording; extension duplicates collapse."""
    scan = _Scan()
    # key: recording directory + stem without the extension suffix
    spellings: dict[tuple[str, str], list[Path]] = {}
    for ext in _BIDS_EXT_CANONICAL:
        for rec in data_dir.glob(f"sub-*/eeg/sub-*_eeg.{ext}"):
            subj = _subject_of(rec)
            if subj is None:
                continue
            spellings.setdefault((subj, str(rec.parent / rec.stem)), []).append(rec)

    for (subj, stem), recs in sorted(spellings.items()):
        if len(recs) > 1:
            keep = min(recs, key=lambda r: _BIDS_EXT_RANK[r.suffix.lstrip(".")])
            dropped = ", ".join(str(r) for r in recs if r != keep)
            scan.warnings.append(
                f"sub-{subj}: one BIDS recording has multiple EEG sidecar spellings "
                f"({dropped}); kept {keep}"
            )
        else:
            keep = recs[0]
        if _refuse_if_wrong_task(keep, task, scan):
            continue
        scan.sources.append((subj, str(keep)))
    return scan


def _refuse(refusals: list[_Refusal], task: str, fmt: str) -> None:
    """Fail loud (US-024 style): list every splice the scan threw away."""
    print(
        f"create_tsv: {len(refusals)} recording file(s) were NOT catalogued "
        f"(configured task {task!r}, format {fmt!r}):",
        file=sys.stderr,
    )
    for r in refusals:
        print(f"  {r.source} — {r.reason}", file=sys.stderr)
    print(
        "The manifest must stay consistent with the configured task (US-025). "
        "Remove or rename the outlier recordings, point the config at the task "
        "you actually want, or hand-author the manifest.",
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    config_path = Path(argv[0]) if argv else _CONFIG
    cfg = _load_config(config_path)
    ps = cfg["project_settings"]
    root = config_path.resolve().parent
    data_dir = (root / ps["data_directory"]).resolve()
    fmt = ps["input_format"]
    task = ps["task"]

    def _rel(p: Path) -> str:
        try:
            return str(p.resolve().relative_to(root))
        except ValueError:
            return str(p)

    if fmt == "BrainVision":
        scan = _scan_brainvision(data_dir, task)
    elif fmt == "BIDS":
        scan = _scan_bids(data_dir, task)
    else:
        print(f"Unsupported input_format {fmt!r}", file=sys.stderr)
        return 2

    for wm in scan.warnings:
        print(f"WARNING: {wm}", file=sys.stderr)
    if scan.refusals:
        _refuse(scan.refusals, task, fmt)
        return 1

    rows = [(s, i, _rel(Path(src))) for s, i, src in _index_segments(scan, fmt == "BrainVision")]

    out = root / cfg.get("ingestion", {}).get("manifest", _DEFAULT_OUT)
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
