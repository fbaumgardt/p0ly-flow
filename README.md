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
| **Regression** | `regression_subject`, `run_regression` | Single-trial OLS beta maps per term (declared `regression.continuous` / `regression.categorical` metadata predictors) for voltage or TFR power, plus equal-subject-weight cohort means |
| **CFC** | `cfc_subject`, `cfc_group_average`, `run_cfc` | Within-channel PAC + n:m phase-phase coupling maps with full surrogate nulls per subject, equal-subject descriptive cohort means, subject-unit condition contrasts with full-map corrected p-values |
| **Variability** | `variability_subject`, `run_variability` | Across-trial maps per condition: voltage SD, power SD/Fano/CV; equal-subject-weight cohort archives with per-cell contributor counts |

Statistics are defined per their group level: cluster-permutation and CFC contrast rules need the configured subject cohorts (CFC contrasts are omitted loudly below 2 subjects — exact sign flips give an n=2 p-value floor of 1/3); grand averages, difference graphs, PSD/TFR summaries, and CFC descriptive means are defined for any n.

CFC artifacts (compressed `.npz`, `config.yaml cfc` block):

- `sub-{subject}/sub-{subject}_{timelock}_{condition}_desc-cfc.npz` — per method key (`pac`, `ppc_2x1`, ...) `__observed`, `__null` (the full surrogate distribution, retained on purpose), `__p_values`, `__valid_mask`; `evidence_level="subject"` (uncorrected subject-level evidence, not a cohort claim).
- `group_analysis/{timelock}/{cohort}/{condition}_desc-cfc_ave.npz` — per method `__mean` + `__valid_mask`; no averaged p-values (`evidence_level="cohort_descriptive"`).
- `group_analysis/{timelock}/{cohort}/{contrast}_cfcperm.npz` — per method `__difference`, `__pvalues_corrected`, `__null_max`, `__valid_mask` (`evidence_level="cohort_subject_unit"`).

Regression is explanatory within-subject OLS, not decoding or inference: one model per (subject, timelock) on all retained trials. Predictors are declared in `regression:` (`signal_domain: voltage | power`, `continuous: [...]`, `categorical: [...]` — at least one non-empty when `analysis.run_regression` is true); the power domain reuses the `tfr:` block for the transform even when `analysis.run_tfr` is false. There is no condition wildcard and no cohort-level statistic — cohort files are equal-subject-weight means of the per-subject beta maps.

Variability (`analysis.run_variability`) is selected per domain in `config.yaml variability:` — omit a domain to disable it (`voltage: {measures: [sd]}` only, power only, or both). The power domain reuses the `tfr:` settings independently of `analysis.run_tfr`, so power variability needs no TFR artifacts. Ratios are `NaN` where mean power is zero; use the `power__positive_mean` mask (subject files) and the `*__n_contributing` counts (group files, next to `n_subjects`) rather than reading `NaN` as zero.

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
