"""Generate the manifest TSV by scanning the raw data directory (US-009, US-025).

Standalone CLI utility — NOT a Snakemake `script:` (it has no `snakemake`
object). Run it whenever raw data is added or rearranged:

    uv run python scripts/create_tsv.py                 # interactive mode (no settings given)
    uv run python scripts/create_tsv.py configs/default.yaml
    uv run python scripts/create_tsv.py --data-dir data/raw --data-fmt BrainVision

The three modes share one scan; they differ only in where the settings come
from: a config file (`project_settings`), standalone CLI flags, or prompts.
Interactive mode offers, in two separate confirmed steps, to write the
manifest and to persist the answers to a config file — amending an existing
one or creating a new one (new configs are seeded from configs/default.yaml,
so they keep the full schema).

Manifest provenance: before a manifest is overwritten, the previous version is
archived to `<outdir>/archive/manifest-<UTC timestamp>.tsv` and one line is
appended to `<outdir>/manifest_history.tsv` (timestamp, sha256, counts,
settings, generation mode) — the "which manifest produced what" ledger.
`scripts/which_manifest.py` maps result files back to a ledger entry.
In config mode, refusal patterns from `ingestion.exclude` are honored in
addition to `--exclude` (they may be persisted through interactive mode).

The manifest is the primary register *which recordings exist per subject*.
One row per segment with columns:

    subject  segment  source

* ``subject``  — numeric ID (matches `configs/default.yaml subjects` / `sub-{id}`).
* ``segment``  — 1-based acquisition order within the subject/session.
* ``source``   — file path (BrainVision `.vhdr` for BV; the BIDS EEG
  recording file for BIDS), relative to the pipeline root, used both for
  DAG resolution and as the `load_raw` source.

Task axis (US-025): the pipeline is single-task by default —
`config.project_settings.task` filters the processed segments (a `null` task
disables the axis: every recording is catalogued).
Recordings whose `task-{}` token differs from the configured task are listed
and the run fails.
`--exclude PATTERN` (fnmatch glob pattern) allows skipping mismatched files
without failing the run — an explicit opt-out.
Task becomes a DAG wildcard when cohort/condition expansion lands
(US-015). TODO: check if it has landed?

Segment order (US-025): per subject, segments order by acquisition time taken
from the 'New Segment` marker timestamp in the `.vmrk` event marker file.
BrainVision only *conventionally* carries that timestamp; without one, the
subject falls back to lexicographic filename order for all segments and a
bambwarning is emitted.

BIDS (US-025): the scanner considers `vhdr/edf/bdf/set` spellings of the same
recording; extension duplicates collapse to one logical recording (canonical
order `.vhdr` > `.edf` > `.bdf` > `.set`) with a warning naming what it
dropped.
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import hashlib
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

_CONFIG = Path(__file__).resolve().parent.parent / "configs" / "default.yaml"
_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_OUT = _ROOT / "metadata" / "manifest.tsv"


def _pipeline_root(config_hint: Path | None = None) -> Path:
    """The pipeline root (where the Snakefile lives) — all relative
    data/manifest paths anchor here, not on configs/ or the cwd.
    Walks up from the config's directory; without a hit (and without a
    config) falls back to the module's repo root."""
    if config_hint is not None:
        hint = config_hint.resolve()
        for base in (hint.parent, *hint.parents):
            if (base / "Snakefile").is_file():
                return base
        return hint.parent
    return _ROOT

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


def _refuse_if_wrong_task(path: Path, task: str | None, scan: _Scan) -> bool:
    """Shared task-axis gate. Returns True when the recording was refused."""
    if task is None:
        return False  # null task disables the task-axis gate entirely
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
    """Acquisition time from the `New Segment` marker.

    BrainVision marker rows have the shape
    ``Mk<n>=<Type>,<Description>,<Position>,<Size>,<Channel>[,<Date>]`` where
    ``Date`` is ``YYYYMMDDhhmmssuuuuuu`` — a convention, not a requirement.
    Returns None when the `.vmrk` is missing, has no `New Segment` marker, or
    carries no parseable date.
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
    the un-dated `.vmrk` files so the manifest can be hand-fixed.
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


def _scan_brainvision(data_dir: Path, task: str | None) -> _Scan:
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


def _scan_bids(data_dir: Path, task: str | None) -> _Scan:
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


def _refuse(refusals: list[_Refusal], task: str | None, fmt: str) -> None:
    """Fail loudly: list every splice the scan threw away."""
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
        "you actually want, hand-author the manifest, or pass --exclude to "
        "skip these recordings explicitly.",
        file=sys.stderr,
    )


# --- CLI ----------------------------------------------------------------------


@dataclass
class _Settings:
    """Where/what to scan, where to write, and how manifest rows are rel'd."""

    data_dir: Path
    fmt: str
    task: str | None
    out: Path
    root: Path  # manifest `source` paths are made relative to this
    mode: str  # config | flags | interactive


_FORMATS = {"BrainVision": _scan_brainvision, "BIDS": _scan_bids}
_HISTORY_COLUMNS = (
    "timestamp",
    "manifest_sha256",
    "n_subjects",
    "n_segments",
    "data_dir",
    "fmt",
    "task",
    "mode",
)
_TOP_KEY_RE = re.compile(r"^([A-Za-z][\w-]*):\s*(?:#.*)?$")
_CHILD_KEY_RE = re.compile(r"^(\s+)([\w-]+):\s*")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _archive(out: Path) -> str | None:
    """Snapshot a to-be-overwritten manifest next to itself (DAG never reads it)."""
    if not out.exists():
        return None
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    arch = out.parent / "archive" / f"manifest-{ts}.tsv"
    arch.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out, arch)
    return str(arch)


def _append_history(ledger: Path, row: dict[str, str]) -> None:
    """Register one manifest build: the `which manifest produced what` ledger."""
    new_file = not ledger.exists()
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        if new_file:
            w.writerow(_HISTORY_COLUMNS)
        w.writerow([row.get(c, "") for c in _HISTORY_COLUMNS])


def _upsert_block_key(text: str, block: str, key: str, yaml_value: str) -> str:
    """Set `key` inside top-level `block:`. Line surgery, not yaml round-trip,
    so sibling comments in the config survive."""
    lines = text.splitlines()
    block_at = next(
        (
            i
            for i, l in enumerate(lines)
            if (m := _TOP_KEY_RE.match(l)) and m.group(1) == block
        ),
        None,
    )
    new_line = f"  {key}: {yaml_value}"
    if block_at is None:
        return text.rstrip("\n") + f"\n\n{block}:\n{new_line}\n"
    end = block_at + 1
    while end < len(lines) and not _TOP_KEY_RE.match(lines[end]):
        end += 1
    key_at = next(
        (
            i
            for i in range(block_at + 1, end)
            if (m := _CHILD_KEY_RE.match(lines[i])) and m.group(2) == key
        ),
        None,
    )
    if key_at is not None:
        indent = _CHILD_KEY_RE.match(lines[key_at]).group(1)
        lines[key_at] = f"{indent}{key}: {yaml_value}"
    else:
        lines.insert(end, new_line)
    return "\n".join(lines) + "\n"


def _yaml_str(value: str | None) -> str:
    return "null" if value is None else f'"{value}"'


def _settings_yaml(
    text: str,
    config_path: Path,
    data_dir: Path,
    fmt: str,
    task: str | None,
    excludes: list[str],
) -> str:
    """Return `text` with the interactive answers upserted; so future pipeline
    runs and future config-mode create_tsv runs see the same settings."""
    try:
        dd = str(data_dir.relative_to(_pipeline_root(config_path)))
    except ValueError:
        dd = str(data_dir)
    text = _upsert_block_key(text, "project_settings", "data_directory", _yaml_str(dd))
    text = _upsert_block_key(text, "project_settings", "input_format", _yaml_str(fmt))
    text = _upsert_block_key(text, "project_settings", "task", _yaml_str(task))
    if excludes:
        text = _upsert_block_key(
            text,
            "ingestion",
            "exclude",
            "[" + ", ".join(_yaml_str(e) for e in excludes) + "]",
        )
    return text


def _run(s: _Settings, excludes: list[str]) -> int:
    """Shared scan → filter → index → archive → write → ledger pipeline."""
    if s.fmt not in _FORMATS:
        print(f"Unsupported input_format {s.fmt!r}", file=sys.stderr)
        return 2
    scan = _FORMATS[s.fmt](s.data_dir, s.task)

    excluded: list[_Refusal] = []
    if excludes:
        remaining = []
        for r in scan.refusals:
            if any(fnmatch.fnmatch(r.source, pat) for pat in excludes):
                excluded.append(r)
            else:
                remaining.append(r)
        scan.refusals = remaining
        if excluded:
            print(
                f"create_tsv: excluded {len(excluded)} recording file(s) via skip "
                "patterns (not catalogued):",
                file=sys.stderr,
            )
            for r in excluded:
                print(f"  {r.source} — {r.reason}", file=sys.stderr)

    for wm in scan.warnings:
        print(f"WARNING: {wm}", file=sys.stderr)
    if scan.refusals:
        _refuse(scan.refusals, s.task, s.fmt)
        return 1

    def _rel(p: Path) -> str:
        try:
            return str(p.resolve().relative_to(s.root))
        except ValueError:
            return str(p)

    rows = [
        (subj, i, _rel(Path(src)))
        for subj, i, src in _index_segments(scan, s.fmt == "BrainVision")
    ]

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    arch = _archive(s.out)
    s.out.parent.mkdir(parents=True, exist_ok=True)
    with s.out.open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["subject", "segment", "source"])
        for subj, seg, src in rows:
            w.writerow([subj, seg, src])

    ledger = s.out.parent / "manifest_history.tsv"
    _append_history(
        ledger,
        {
            "timestamp": ts,
            "manifest_sha256": _sha256(s.out),
            "n_subjects": str(len({subj for subj, _, _ in rows})),
            "n_segments": str(len(rows)),
            "data_dir": str(s.data_dir),
            "fmt": s.fmt,
            "task": s.task or "",
            "mode": s.mode,
        },
    )

    if arch:
        print(f"create_tsv: archived previous manifest to {arch}")
    print(f"create_tsv: history appended to {ledger}")
    print(f"Wrote {len(rows)} segment row(s) to {s.out}")
    for subj, seg, src in rows:
        print(f"  sub-{subj}\tseg {seg}\t{src}")
    return 0


def _interactive(config_path: Path = _CONFIG) -> int:
    """Prompt for the missing bits (config values are the bracketed defaults).
    Writing the manifest and persisting the settings are confirmed separately;
    persisting may target an existing config or create a new one."""
    print("create_tsv interactive mode — press <enter> to accept [defaults]")
    ps: dict = {}
    if config_path.exists():
        ps = _load_config(config_path).get("project_settings", {})
    root = _pipeline_root(config_path)

    data_dir = None
    while data_dir is None:
        dflt = str(ps.get("data_directory") or "")
        raw = input(f"Data directory (raw data root) [{dflt}]: ").strip() or dflt
        if not raw:
            print("  a data directory is required", file=sys.stderr)
            continue
        cand = Path(raw).expanduser()
        cand = cand if cand.is_absolute() else root / cand
        if cand.is_dir():
            data_dir = cand.resolve()
        else:
            print(f"  not a directory: {cand}", file=sys.stderr)

    dflt_fmt = ps.get("input_format") or ""
    fmt = None
    while fmt not in _FORMATS:
        raw = input(
            f"Format — [1] BrainVision / [2] BIDS"
            f"{' [' + str(list(_FORMATS).index(dflt_fmt) + 1) if dflt_fmt in _FORMATS else ''}]: "
        ).strip()
        if raw in ("", "1") and (dflt_fmt in _FORMATS or raw == "1"):
            fmt = dflt_fmt if raw == "" else "BrainVision"
        elif raw == "2":
            fmt = "BIDS"

    dflt_task = str(ps.get("task") or "")
    task = input(f"Task token to keep, empty = no task filter [{dflt_task}]: ").strip()
    task = task or (dflt_task or None)

    scan = _FORMATS[fmt](data_dir, task)
    excludes: list[str] = []
    if scan.refusals:
        print(
            f"{len(scan.refusals)} recording(s) do not match configured task "
            f"{task!r}:",
            file=sys.stderr,
        )
        for r in scan.refusals:
            if input(f"  exclude {r.source} ({r.reason})? [y/N] ").strip().lower() == "y":
                excludes.append(r.source)
    for wm in scan.warnings:
        print(f"WARNING: {wm}", file=sys.stderr)

    dflt_out = str(_load_config(config_path).get("ingestion", {}).get("manifest") or "metadata/manifest.tsv") \
        if config_path.exists() else "metadata/manifest.tsv"
    out = input(f"Manifest path [{dflt_out}]: ").strip() or dflt_out
    out = Path(out).expanduser()
    out = out if out.is_absolute() else root / out

    rc = 0
    if input(f"Write the manifest to {out}? [y/N] ").strip().lower() == "y":
        rc = _run(_Settings(data_dir, fmt, task, out, root, "interactive"), excludes)
        if rc != 0:
            return rc
    else:
        print("Manifest not written.", file=sys.stderr)

    if input("Persist these settings to a config file? [y/N] ").strip().lower() == "y":
        target = input(
            f"Config file to amend or create [{config_path}]: "
        ).strip() or str(config_path)
        target = Path(target).expanduser()
        target = target if target.is_absolute() else root / target
        if target.exists():
            base_text = target.read_text()
        elif input(f"  {target} does not exist — create it? [y/N] ").strip().lower() == "y":
            # seed from the module's default config so the new file keeps the full schema
            base_text = (
                _CONFIG.read_text()
                if _CONFIG.exists()
                else "# p0ly-flow configuration\n\nproject_settings:\n"
            )
        else:
            print("  settings not persisted.", file=sys.stderr)
            base_text = None
        if base_text is not None:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                _settings_yaml(base_text, target, data_dir, fmt, task, excludes)
            )
            print(f"create_tsv: persisted settings to {target}")
    return rc


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("config", nargs="?", help="config mode: YAML with project_settings")
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="interactive mode: prompt for data_dir/task/output; writing the "
        "manifest and persisting to a config are confirmed separately",
    )
    parser.add_argument("--data-dir", help="flags mode: raw data root (relative paths anchor at the pipeline root)")
    parser.add_argument(
        "--data-fmt",
        choices=_FORMATS,
        help="flags mode: input format (BrainVision or BIDS)",
    )
    parser.add_argument(
        "--task",
        help="flags mode: keep only task-{...} recordings (default: all)",
    )
    parser.add_argument(
        "--out",
        help="flags mode: manifest output path (default: metadata/manifest.tsv)",
    )
    parser.add_argument(
        "--exclude",
        "-e",
        action="append",
        default=[],
        metavar="PATTERN",
        help="fnmatch glob against the recording path — matching refusals are "
        "skipped (printed, never catalogued) instead of hard-erroring (also "
        "read from `ingestion.exclude` in config mode)",
    )

    args = parser.parse_args(argv)
    using_flags = bool(args.data_dir or args.data_fmt)
    if args.interactive and (using_flags or args.config):
        parser.error("--interactive cannot be combined with config or flags settings")
    if using_flags and args.config:
        parser.error("config path and --data-dir/--data-fmt are mutually exclusive")

    if args.interactive:
        return _interactive()
    if using_flags:
        missing = [
            f
            for f, v in (("--data-dir", args.data_dir), ("--data-fmt", args.data_fmt))
            if not v
        ]
        if missing:
            parser.error(
                f"flags mode requires both --data-dir and --data-fmt "
                f"(missing {missing[0]})"
            )
        root = _pipeline_root()
        out = Path(args.out).expanduser() if args.out else _DEFAULT_OUT
        out = out if out.is_absolute() else root / out
        data_dir = Path(args.data_dir).expanduser()
        data_dir = data_dir if data_dir.is_absolute() else root / data_dir
        return _run(
            _Settings(
                data_dir=data_dir,
                fmt=args.data_fmt,
                task=args.task or None,
                out=out,
                root=root,
                mode="flags",
            ),
            list(args.exclude),
        )
    if args.config is None:
        return _interactive()

    config_path = Path(args.config)
    cfg = _load_config(config_path)
    ps = cfg["project_settings"]
    root = _pipeline_root(config_path)
    return _run(
        _Settings(
            data_dir=(root / ps["data_directory"]).resolve(),
            fmt=ps["input_format"],
            task=ps.get("task"),
            out=root / cfg.get("ingestion", {}).get("manifest", _DEFAULT_OUT),
            root=root,
            mode="config",
        ),
        list(args.exclude) + list(cfg.get("ingestion", {}).get("exclude", [])),
    )


if __name__ == "__main__":
    raise SystemExit(main())
