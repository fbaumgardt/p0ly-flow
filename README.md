# p0ly-flow

Snakemake orchestration pipeline for EEG analysis, powered by [p0ly-eeg](../p0ly-eeg) (`p0ly_utils`). Rule scripts are thin wrappers that import library functions — all signal processing lives in the library.

## Pipeline

```text
raw data (BrainVision or BIDS)
  → manifest-driven ingestion (segments merged per subject)
  → preprocessing (bad channels, ICA, sliding-window rejection)
  → metadata injection + epoching (per timelock)
  → per-subject analyses
  → group aggregation (cohort × condition) + statistics
```

Cohorts expand from `data/metadata/participants.tsv`; conditions from `group_aggregation.condition_splits` queries (e.g. `Correct == True/False`) — every unordered condition pair becomes a contrast. Outputs land in `data/derivatives/group_analysis/{timelock}/{cohort}/{condition}/`.

## Main analyses

Enable in `config.yaml` under `analysis:`; parameters live in the matching `config.yaml` block.

| Analysis | Rules | Output |
| :--- | :--- | :--- |
| **ERP** | `erp_*`, `run_erp` | Evoked grand averages per condition, one-sample cluster-permutation contrasts |
| **PSD** | `psd_*`, `run_psd` | Welch spectra per condition, band powers, aperiodic (1/f) fits |
| **TFR** | `tfr_*`, `run_tfr`, `run_tfr_cluster` | Power and ITPC grand averages, TFR cluster-permutation |
| **Connectivity** | `connectivity_subject`, `connectivity_group_average`, `run_connectivity`, `connectivity_contrast` | Spectral connectivity (wPLI/coh/PLV) grand averages (plain or Fisher-z), band-averaged graph metrics, per-contrast difference graphs |

Statistics are defined per their group level: cluster-permutation rules need the configured subject cohorts; grand averages, difference graphs, PSD/TFR summaries are defined for any n.

## Usage

```bash
# 1. Configure: subjects + data paths + analysis toggles in config.yaml
#    (raw data under data/raw/sub-{id}/; participants.tsv lists cohorts)

# 2. Install (resolves p0ly-utils from the sibling p0ly-eeg via path source)
uv sync

# 3. Validate the DAG, then run
uv run snakemake -n
uv run snakemake --cores all           # or: --profile local

# Smoke test (2 synthetic subjects, < 60 s)
uv run snakemake --configfile config.test.yaml --cores all
```

Regenerate the ingestion manifest after adding recordings:

```bash
uv run python scripts/create_tsv.py          # refuses unknown-task recordings unless --exclude PATTERN
```

Tests for rule-script logic: `uv run pytest tests/`.

## See also

- [p0ly-eeg](../p0ly-eeg) — the analysis library
- [scrum/](../scrum/) — project management vault (specs, backlog, sprints)
