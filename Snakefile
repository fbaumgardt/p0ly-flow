# p0ly-flow Snakemake DAG
# Bootstrap skeleton — US-006

# --- Config ---
configfile: "config.yaml"

# --- Wildcard Constraints ---
wildcard_constraints:
    subject = r"\d+"

# --- Target Rule ---
rule all:
    input:
        expand(
            "data/derivatives/sub-{subject}/metadata.tsv",
            subject=config["subjects"],
        ),


# --- Ingestion Layer (placeholder — US-007) ---
rule raw_ingestion:
    """Ingest raw EEG per input_format. Placeholder — wired in US-007."""
    conda:
        "envs/snakemake.yaml"
    input:
        vhdr=lambda wildcards: f"data/raw/sub-{wildcards.subject}/sub-{wildcards.subject}.vhdr"
        if config["project_settings"]["input_format"] == "BrainVision"
        else [],
    output:
        "data/derivatives/sub-{subject}/sub-{subject}_desc-raw.fif",
    params:
        input_format=config["project_settings"]["input_format"],
        data_dir=config["project_settings"]["data_directory"],
    log:
        "logs/sub-{subject}/raw_ingestion.log",
    script:
        "scripts/ingest_raw.py"


# --- Metadata Layer (placeholder — US-008) ---
rule inject_metadata:
    """Inject trial metadata. Implementation placeholder."""
    conda:
        "envs/snakemake.yaml"
    input:
        raw="data/derivatives/sub-{subject}/sub-{subject}_desc-raw.fif",
    output:
        "data/derivatives/sub-{subject}/metadata.tsv",
    params:
        parser=config["metadata"]["custom_parser_script"],
    log:
        "logs/sub-{subject}/inject_metadata.log",
    script:
        "scripts/parse_metadata.py"
