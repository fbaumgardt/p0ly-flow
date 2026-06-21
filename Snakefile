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
    subject = r"\d+"


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
            f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_desc-raw.fif",
            subject=config["subjects"],
        ),
        expand(
            f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_desc-clean-raw.fif.gz",
            subject=config["subjects"],
        ),
        # ICA sidecar target only when ICA is enabled in config (US-008).
        _ICA_TARGETS,
        # US-016 will re-add the metadata target once inject_metadata is wired.


# --- Ingestion Layer (US-007) ---
rule raw_ingestion:
    """Ingest raw EEG per input_format via p0ly_utils.io.load_raw.

    Output follows BIDS-style naming: sub-{subject}_desc-raw.fif
    """
    conda:
        "envs/snakemake.yaml"
    input:
        paths=lambda wildcards: _ingest_inputs(wildcards.subject),
    output:
        f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_desc-raw.fif",
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
        raw=f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_desc-raw.fif",
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


# --- Metadata Layer (placeholder — US-016) ---
rule inject_metadata:
    """Inject trial metadata. Implementation placeholder (US-016)."""
    conda:
        "envs/snakemake.yaml"
    input:
        raw=f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_desc-clean-raw.fif.gz",
    output:
        f"{_OUT_DIR}/sub-{{subject}}/metadata.tsv",
    params:
        parser=config["metadata"]["custom_parser_script"],
    log:
        "logs/sub-{subject}/inject_metadata.log",
    script:
        "scripts/parse_metadata.py"
