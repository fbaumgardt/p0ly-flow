# p0ly-flow Snakemake DAG

# --- Config ---
configfile: "config.yaml"

# --- Config-derived path roots (no hardcoded directories in rules) ---
_DATA_DIR = config["project_settings"]["data_directory"].rstrip("/")
_OUT_DIR = config["project_settings"]["output_directory"].rstrip("/")
_TASK = config["project_settings"]["task"]
_FMT = config["project_settings"]["input_format"]

# Preprocessing config. All keys optional; ica_strategy present =>
# the preprocess rule also emits a fitted-ICA sidecar (see _ICA_OUT below).
_PP = config["preprocessing"]
_ICA_ENABLED = _PP.get("ica_strategy") is not None

# Metadata config. The experiment spec drives trial/Block/Onset
# extraction; csv_columns and expand_trials are optional companions.
_META = config["metadata"]

# The timelock set is derived from the experiment spec itself
# (``ExperimentSpec.timelocks`` keys) so no timelock literals live in the
# Snakefile. ``p0ly_utils`` is already a dependency, so the spec is loaded at
# DAG-parse time.
from p0ly_utils.metadata import ExperimentSpec

_TIMELOCKS = list(ExperimentSpec.from_yaml(_META["experiment_spec"]).timelocks.keys())

# Optional ICA output path (declared as a plain value, not a function —
# Snakemake only allows callables for `input:`, not `output:`). Empty list
# when ICA is disabled so the rule emits no ICA file in that case.
_ICA_OUT = (
    f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_desc-ica.fif.gz"
    if _ICA_ENABLED
    else []
)

# `rule all` ICA target expansion (empty list when ICA disabled).
_ICA_TARGETS = (
    expand(_ICA_OUT, subject=config["subjects"])
    if _ICA_ENABLED
    else []
)

# --- Group analysis config (US-010) ---
#
# ERP grand averages + cluster permutation contrasts (PRD stage 5). The
# implicit `all_trials` condition carries no query, so one grand average per
# timelock always exists even when `condition_splits` is empty; contrasts
# enumerate the unordered pairs of the explicit condition splits only (US-010
# Notes: all_trials is an average target, never a contrast arm).
from itertools import combinations

_ERP_ENABLED = config["analysis"]["run_erp"]
_ERP_SPLITS = config["group_aggregation"]["condition_splits"]
if "all_trials" in _ERP_SPLITS:
    raise ValueError(
        "config group_aggregation.condition_splits must not redefine the "
        "reserved 'all_trials' condition"
    )
_ERP_QUERIES = {"all_trials": None, **_ERP_SPLITS}
_ERP_STATS = config["erp"] if _ERP_ENABLED else {}
_ERP_CONTRASTS = {
    f"{first}-vs-{second}": (first, second)
    for first, second in combinations(_ERP_SPLITS, 2)
}
# Cluster permutation contrasts are a one-sample test over per-subject
# difference waves, so they need >= 2 subjects (grand averages stay valid for
# a single-subject bootstrap; adding subjects re-parses the DAG and re-enables
# the contrast targets).
_ERP_CONTRASTS_ENABLED = (
    _ERP_ENABLED and len(_ERP_CONTRASTS) > 0 and len(config["subjects"]) >= 2
)
if _ERP_ENABLED and _ERP_CONTRASTS and not _ERP_CONTRASTS_ENABLED:
    print(
        f"run_erp: only {len(config['subjects'])} subject(s) configured — "
        "cluster permutation contrast targets omitted from the DAG; "
        "grand averages only (re-parse after adding subjects)"
    )

# Per-subject condition averages (rule erp_subject): keep every channel as a
# QC artifact; EEG-only selection + stats happen inside the library call.
_ERP_AVE_OUT = (
    f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_{{timelock}}_{{condition}}_desc-ave.fif.gz"
)
# Flat per-timelock group layout (US-010 decision); US-015 will slot the
# {cohort} wildcard in between for cohort-condition expansion.
_ERP_GROUP_AVE_OUT = (
    f"{_OUT_DIR}/group_analysis/{{timelock}}/{{condition}}_desc-ave.fif.gz"
)
_ERP_CONTRAST_NPZ_OUT = (
    f"{_OUT_DIR}/group_analysis/{{timelock}}/{{contrast}}_clusterperm.npz"
)
_ERP_CONTRAST_CSV_OUT = (
    f"{_OUT_DIR}/group_analysis/{{timelock}}/{{contrast}}_clusterperm.csv"
)

# `rule all` ERP target expansion (empty list when analysis.run_erp is false;
# contrast families additionally gated to cohorts with >= 2 subjects).
_ERP_TARGETS = (
    (
        expand(
            _ERP_GROUP_AVE_OUT,
            timelock=_TIMELOCKS,
            condition=list(_ERP_QUERIES),
        )
        + (
            expand(
                [_ERP_CONTRAST_NPZ_OUT, _ERP_CONTRAST_CSV_OUT],
                timelock=_TIMELOCKS,
                contrast=list(_ERP_CONTRASTS),
            )
            if _ERP_CONTRASTS_ENABLED
            else []
        )
    )
    if _ERP_ENABLED
    else []
)

# --- PSD Analysis Layer (US-011) ---
#
# Absolute/relative band power + specparam aperiodic parameterization (PRD
# stage 5). The condition set is shared with the ERP layer (_ERP_QUERIES,
# built above with the all_trials guard). No statistics live in this module,
# so single-subject cohorts run the full rule set (no n >= 2 gating).
_PSD_ENABLED = config["analysis"]["run_psd"]
_PSD_QUERIES = _ERP_QUERIES
_PSD_SETTINGS = config["psd"] if _PSD_ENABLED else {}

# Per-subject condition spectra (rule psd_subject): every channel kept as a
# QC artifact. Containers are MNE Spectrum HDF5 files (h5io — Spectrum.save's
# native format; read back via mne.time_frequency.read_spectrum), NOT FIF:
# Spectrum persistence is HDF5-only in MNE 1.12. Flat per-timelock group
# layout (ADR-007 pattern; US-015 will slot the {cohort} wildcard in between).
_PSD_SUBJECT_OUT = (
    f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_{{timelock}}_{{condition}}_desc-psd.h5"
)
_PSD_GROUP_OUT = (
    f"{_OUT_DIR}/group_analysis/{{timelock}}/{{condition}}_desc-psd_ave.h5"
)
_PSD_PARAMS_OUT = (
    f"{_OUT_DIR}/group_analysis/{{timelock}}/{{condition}}_desc-psd_params.csv"
)
_PSD_BANDPOWER_OUT = (
    f"{_OUT_DIR}/group_analysis/{{timelock}}/{{condition}}_desc-psd_bandpower.csv"
)

# `rule all` PSD target expansion (empty list when analysis.run_psd is false);
# per-subject spectra stay intermediates feeding the group rules.
_PSD_TARGETS = (
    expand(
        [_PSD_GROUP_OUT, _PSD_PARAMS_OUT, _PSD_BANDPOWER_OUT],
        timelock=_TIMELOCKS,
        condition=list(_PSD_QUERIES),
    )
    if _PSD_ENABLED
    else []
)

# --- TFR Analysis Layer (US-012) ---
#
# Morlet/multitaper complex TFR (one convolution) -> per-subject two-entry
# HDF5 files ([0] = epoch-mean power, [1] = ITPC — documented positional
# convention, verified by the rule scripts on read) + grand averages +
# per-contrast difference maps. Mirrors the PSD layer (ADR-007): condition
# set shared with ERP (_ERP_QUERIES), flat per-timelock group layout, and
# no n >= 2 gating — the difference map is a subtraction, defined at n=1
# (no statistics in this module; cluster permutation over channel x freq x
# time is a documented US-015 deferred alternative).
_TFR_ENABLED = config["analysis"]["run_tfr"]
_TFR_QUERIES = _ERP_QUERIES
_TFR_SETTINGS = config["tfr"] if _TFR_ENABLED else {}

# Per-subject condition TFRs (rule tfr_subject): every channel kept as a QC
# artifact. Containers are two-entry AverageTFR HDF5 files (h5io family via
# mne.time_frequency.write_tfrs/read_tfrs — verified live in MNE 1.12.1).
_TFR_SUBJECT_OUT = (
    f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_{{timelock}}_{{condition}}_desc-tfr.h5"
)
_TFR_GROUP_OUT = (
    f"{_OUT_DIR}/group_analysis/{{timelock}}/{{condition}}_desc-tfr_ave.h5"
)
_TFR_DIFF_OUT = (
    f"{_OUT_DIR}/group_analysis/{{timelock}}/{{contrast}}_desc-tfrdiff.h5"
)

# `rule all` TFR target expansion (empty when analysis.run_tfr is false);
# per-subject TFRs stay intermediates feeding the group rules. Contrast
# naming shares the ERP contrast set (unordered pairs of condition_splits).
_TFR_TARGETS: list[str]
if _TFR_ENABLED:
    _TFR_TARGETS = expand(
        _TFR_GROUP_OUT,
        timelock=_TIMELOCKS,
        condition=list(_TFR_QUERIES),
    )
    if _ERP_CONTRASTS:
        _TFR_TARGETS += expand(
            _TFR_DIFF_OUT,
            timelock=_TIMELOCKS,
            contrast=list(_ERP_CONTRASTS),
        )
else:
    _TFR_TARGETS = []

# --- Connectivity Analysis Layer (US-013) ---
#
# One mne-connectivity call computes every configured method (wPLI /
# coherence / PLV) per (subject × timelock × condition) -> per-method
# adjacency (n_channels, n_channels, n_freqs) flattened to .npz archives +
# grand averages + graph metrics of the band-averaged group adjacencies.
# Mirrors the TFR/PSD layers (ADR-007): condition set shared with ERP
# (_ERP_QUERIES), flat per-timelock group layout, and no n >= 2 gating —
# graph metrics of a grand-averaged adjacency are defined at n=1 (no
# statistics in this module).
_CONN_ENABLED = config["analysis"]["run_connectivity"]
_CONN_QUERIES = _ERP_QUERIES
_CONN_SETTINGS = config["connectivity"] if _CONN_ENABLED else {}

# Per-subject condition connectivity (rule connectivity_subject): every
# channel kept as a QC artifact. Containers are .npz archives — one
# (n_channels, n_channels, n_freqs) adjacency per method + ch_names + freqs.
_CONN_SUBJECT_OUT = (
    f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_{{timelock}}_{{condition}}_desc-conn.npz"
)
_CONN_GROUP_OUT = (
    f"{_OUT_DIR}/group_analysis/{{timelock}}/{{condition}}_desc-conn_ave.npz"
)
_CONN_GRAPH_OUT = (
    f"{_OUT_DIR}/group_analysis/{{timelock}}/{{condition}}_desc-conn_graph.csv"
)

# `rule all` connectivity target expansion (empty when
# analysis.run_connectivity is false); per-subject archives stay
# intermediates feeding the group rules. No contrast family here: graph
# metrics of a difference adjacency would compound two biases (averaging
# flipped-coupled pairs) — per-condition graphs only (deferred to US-015).
_CONN_TARGETS: list[str]
if _CONN_ENABLED:
    _CONN_TARGETS = expand(
        _CONN_GROUP_OUT,
        timelock=_TIMELOCKS,
        condition=list(_CONN_QUERIES),
    ) + expand(
        _CONN_GRAPH_OUT,
        timelock=_TIMELOCKS,
        condition=list(_CONN_QUERIES),
    )
else:
    _CONN_TARGETS = []

# --- Wildcard Constraints ---
wildcard_constraints:
    subject = r"\d+",
    timelock = r"[a-z]+",
    condition = r"[a-z_]+",
    contrast = r"[a-z_]+-vs-[a-z_]+"


# --- Manifest-driven ingestion input resolver (US-009) ---
#
# `metadata/manifest.tsv` (path from `config.yaml ingestion.manifest`) is the
# single source of truth for *which recording segments exist per subject*
# (ADR-005 §3 amendment). One row per segment: (subject, segment, source).
# The `raw_ingestion` rule resolves every source for a subject and merges the
# segments in one shot (no per-segment intermediate FIFs — collapsed in the
# first US-009 step). Regenerate the manifest after adding/raw-arranging data
# via `scripts/create_tsv.py` (standalone CLI, not a Snakemake script).
import pandas as _pd

_MANIFEST = config["ingestion"]["manifest"]

# One row per recording segment: (subject, segment, source). subject/segment
# are forced to str so wildcard comparisons (always str) match the manifest.
# groupby(sort=False) preserves manifest row order within each subject.
_MANIFEST_ROWS: dict[str, list[tuple[str, str]]] = (
    _pd.read_csv(
        _MANIFEST, sep="\t", dtype={"subject": str, "segment": str}
    )
    .groupby("subject", sort=False)[["segment", "source"]]
    .apply(lambda _g: list(_g.itertuples(index=False, name=None)))
    .to_dict()
)


def _subject_sources(subject: str) -> list[str]:
    return [src for _, src in _MANIFEST_ROWS.get(subject, [])]


# --- Target Rule ---
rule all:
    input:
        expand(
            f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_desc-raw.fif.gz",
            subject=config["subjects"],
        ),
        expand(
            f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_desc-clean-raw.fif.gz",
            subject=config["subjects"],
        ),
        # ICA sidecar target only when ICA is enabled in config (US-008).
        _ICA_TARGETS,
        # US-016: per-subject trial metadata TSV (input to the epoch rule).
        expand(
            f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_metadata.tsv",
            subject=config["subjects"],
        ),
        # US-017: per-(subject × timelock) epochs + excluded-trials sidecar.
        expand(
            f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_{{timelock}}_desc-epo.fif.gz",
            subject=config["subjects"],
            timelock=_TIMELOCKS,
        ),
        expand(
            f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_{{timelock}}_excluded_trials.csv",
            subject=config["subjects"],
            timelock=_TIMELOCKS,
        ),
        # US-010: ERP group analysis when enabled in config (analysis.run_erp;
        # contrast families parse-time-gated to cohorts with >= 2 subjects).
        _ERP_TARGETS,
        # US-011: PSD band powers + aperiodic parameterization when enabled
        # (analysis.run_psd; no n >= 2 gating — no statistics in this module).
        _PSD_TARGETS,
        # US-012: TFR grand averages + per-contrast difference maps when
        # enabled in config (analysis.run_tfr; no n >= 2 gating — a
        # subtraction is defined at n=1).
        _TFR_TARGETS,
        # US-013: connectivity grand averages + band graph metrics when
        # enabled in config (analysis.run_connectivity; no n >= 2 gating —
        # graph metrics of a grand average are defined at n=1).
        _CONN_TARGETS,


# --- Ingestion Layer (US-007 / US-009) ---
# Manifest-driven, one rule per subject: the manifest's rows for the subject
# are resolved at DAG time (input) and merged at runtime by the script, which
# calls `p0ly_utils.merge_recordings` (BAD_break boundaries, channel/sfreq
# validation) over the per-segment Raw objects loaded via `load_raw`. No
# per-segment intermediate FIFs are written (first US-009 step); the two-rule
# split (per-segment ingest + merge) is a future scaling lever for per-segment
# parallelism if needed.
rule raw_ingestion:
    """Ingest and merge a subject's manifest-listed raw segments into one FIF.

    For each manifest row ``(segment, source)`` the script builds the per-format
    ``source`` (BV: concrete ``.vhdr`` path; BIDS: pipeline-constructed
    ``BIDSPath`` — single-segment BIDS only in this first step) and loads it via
    ``p0ly_utils.io.load_raw``, then concatenates the segments with
    ``p0ly_utils.merge.merge_recordings``. Channel types + montage are fixed on
    each segment by ``load_raw`` and preserved by ``mne.concatenate_raws``; a
    single-segment subject passes through ``merge_recordings`` unchanged.
    Output: ``sub-{subject}_desc-raw.fif.gz`` consumed by ``preprocess``.
    """
    conda:
        "envs/snakemake.yaml"
    input:
        source_paths=lambda wildcards: _subject_sources(wildcards.subject),
    output:
        f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_desc-raw.fif.gz",
    params:
        rows=lambda wildcards: _MANIFEST_ROWS.get(wildcards.subject, []),
        fmt=_FMT,
        subject="{subject}",
        task=_TASK,
        montage=config["project_settings"]["montage"],
        data_dir=_DATA_DIR,
        datatype="eeg",
    log:
        "logs/sub-{subject}/raw_ingestion.log",
    script:
        "scripts/ingest_raw.py"


# --- Preprocessing Layer (US-008) ---
rule preprocess:
    """Continuous-data preprocessing on un-segmented raw.

    Chains filter -> bad-channels -> ICA -> sliding-window reject in a single
    rule (PRD Core App §3 stage 2) so that any change to a preprocessing
    parameter recomputes the whole subject without exploding intermediate FIF
    checkpoints. All tunables arrive from config['preprocessing'] via
    snakemake.params; the rule body holds no math — algorithms live in
    p0ly_utils.preprocessing.

    Outputs:
      - sub-{subject}_desc-clean-raw.fif.gz : cleaned continuous raw carrying
        bad-interval Annotations (consumed by the downstream `epoch` rule).
      - bad_channels.json : pre-interpolation flagged channels + ica_strategy +
        ICA component-exclusion summary (``n_components``/``exclude``/``method``).
      - sub-{subject}_desc-ica.fif.gz : fitted ICA object, emitted only when
        `ica_strategy` is set in config (optional output via _ica_output).
    """
    conda:
        "envs/snakemake.yaml"
    input:
        raw=f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_desc-raw.fif.gz",
    output:
        raw=f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_desc-clean-raw.fif.gz",
        bads=f"{_OUT_DIR}/sub-{{subject}}/bad_channels.json",
        ica=_ICA_OUT,
    params:
        pp=config["preprocessing"],
    log:
        "logs/sub-{subject}/preprocess.log",
    script:
        "scripts/preprocess.py"


# --- Metadata Layer (US-016) ---
rule inject_metadata:
    """Compute by-trial metadata from the cleaned raw's event-marker Annotations.

    Reads the cleaned continuous raw (US-008 output) — which carries the
    Psychtoolbox Stim Annotations and recomputes whenever preprocessing changes
    — extracts the event frame, and runs ``p0ly_utils.metadata.parse_metadata``
    against the experiment spec referenced by ``config.yaml``
    ``metadata.experiment_spec``. Writes a per-subject TSV (SCHEMA §6:
    ``sub-{subject}_metadata.tsv``).

    Metadata only: this rule does not epoch or bind metadata to ``mne.Epochs``
    (that is US-017). The spec path, optional companion CSV, and trial-expansion
    flag all arrive from ``config['metadata']`` via ``snakemake.params`` — no
    hardcoded experiment names.
    """
    conda:
        "envs/snakemake.yaml"
    input:
        raw=f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_desc-clean-raw.fif.gz",
    output:
        f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_metadata.tsv",
    params:
        spec_path=_META["experiment_spec"],
        csv_columns=_META.get("csv_columns"),
        expand_trials=_META.get("expand_trials", False),
    log:
        "logs/sub-{subject}/inject_metadata.log",
    script:
        "scripts/parse_metadata.py"


# --- Epoching Layer (US-017) ---
rule epoch:
    """Segment each subject's clean continuous raw into per-timelock epochs.

    Cuts ``mne.Epochs`` from the timelock's annotation events using the
    analysis-run ``intervals[timelock]`` -> ``(tmin, tmax)`` (from
    ``config.yaml epoching.intervals``, ADR-006) and the shared ``baseline``
    (``config.yaml epoching.baseline``), then aligns the US-016 by-trial
    metadata TSV to those epochs via
    ``p0ly_utils.epoching.epoch_with_metadata``. Mismatches (extra epochs,
    missing epochs, bad-interval drops) are written to the per-timelock
    ``excluded_trials.csv`` sidecar (SCHEMA §6) rather than silently dropped.
    The ``{timelock}`` wildcard propagates to downstream cohort/condition /
    analysis rules (PRD §3).

    Inputs:
      - sub-{subject}_desc-clean-raw.fif.gz : US-008 cleaned continuous raw
        carrying event-marker + bad-interval Annotations.
      - sub-{subject}_metadata.tsv : US-016 by-trial metadata.
    Outputs:
      - sub-{subject}_{timelock}_desc-epo.fif.gz : epochs with aligned metadata.
      - sub-{subject}_{timelock}_excluded_trials.csv : mismatch log.

    The timelock set comes from the experiment spec (``_TIMELOCKS`` above),
    not config literals; per-timelock ``(tmin, tmax)`` come from
    ``config.yaml epoching.intervals`` (ADR-006: windows are analysis-run
    config; the spec owns the event-code map only).  No segmentation/
    alignment math here -- algorithms live in p0ly-eeg.
    """
    conda:
        "envs/snakemake.yaml"
    input:
        raw=f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_desc-clean-raw.fif.gz",
        metadata=f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_metadata.tsv",
    output:
        epochs=f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_{{timelock}}_desc-epo.fif.gz",
        excluded=f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_{{timelock}}_excluded_trials.csv",
    params:
        spec_path=_META["experiment_spec"],
        baseline=config["epoching"]["baseline"],
        intervals=config["epoching"]["intervals"],
        timelock="{timelock}",
        expand_trials=_META.get("expand_trials", False),
    log:
        "logs/sub-{subject}/epoch_{timelock}.log",
    script:
        "scripts/epoch.py"


# --- ERP Analysis Layer (US-010) ---
# Per-subject condition averages (erp_subject) feed the two group rules;
# the split keeps per-subject QC artifacts independent of group
# recomputation. All math lives in p0ly_utils.analysis (DoD: no algorithm
# logic in rule scripts); cluster permutation contrasts are omitted from
# the DAG at parse time for cohorts with < 2 subjects.
rule erp_subject:
    """Average one subject's epochs for one (timelock, condition) pair.

    Reads the US-017 ``sub-{subject}_{timelock}_desc-epo.fif.gz`` epochs
    (carrying trial metadata) and selects the condition via its
    ``metadata.eval`` query from ``config.yaml
    group_aggregation.condition_splits``; the reserved ``all_trials``
    condition applies no query. ``p0ly_utils.analysis.average_epochs``
    performs selection + averaging and fails loud on zero epochs or zero
    query matches (US-024 philosophy). The output keeps every channel
    (per-subject QC artifact).
    """
    conda:
        "envs/snakemake.yaml"
    input:
        epochs=f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_{{timelock}}_desc-epo.fif.gz",
    output:
        ave=_ERP_AVE_OUT,
    params:
        condition_query=lambda wildcards: _ERP_QUERIES[wildcards.condition],
    log:
        "logs/sub-{subject}/erp_subject_{timelock}_{condition}.log",
    script:
        "scripts/erp_subject.py"


rule erp_group_average:
    """Equal-weight grand average across subjects for one (timelock, condition).

    Consumes the per-subject ``desc-ave`` files (rule erp_subject) and writes
    ``group_analysis/{timelock}/{condition}_desc-ave.fif.gz`` (flat
    per-timelock layout; US-015 will slot the ``{cohort}`` wildcard in
    between). ``p0ly_utils.analysis.grand_average`` equal-weights every
    subject regardless of trial counts.
    """
    conda:
        "envs/snakemake.yaml"
    input:
        subject_averages=lambda wildcards: expand(
            _ERP_AVE_OUT,
            subject=config["subjects"],
            timelock=wildcards.timelock,
            condition=wildcards.condition,
        ),
    output:
        ave=_ERP_GROUP_AVE_OUT,
    log:
        "logs/group/erp_group_average_{timelock}_{condition}.log",
    script:
        "scripts/erp_group_average.py"


rule run_erp:
    """Cluster permutation contrast across subjects for one timelock (PRD stage 5).

    Inputs are the per-subject condition evokeds (rule erp_subject) for both
    contrast arms. ``p0ly_utils.analysis.group_erp`` builds the per-subject
    difference waves (cond_first - cond_second), picks EEG-only channels so
    they align with the montage-derived channel adjacency, and runs the
    one-sample cluster permutation test against zero with ``config.yaml erp``
    statistics settings; it fails loud on < 2 subjects (the DAG omits
    contrast targets for smaller cohorts — see _ERP_CONTRASTS_ENABLED, so
    this guard only trips on forced/stale rule runs).

    Outputs (flat per-timelock under group_analysis/, one job writes both):
      - {cond_first}-vs-{cond_second}_clusterperm.npz : t_obs
        (n_channels, n_times), per-cluster p-values, sign-flip null maxima
        (h0; length = unique permutations actually used) + settings echo.
      - .csv : one row per detected cluster — index arrays are pixel-wise
        (values repeat), so n_channels/n_times count distinct values and
        n_pixels the total mass; header-only when no cluster formed.
    """
    conda:
        "envs/snakemake.yaml"
    input:
        cond_first=lambda wildcards: expand(
            _ERP_AVE_OUT,
            subject=config["subjects"],
            timelock=wildcards.timelock,
            condition=_ERP_CONTRASTS[wildcards.contrast][0],
        ),
        cond_second=lambda wildcards: expand(
            _ERP_AVE_OUT,
            subject=config["subjects"],
            timelock=wildcards.timelock,
            condition=_ERP_CONTRASTS[wildcards.contrast][1],
        ),
    output:
        npz=_ERP_CONTRAST_NPZ_OUT,
        csv=_ERP_CONTRAST_CSV_OUT,
    params:
        conditions=lambda wildcards: _ERP_CONTRASTS[wildcards.contrast],
        stats=_ERP_STATS,
    log:
        "logs/group/run_erp_{timelock}_{contrast}.log",
    script:
        "scripts/erp.py"


# --- PSD Analysis Layer (US-011) ---
# Welch spectra per (subject, timelock, condition) feed two group rules; the
# split mirrors the ERP layer (ADR-007): per-subject QC artifacts, group
# averages, and per-condition parameterization. All math lives in
# p0ly_utils.analysis (DoD: no algorithm logic in rule scripts); single-subject
# cohorts run everything (no statistics in this module).
rule psd_subject:
    """Welch spectrum of one subject's epochs for one (timelock, condition).

    Reads the US-017 ``sub-{subject}_{timelock}_desc-epo.fif.gz`` epochs
    (carrying trial metadata), selects the condition via its ``metadata.eval``
    query from ``config.yaml group_aggregation.condition_splits`` (the
    reserved ``all_trials`` condition applies no query), and computes the
    Welch spectrum with ``config.yaml psd`` settings.
    ``p0ly_utils.analysis.psd_by_condition`` fails loud on zero query matches
    (US-024 philosophy). The spectrum keeps every channel (per-subject QC
    artifact) and is written as MNE Spectrum HDF5 (h5io — Spectrum.save's
    native container; not FIF).
    """
    conda:
        "envs/snakemake.yaml"
    input:
        epochs=f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_{{timelock}}_desc-epo.fif.gz",
    output:
        psd=_PSD_SUBJECT_OUT,
    params:
        condition="{condition}",
        condition_query=lambda wildcards: _PSD_QUERIES[wildcards.condition],
        psd=_PSD_SETTINGS,
    log:
        "logs/sub-{subject}/psd_subject_{timelock}_{condition}.log",
    script:
        "scripts/psd_subject.py"


rule psd_group_average:
    """Equal-weight grand-average spectrum across subjects (timelock, condition).

    Consumes the per-subject ``desc-psd`` files (rule psd_subject) and writes
    ``group_analysis/{timelock}/{condition}_desc-psd_ave.h5`` (MNE Spectrum
    HDF5) via ``p0ly_utils.analysis.group_psd`` (frequency-grid + channel-set
    guards).
    """
    conda:
        "envs/snakemake.yaml"
    input:
        subject_psds=lambda wildcards: expand(
            _PSD_SUBJECT_OUT,
            subject=config["subjects"],
            timelock=wildcards.timelock,
            condition=wildcards.condition,
        ),
    output:
        ave=_PSD_GROUP_OUT,
    log:
        "logs/group/psd_group_average_{timelock}_{condition}.log",
    script:
        "scripts/psd_group_average.py"


rule run_psd:
    """Aperiodic parameterization + band powers for one (timelock, condition).

    Fits specparam (fixed mode, library defaults) to every subject's
    per-condition spectrum and to the grand-average spectrum, and computes
    absolute/relative band power per channel from ``config.yaml psd`` (bands
    + norm_range). Outputs (flat per-timelock, one job writes both):
      - {condition}_desc-psd_params.csv : one row per (subject, channel) plus
        a ``subject == 'group_average'`` row fit on the grand-average spectrum
        — columns offset, exponent, knee_frequency (empty in fixed mode),
        r_squared, error_mae, n_peaks, and peak_centers/peak_powers/
        peak_widths (space-separated lists).
      - {condition}_desc-psd_bandpower.csv : one row per (subject, channel,
        band) — absolute (V^2/Hz mean density) and relative (fraction of the
        norm_range mass) power.
    """
    conda:
        "envs/snakemake.yaml"
    input:
        subject_psds=lambda wildcards: expand(
            _PSD_SUBJECT_OUT,
            subject=config["subjects"],
            timelock=wildcards.timelock,
            condition=wildcards.condition,
        ),
        group_average=_PSD_GROUP_OUT,
    output:
        params=_PSD_PARAMS_OUT,
        bandpower=_PSD_BANDPOWER_OUT,
    params:
        condition="{condition}",
        bands=_PSD_SETTINGS.get("bands", {}),
        norm_range=_PSD_SETTINGS.get("norm_range"),
    log:
        "logs/group/run_psd_{timelock}_{condition}.log",
    script:
        "scripts/run_psd.py"


# --- TFR Analysis Layer (US-012) ---
# Complex Morlet/multitaper transforms per (subject, timelock, condition) —
# reduced in-memory to a two-entry [power, ITPC] HDF5 — feed two group
# rules; the split mirrors the ERP/PSD layers (ADR-007): per-subject QC
# artifacts, group averages, per-contrast difference maps. All math lives
# in p0ly_utils.analysis (DoD: no algorithm logic in rule scripts);
# single-subject cohorts run everything (difference is defined at n=1).
rule tfr_subject:
    """Complex TFR -> [power, ITPC] for one subject's (timelock, condition).

    Reads the US-017 ``sub-{subject}_{timelock}_desc-epo.fif.gz`` epochs
    (carrying trial metadata), selects the condition via its ``metadata.eval``
    query from ``config.yaml group_aggregation.condition_splits`` (the
    reserved ``all_trials`` condition applies no query), and computes the
    single-trial complex TFR with ``config.yaml tfr`` settings — one
    convolution (``p0ly_utils.analysis.tfr_epochs``) reduced immediately to
    epoch-mean power (:func:`average_power`) and ITPC (:func:`itpc`); the
    large complex transient never touches disk. Fails loud on zero query
    matches (US-024 philosophy). The result keeps every channel (per-subject
    QC artifact) and is written as a two-entry AverageTFR HDF5 (h5io —
    write_tfrs/read_tfrs; positional convention [0]=power, [1]=ITPC).
    """
    conda:
        "envs/snakemake.yaml"
    input:
        epochs=f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_{{timelock}}_desc-epo.fif.gz",
    output:
        tfr=_TFR_SUBJECT_OUT,
    params:
        condition="{condition}",
        condition_query=lambda wildcards: _TFR_QUERIES[wildcards.condition],
        tfr=_TFR_SETTINGS,
    log:
        "logs/sub-{subject}/tfr_subject_{timelock}_{condition}.log",
    script:
        "scripts/tfr_subject.py"


rule tfr_group_average:
    """Equal-weight grand average of [power, ITPC] across subjects.

    Consumes the per-subject ``desc-tfr`` files (rule tfr_subject) and writes
    ``group_analysis/{timelock}/{condition}_desc-tfr_ave.h5`` (two-entry
    AverageTFR HDF5) via ``p0ly_utils.analysis.group_tfr`` (mne.grand_average
    with frequency-grid + channel-set guards), independently for the power
    and ITPC entries.
    """
    conda:
        "envs/snakemake.yaml"
    input:
        subject_tfrs=lambda wildcards: expand(
            _TFR_SUBJECT_OUT,
            subject=config["subjects"],
            timelock=wildcards.timelock,
            condition=wildcards.condition,
        ),
    output:
        ave=_TFR_GROUP_OUT,
    log:
        "logs/group/tfr_group_average_{timelock}_{condition}.log",
    script:
        "scripts/tfr_group_average.py"


rule run_tfr:
    """Difference map (cond_first - cond_second) for one timelock contrast.

    Inputs are the two group-average ``desc-tfr_ave.h5`` files (rule
    tfr_group_average — two reads, not 2 x N subject re-reads). Each file's
    [power, ITPC] entries are subtracted element-wise with
    ``p0ly_utils.analysis.tfr_difference`` (grid + channel guards) and
    written as a two-entry ``{condA}-vs-{condB}_desc-tfrdiff.h5``. No
    statistical test: subtraction is defined at n=1 (a single-subject
    difference is honest — group averages of one subject). Cluster
    permutation over (channel x freq x time) is a documented US-015
    deferred alternative.
    """
    conda:
        "envs/snakemake.yaml"
    input:
        cond_first=lambda wildcards: expand(
            _TFR_GROUP_OUT,
            timelock=wildcards.timelock,
            condition=_ERP_CONTRASTS[wildcards.contrast][0],
        ),
        cond_second=lambda wildcards: expand(
            _TFR_GROUP_OUT,
            timelock=wildcards.timelock,
            condition=_ERP_CONTRASTS[wildcards.contrast][1],
        ),
    output:
        diff=_TFR_DIFF_OUT,
    params:
        conditions=lambda wildcards: _ERP_CONTRASTS[wildcards.contrast],
    log:
        "logs/group/run_tfr_{timelock}_{contrast}.log",
    script:
        "scripts/run_tfr.py"


rule connectivity_subject:
    """Per-method spectral connectivity for one subject's (timelock, condition).

    Reads the US-017 ``sub-{subject}_{timelock}_desc-epo.fif.gz`` epochs
    (carrying trial metadata), selects the condition via its ``metadata.eval``
    query from ``config.yaml group_aggregation.condition_splits`` (the
    reserved ``all_trials`` condition applies no query), and computes one
    ``mne_connectivity.spectral_connectivity_epochs`` call across all
    configured methods with ``config.yaml connectivity`` settings. The result
    keeps every channel (per-subject QC artifact) and is written as an ``.npz``
    archive — one ``(n_channels, n_channels, n_freqs)`` adjacency per method
    (symmetric, zero diagonal) plus ``ch_names`` and ``freqs``.
    """
    conda:
        "envs/snakemake.yaml"
    input:
        epochs=f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_{{timelock}}_desc-epo.fif.gz",
    output:
        conn=_CONN_SUBJECT_OUT,
    params:
        condition="{condition}",
        condition_query=lambda wildcards: _CONN_QUERIES[wildcards.condition],
        connectivity=_CONN_SETTINGS,
    log:
        "logs/sub-{subject}/connectivity_subject_{timelock}_{condition}.log",
    script:
        "scripts/connectivity_subject.py"


rule connectivity_group_average:
    """Equal-weight grand average of per-method adjacencies across subjects.

    Consumes the per-subject ``desc-conn.npz`` archives (rule
    connectivity_subject) and writes
    ``group_analysis/{timelock}/{condition}_desc-conn_ave.npz`` (same archive
    layout) via ``p0ly_utils.analysis.group_connectivity`` (equal-weight mean
    with channel-set + method + frequency-grid guards).
    """
    conda:
        "envs/snakemake.yaml"
    input:
        subject_conns=lambda wildcards: expand(
            _CONN_SUBJECT_OUT,
            subject=config["subjects"],
            timelock=wildcards.timelock,
            condition=wildcards.condition,
        ),
    output:
        ave=_CONN_GROUP_OUT,
    params:
        methods=lambda wildcards: _CONN_SETTINGS["methods"],
    log:
        "logs/group/connectivity_group_average_{timelock}_{condition}.log",
    script:
        "scripts/connectivity_group_average.py"


rule run_connectivity:
    """Graph metrics of the band-averaged group connectivity (timelock, condition).

    Input is the grand-average ``desc-conn_ave.npz`` (rule
    connectivity_group_average — one read, not N subject re-reads). Each
    method's adjacency is band-averaged (``config.yaml connectivity.bands``,
    inclusive windows) and thresholded (``min_edge_weight`` noise floor), and
    ``p0ly_utils.analysis.graph_metrics`` reports weighted clustering, the
    characteristic path length (largest connected component, effective
    distance ``1/weight``) and strength centrality as one long-format CSV
    ``(method, band, node)``. No statistical test: defined at n=1, mirroring
    PSD/TFR. Per-contrast difference *graphs* are a documented deferral —
    difference adjacencies compound sign flips of near-zero couplings.
    """
    conda:
        "envs/snakemake.yaml"
    input:
        ave=_CONN_GROUP_OUT,
    output:
        graph=_CONN_GRAPH_OUT,
    params:
        methods=lambda wildcards: _CONN_SETTINGS["methods"],
        bands=lambda wildcards: _CONN_SETTINGS["bands"],
        min_edge_weight=lambda wildcards: _CONN_SETTINGS["min_edge_weight"],
    log:
        "logs/group/run_connectivity_{timelock}_{condition}.log",
    script:
        "scripts/run_connectivity.py"
