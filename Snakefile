# p0ly-flow Snakemake DAG
# Ingestion layer — US-007

# --- Config ---
configfile: "config.yaml"

# --- Config-derived path roots (no hardcoded directories in rules) ---
_DATA_DIR = config["project_settings"]["data_directory"].rstrip("/")
_OUT_DIR = config["project_settings"]["output_directory"].rstrip("/")
_TASK = config["project_settings"]["task"]
_FMT = config["project_settings"]["input_format"]

# Preprocessing config (US-008). All keys optional; ica_strategy present =>
# the preprocess rule also emits a fitted-ICA sidecar (see _ICA_OUT below).
_PP = config["preprocessing"]
_ICA_ENABLED = _PP.get("ica_strategy") is not None

# Metadata config (US-016). The experiment spec drives trial/Block/Onset
# extraction; csv_columns and expand_trials are optional companions.
_META = config["metadata"]

# US-017: the timelock set is derived from the experiment spec itself
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

# --- Wildcard Constraints ---
wildcard_constraints:
    subject = r"\d+",
    timelock = r"[a-z]+"


# --- Ingestion input resolver ---
#
# Returns the concrete source file(s) Snakemake must see at DAG-parse time so
# the dry-run resolves for every supported input_format. The actual reading is
# done at runtime by scripts/ingest_raw.py via p0ly_utils.io.load_raw; these
# paths exist purely for DAG resolution.
#
# BrainVision: the .vhdr is the entry point (.eeg/.vmrk are implicit siblings).
# BIDS:        the recording resolved from the BIDS convention under the root.
def _ingest_inputs(subject: str) -> str | list[str]:
    if _FMT == "BrainVision":
        return f"{_DATA_DIR}/sub-{subject}/sub-{subject}_task-{_TASK}.vhdr"
    if _FMT == "BIDS":
        # BIDS EEG recording basename: sub-{subject}_task-{task}_eeg.<ext>
        # mne-bids picks the concrete extension at runtime; for DAG resolution
        # we point at the .vhdr sidecar that the fixture / a BrainVision-based
        # BIDS dataset writes. EDF-based BIDS datasets would use .edf here.
        return f"{_DATA_DIR}/sub-{subject}/eeg/sub-{subject}_task-{_TASK}_eeg.vhdr"
    raise ValueError(f"Unsupported input_format {_FMT!r} (expected 'BrainVision' or 'BIDS').")


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


# --- Ingestion Layer (US-007) ---
rule raw_ingestion:
    """Ingest raw EEG per input_format via p0ly_utils.io.load_raw.

    Output follows BIDS-style naming: sub-{subject}_desc-raw.fif.gz
    """
    conda:
        "envs/snakemake.yaml"
    input:
        paths=lambda wildcards: _ingest_inputs(wildcards.subject),
    output:
        f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_desc-raw.fif.gz",
    params:
        fmt=_FMT,
        subject="{subject}",
        task=_TASK,
        montage=config["project_settings"]["montage"],
        data_dir=_DATA_DIR,
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

    Cuts ``mne.Epochs`` from the timelock's annotation events using the spec's
    ``intervals[timelock]`` -> ``(tmin, tmax)`` and the shared ``baseline``
    (``config.yaml`` ``epoching.baseline``), then aligns the US-016 by-trial
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

    The timelock set comes from the experiment spec (``_TIMELOCKS`` above), not
    config literals; per-timelock ``(tmin, tmax)`` come from the spec, not
    config. No segmentation/alignment math here -- algorithms live in p0ly-eeg.
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
        timelock="{timelock}",
        expand_trials=_META.get("expand_trials", False),
    log:
        "logs/sub-{subject}/epoch_{timelock}.log",
    script:
        "scripts/epoch.py"
