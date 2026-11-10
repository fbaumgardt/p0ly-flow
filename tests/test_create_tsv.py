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


# --- US-013 deferral: --exclude skips matching refusals, prints them loud -------


_EXCLUDE_CFG = (
    "project_settings:\n"
    "  input_format: BrainVision\n"
    "  data_directory: data/raw\n"
    "  task: rest\n"
    "ingestion:\n"
    "  manifest: metadata/manifest.tsv\n"
)


def _raw_outlier(tmp_path: Path) -> None:
    (tmp_path / "data" / "raw" / "sub-001").mkdir(parents=True)
    good = tmp_path / "data" / "raw" / "sub-001" / "sub-001_task-rest.vhdr"
    good.write_text("")
    (tmp_path / "data" / "raw" / "sub-001" / "sub-001_task-video.vhdr").write_text("")


def test_exclude_skips_matching_refusal_and_writes(tmp_path, capsys):
    _raw_outlier(tmp_path)
    cfg = tmp_path / "config.yaml"
    cfg.write_text(_EXCLUDE_CFG)
    out = tmp_path / "metadata" / "manifest.tsv"
    rc = create_tsv.main([str(cfg), "--exclude", "*task-video*"])
    assert rc == 0
    assert out.exists()
    text = out.read_text()
    assert "task-rest" in text
    assert "task-video" not in text
    # excluded files are never silently skipped: they are printed, with reason
    err = capsys.readouterr().err
    assert "excluded 1 recording file(s)" in err
    assert "task-video" in err


def test_exclude_nonmatching_pattern_still_refuses(tmp_path):
    _raw_outlier(tmp_path)
    cfg = tmp_path / "config.yaml"
    cfg.write_text(_EXCLUDE_CFG)
    out = tmp_path / "metadata" / "manifest.tsv"
    rc = create_tsv.main([str(cfg), "--exclude", "*sub-002*"])
    assert rc == 1
    assert not out.exists()




# --- US-013 deferral (W27/W28): null task disables the task-axis gate -----------


def test_null_task_catalogues_every_recording(tmp_path):
    d = tmp_path / "sub-001"
    d.mkdir()
    (d / "sub-001_task-dmss.vhdr").write_text("")
    (d / "sub-001_task-rest.vhdr").write_text("")
    (d / "sub-001.vhdr").write_text("")
    scan = create_tsv._scan_brainvision(tmp_path, None)
    # sources come back in the scanner's lexicographic order; the point is
    # all three recordings pass the (disabled) task gate with zero refusals
    assert sorted(src for _, src in scan.sources) == [
        str(d / "sub-001.vhdr"),
        str(d / "sub-001_task-dmss.vhdr"),
        str(d / "sub-001_task-rest.vhdr"),
    ]
    assert scan.refusals == []


# --- three-mode CLI: flags, interactive, provenance ledger ---------------------

import builtins
import hashlib
import importlib.util
import os

_spec_wm = importlib.util.spec_from_file_location(
    "which_manifest", _SCRIPTS / "which_manifest.py"
)
which_manifest = importlib.util.module_from_spec(_spec_wm)
sys.modules["which_manifest"] = which_manifest
assert _spec_wm.loader is not None
_spec_wm.loader.exec_module(which_manifest)


def _one_recording(tmp_path: Path, task: str = "dmss") -> Path:
    d = tmp_path / "raw" / "sub-001"
    d.mkdir(parents=True)
    (d / f"sub-001_task-{task}.vhdr").write_text("")
    (d / f"sub-001_task-{task}.vmrk").write_text("")
    return tmp_path / "raw"


_FLAGS_CFG = """\
project_settings:
  data_directory: raw
  input_format: BrainVision
  task: dmss
"""


def test_flags_mode_writes_manifest_and_ledger(tmp_path, monkeypatch):
    d = _one_recording(tmp_path)
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "metadata" / "manifest.tsv"
    rc = create_tsv.main(
        ["--data-dir", str(d), "--data-fmt", "BrainVision", "--task", "dmss", "--out", str(out)]
    )
    assert rc == 0
    text = out.read_text()
    assert "sub-001" in text
    ledger = out.parent / "manifest_history.tsv"
    lines = ledger.read_text().strip().splitlines()
    assert lines[0].split("\t")[:2] == ["timestamp", "manifest_sha256"]
    sha, n_seg, mode_col = (
        lines[1].split("\t")[1], lines[1].split("\t")[3], lines[1].split("\t")[7]
    )
    assert sha == hashlib.sha256(out.read_bytes()).hexdigest()
    assert n_seg == "1" and mode_col == "flags"


def test_flags_mode_requires_both_settings(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        create_tsv.main(["--data-dir", str(tmp_path)])


def test_rebuilds_archive_previous_and_append_ledger(tmp_path, monkeypatch):
    d = _one_recording(tmp_path)
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "metadata" / "manifest.tsv"
    for _ in range(2):
        assert create_tsv.main(["--data-dir", str(d), "--data-fmt", "BrainVision", "--out", str(out)]) == 0
    archived = list((out.parent / "archive").glob("manifest-*.tsv"))
    assert len(archived) == 1  # first build had no previous manifest to archive
    assert len((out.parent / "manifest_history.tsv").read_text().strip().splitlines()) == 3  # header + 2 builds


def test_interactive_prompts_and_persists(tmp_path, monkeypatch):
    d = _one_recording(tmp_path)
    monkeypatch.chdir(tmp_path)
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        "project_settings:\n"
        "  data_directory: raw\n"
        "  input_format: BrainVision\n"
        "  task: null\n"
    )
    out = tmp_path / "metadata" / "manifest.tsv"
    # write and persist are separate confirmations; blank config target = default
    answers = iter([str(d), "1", "dmss", str(out), "y", "y", ""])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(answers))
    rc = create_tsv._interactive(cfg)
    assert rc == 0
    assert out.exists()

    import yaml

    updates = yaml.safe_load(cfg.read_text())["project_settings"]
    assert updates["task"] == "dmss"
    assert updates["input_format"] == "BrainVision"
    ledger = out.parent / "manifest_history.tsv"
    assert ledger.read_text().strip().splitlines()[1].split("\t")[7] == "interactive"

    # …and to a NEW config, seeded from configs/default.yaml (full schema kept)
    new_cfg = tmp_path / "configs" / "study.yaml"
    answers = iter([str(d), "1", "dmss", str(out), "n", "y", str(new_cfg), "y"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(answers))
    assert create_tsv._interactive(cfg) == 0
    import yaml as _y

    study = _y.safe_load(new_cfg.read_text())
    assert study["project_settings"]["task"] == "dmss"
    assert study["project_settings"]["data_directory"] == str(d)  # absolute: not under the new config's root
    assert "analysis:" in new_cfg.read_text()  # schema blocks survived seeding

    # a later interactive run with one refusal excluded persists the skip pattern
    (tmp_path / "raw" / "sub-002").mkdir()
    (tmp_path / "raw" / "sub-002" / "sub-002_task-other.vhdr").write_text("")
    (tmp_path / "raw" / "sub-002" / "sub-002_task-other.vmrk").write_text("")
    answers = iter([str(d), "1", "dmss", "y", str(out), "y", "y", ""])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(answers))
    assert create_tsv._interactive(cfg) == 0
    assert _y.safe_load(cfg.read_text())["ingestion"]["exclude"] == [
        str(tmp_path / "raw" / "sub-002" / "sub-002_task-other.vhdr")
    ]


def test_config_mode_honors_ingestion_exclude(tmp_path, capsys):
    d = tmp_path / "raw" / "sub-001"
    d.mkdir(parents=True)
    (d / "sub-001_task-dmss.vhdr").write_text("")
    (d / "sub-001_task-dmss.vmrk").write_text("")
    (tmp_path / "raw" / "sub-002").mkdir()
    (tmp_path / "raw" / "sub-002" / "sub-002_task-video.vhdr").write_text("")
    (tmp_path / "raw" / "sub-002" / "sub-002_task-video.vmrk").write_text("")
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "project_settings:\n"
        "  data_directory: raw\n"
        "  input_format: BrainVision\n"
        "  task: dmss\n"
        "ingestion:\n"
        "  manifest: metadata/manifest.tsv\n"
        "  exclude:\n"
        '    - "*task-video*"\n'
    )
    out = tmp_path / "metadata" / "manifest.tsv"
    rc = create_tsv.main([str(cfg)])
    assert rc == 0
    assert out.exists()
    assert "task-video" not in out.read_text()
    assert "excluded 1 recording file(s)" in capsys.readouterr().err


def test_which_manifest_maps_files_to_ledger(tmp_path):
    out = tmp_path / "metadata" / "manifest.tsv"
    out.parent.mkdir(parents=True)
    out.write_text("subject\tsegment\tsource\n")
    ledger = tmp_path / "metadata" / "manifest_history.tsv"
    ledger.write_text(
        "timestamp\tmanifest_sha256\tn_subjects\tn_segments\tdata_dir\tfmt\ttask\tmode\n"
        "20200101T000000.000000Z\t" + "a" * 64 + "\t1\t1\traw\tBrainVision\tdmss\tconfig\n"
    )
    result = tmp_path / "deriv" / "out.fif"
    result.parent.mkdir(parents=True)
    result.write_text("x")
    # normal: file newer than the ledger entry, manifest rebuilt after it → stale
    os.utime(result, (1_600_000_000, 1_600_000_000))
    os.utime(out, (1_600_000_001, 1_600_000_001))
    lines = which_manifest.report([tmp_path / "deriv"], ledger, out)
    assert len(lines) == 1
    assert "20200101T000000.000000Z" in lines[0]
    assert "STALE" in lines[0]
    # fresh: file rebuilt after the manifest rebuild → not stale
    os.utime(result, (1_700_000_002, 1_700_000_002))
    lines = which_manifest.report([tmp_path / "deriv"], ledger, out)
    assert "STALE" not in lines[0]
