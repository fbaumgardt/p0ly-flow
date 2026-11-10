"""Map result files back to the manifest build that produced them (US-009).

Reads ``metadata/manifest_history.tsv`` — the ledger ``create_tsv.py`` appends
to on every manifest build. For each given file (or directory, searched
recursively), the newest ledger entry whose timestamp is at or before the
file's mtime names the manifest it was built from. Files older than the
current manifest are flagged as stale (they predate the last rebuild).

Usage::

    uv run python scripts/which_manifest.py data/derivatives some/file.fif
"""

from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

_TS_FMT = "%Y%m%dT%H%M%S.%fZ"


def _its_time(ts: str) -> float:
    return datetime.strptime(ts, _TS_FMT).replace(tzinfo=timezone.utc).timestamp()


def report(targets: list[Path], ledger: Path, manifest: Path) -> list[str]:
    """One line per file: covering ledger entry, plus a STALE flag."""
    rows: list[dict] = []
    if ledger.exists():
        with ledger.open() as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
    manifest_mtime = manifest.stat().st_mtime if manifest.exists() else float("inf")

    out: list[str] = []
    for target in targets:
        files = sorted(target.rglob("*")) if target.is_dir() else [target]
        for file in files:
            if not file.is_file():
                continue
            m = file.stat().st_mtime
            covers = [r for r in rows if _its_time(r["timestamp"]) <= m]
            if not covers:
                out.append(f"{file}: predates every ledger entry (built before provenance tracking)")
                continue
            r = covers[-1]
            line = (
                f"{file}: manifest build {r['timestamp']} "
                f"sha {r['manifest_sha256'][:12]} task={r['task'] or '∅'} mode={r['mode']}"
            )
            if m < manifest_mtime:
                line += " — STALE: manifest rebuilt since"
            out.append(line)
    return out


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    metadata = Path(__file__).resolve().parent.parent / "metadata"
    ledger = metadata / "manifest_history.tsv"
    if not ledger.exists():
        print(f"no {ledger} — run create_tsv.py first", file=sys.stderr)
        return 2
    targets = [Path(a) for a in argv] or [metadata.parent / "data" / "derivatives"]
    missing = [t for t in targets if not t.exists()]
    if missing:
        print(f"no such file(s): {', '.join(map(str, missing))}", file=sys.stderr)
        return 2
    lines = report(targets, ledger, metadata / "manifest.tsv")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
