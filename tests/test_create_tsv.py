"""US-025: task filter, acquisition-time ordering, and BIDS dedup in the manifest."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
_spec = importlib.util.spec_from_file_location("create_tsv", _SCRIPTS / "create_tsv.py")
create_tsv = importlib.util.module_from_spec(_spec)
sys.modules["create_tsv"] = create_tsv
assert _spec.loader is not None
_spec.loader.exec_module(create_tsv)


def _vmrk(
    path: Path,
    markers: list[str],
    *,
    dates: list[str] | None = None,
) -> Path:
    """Minimal BrainVision marker file `New Segment` fixtures start every recording."""
    lines = ["Brainvision Data Exchange Marker File, Version 1.0", "", "[Common Infos]"]
    recs = []
    for i, m in enumerate(markers, start=1):
        date = f",{dates[i - 1]}" if dates and dates[i - 1] else ""
        recs.append(f"Mk{i}={m},,{10**6 * i},1,0{date}")
    lines += ["DataFile=x.eeg", "", "[Marker Infos]"] + recs
    path.write_text("\n".join(lines), encoding="cp1252")
    return path


@pytest.fixture()
def scan():
    def f(fmt_dir: Path, task: str):
        return (
            create_tsv._scan_brainvision(fmt_dir, task)
            if (fmt_dir.name.startswith("bv"))
            else create_tsv._scan_bids(fmt_dir, task)
        )

    return f


# --- AC: task filter + no-token refusal ----------------------------------------


def test_filter_pass(tmp_path):
    (tmp_path / "sub-001").mkdir()
    (tmp_path / "sub-001" / "sub-001_task-dmss.vhdr").write_text("")
    (tmp_path / "sub-001" / "sub-001_task-dmss.vmrk").write_text("")
    s = create_tsv._scan_brainvision(tmp_path, "dmss")
    assert s.refusals == []
    assert s.sources == [("001", str(tmp_path / "sub-001" / "sub-001_task-dmss.vhdr"))]


def test_filter_refuses_other_task(tmp_path):
    d = tmp_path / "sub-001"
    d.mkdir()
    match = d / "sub-001_task-rest.vhdr"
    match.write_text("")
    (d / "sub-001_task-dmss.vhdr").write_text("")
    (d / "sub-001_task-dmss.vmrk").write_text("")
    s = create_tsv._scan_brainvision(tmp_path, "rest")
    assert s.sources == [("001", str(match))]
    assert len(s.refusals) == 1
    assert re.search(r"task-dmss", s.refusals[0].reason)


def test_refuse_no_task_token(tmp_path):
    (tmp_path / "sub-001").mkdir()
    (tmp_path / "sub-001" / "sub-001.vhdr").write_text("")
    s = create_tsv._scan_brainvision(tmp_path, "rest")
    assert s.sources == []  # never assumed; the tokenless file cannot be matched
    assert len(s.refusals) == 1
    assert "no task token" in s.refusals[0].reason


# --- AC: acquisition-time ordering via `New Segment` markers -------------------


def test_order_by_marker_timestamps(tmp_path):
    d1 = tmp_path / "sub-001"
    d1.mkdir(exist_ok=True)
    # filename order and timestamp order deliberately disagree (b written first)
    b = d1 / "sub-001_task-dmss_b.vhdr"
    a = d1 / "sub-001_task-dmss_a.vhdr"
    for f in (b, a):
        f.write_text("")
    _vmrk(
        b.with_suffix(".vmrk"),
        ["New Segment", "Stimulus"],
        dates=["20250101100000000000", ""],
    )
    _vmrk(
        a.with_suffix(".vmrk"),
        ["New Segment", "Stimulus"],
        dates=["20250101100000000000", ""],
    )
    # `_vmrk` timestamps saturate positions, not dates; craft distinct dates by rewrite
    dates = {"b": "20240203080000000000", "a": "20240203120000000000"}
    _vmrk(
        b.with_suffix(".vmrk"),
        ["New Segment", "Stimulus"],
        dates=[dates["b"], ""],
    )
    _vmrk(
        a.with_suffix(".vmrk"),
        ["New Segment", "Stimulus"],
        dates=[dates["a"], ""],
    )
    s = create_tsv._scan_brainvision(tmp_path, "dmss")
    rows = create_tsv._index_segments(s, True)
    assert [r[2] for r in rows if r[0] == "001" and r[1] == 1] == [str(b)]
    assert [r[2] for r in rows if r[0] == "001" and r[1] == 2] == [str(a)]
    assert s.warnings == []


def test_order_fallback_lexicographic_with_warning(tmp_path):
    d = tmp_path / "sub-001"
    d.mkdir()
    # name order also the true order; but timestamps absent -> must warn, not guess
    first = d / "sub-001_task-dmss_a.vhdr"
    second = d / "sub-001_task-dmss_z.vhdr"
    for f in (first, second):
        f.write_text("")
    _vmrk(second.with_suffix(".vmrk"), ["Stimulus"], dates=["20250101"])
    s = create_tsv._scan_brainvision(tmp_path, "dmss")
    rows = create_tsv._index_segments(s, True)
    assert rows == [
        ("001", 1, str(first)),
        ("001", 2, str(second)),
    ]
    assert len(s.warnings) == 1
    assert "New Segment" in s.warnings[0]
    assert str(first.with_suffix(".vmrk")) in s.warnings[0]
    assert str(second.with_suffix(".vmrk")) in s.warnings[0]


# --- AC: BIDS duplicate-extension dedup ---------------------------------------


def test_bids_dedup_and_task_refusal(tmp_path):
    eeg = tmp_path / "sub-001" / "eeg"
    eeg.mkdir(parents=True)
    stem = "sub-001_task-dmss_eeg"
    for ext in ("vhdr", "edf"):
        (eeg / f"{stem}.{ext}").write_text("")
    # one wrong-task recording to exercise the refusal listing too
    (eeg / "sub-001_task-rest_eeg.edf").write_text("")
    s = create_tsv._scan_bids(tmp_path, "dmss")
    # one logical recording, kept as the canonical .vhdr spelling
    assert s.sources == [("001", str(eeg / f"{stem}.vhdr"))]
    # the .edf twin is a warning (same recording, not a different segment)...
    assert any(f"{stem}.edf" in w for w in s.warnings)
    # ...while task-rest is a hard refusal (different task, currently configured)
    assert len(s.refusals) == 1
    assert "task-rest" in s.refusals[0].reason


# --- AC: CLI end-to-end refusal (no manifest written) --------------------------


def test_main_refuses_without_writing(tmp_path, capsys):
    raw = tmp_path / "data" / "raw" / "sub-001"
    raw.mkdir(parents=True)
    (raw / "sub-001_task-rest.vhdr").write_text("")
    (raw / "sub-001_task-dmss.vhdr").write_text("")
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "project_settings:\n"
        "  input_format: BrainVision\n"
        "  data_directory: data/raw\n"
        "  task: rest\n"
        "ingestion:\n"
        "  manifest: metadata/manifest.tsv\n"
    )
    out = tmp_path / "metadata" / "manifest.tsv"
    rc = create_tsv.main([str(cfg)])
    assert rc == 1
    assert not out.exists()
    err = capsys.readouterr().err
    assert "sub-001_task-dmss.vhdr" in err
    assert "task-dmss" in err


def test_main_filters_and_writes(tmp_path, capsys):
    raw = tmp_path / "data" / "raw" / "sub-001"
    raw.mkdir(parents=True)
    (raw / "sub-001_task-dmss.vhdr").write_text("")
    _vmrk(raw / "sub-001_task-dmss.vmrk", ["New Segment"], dates=["20250101", ""])
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "project_settings:\n"
        "  input_format: BrainVision\n"
        "  data_directory: data/raw\n"
        "  task: dmss\n"
        "ingestion:\n"
        "  manifest: metadata/manifest.test.tsv\n"
    )
    out = tmp_path / "metadata" / "manifest.test.tsv"
    rc = create_tsv.main([str(cfg)])
    assert rc == 0
    text = out.read_text()
    # output path honoured from `ingestion.manifest` (not the hardcoded default)
    assert "001\t1\t" in text
    assert "task-dmss" in text
    assert "task-rest" not in text
