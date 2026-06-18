# p0ly-flow Snakemake DAG
# Ingestion layer — US-007

# --- Config ---
configfile: "config.yaml"

# --- Config-derived path roots (no hardcoded directories in rules) ---
_DATA_DIR = config["project_settings"]["data_directory"].rstrip("/")
_OUT_DIR = config["project_settings"]["output_directory"].rstrip("/")
_TASK = config["project_settings"]["task"]
_FMT = config["project_settings"]["input_format"]

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
        # US-008 will re-add the metadata target once inject_metadata is wired.


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


# --- Metadata Layer (placeholder — US-008) ---
rule inject_metadata:
    """Inject trial metadata. Implementation placeholder (US-008)."""
    conda:
        "envs/snakemake.yaml"
    input:
        raw=f"{_OUT_DIR}/sub-{{subject}}/sub-{{subject}}_desc-raw.fif",
    output:
        f"{_OUT_DIR}/sub-{{subject}}/metadata.tsv",
    params:
        parser=config["metadata"]["custom_parser_script"],
    log:
        "logs/sub-{subject}/inject_metadata.log",
    script:
        "scripts/parse_metadata.py"
