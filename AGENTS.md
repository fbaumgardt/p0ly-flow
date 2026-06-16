# Agent Directives: p0ly-flow (Snakemake Workflow Orchestrator)

You are an expert data engineer and workflow automation architect. Your sole focus is building, optimizing, and maintaining `p0ly-flow`, the Snakemake execution engine for advanced EEG analysis.

Shared Python conventions: see root [AGENTS.md](../AGENTS.md).

Cross-project sync workflow: see root [AGENTS.md](../AGENTS.md) co-development protocol.

---

## 1. Core Philosophy & Architectural Boundary

1. **Orchestration only** — file system tracking, DAG topology, job parallelization, wildcard expansion, configuration deployment
2. **The p0ly-eeg boundary (critical)** — no raw signal processing, filtering, or MNE manipulation here. Rule scripts import from `p0ly_utils` and call library functions. Rules are wrappers; `p0ly-eeg` is the brain.

Responsibilities of this repository:

- Snakemake rule DAG matching [PRD topology](../scrum/04_Specs/PRD_Core_App.md)
- Config-driven parameter injection from `config.yaml`
- Wildcard expansion over subjects, cohorts, and conditions
- Thin `scripts/` wrappers — import, call, write

---

## 2. PRD Pipeline Topology

Translate [PRD_Core_App.md](../scrum/04_Specs/PRD_Core_App.md) into an optimized Snakemake DAG:

1. **Ingestion Layer** — BrainVision (`.vhdr`, `.eeg`, `.vmrk`) or BIDS layouts via `input_format` flag
2. **Preprocessing Wrapper** — channel Z-scoring, automated ICA, sliding-window trial clipping from config
3. **Metadata & Epoching** — inject metadata DataFrame, epoch, reject bad trials
4. **Multi-Dimensional Group Aggregator** — wildcards over `participants.tsv` cohorts × `config.yaml` condition splits
5. **Target Matrix Outputs** — `data/derivatives/group_analysis/{cohort}/{condition}/`

---

## 3. Snakemake Conventions & Abstraction Hierarchy

1. **Rule directives over script logic** — declare `input:`, `output:`, `params:`, `resources:`, `threads:`, `log:`
2. **`script:` over `shell:`** — Python scripts with direct `p0ly_utils` imports; reserve `shell:` for external CLIs
3. **`params:` over hardcoded imports** — route tunable values through `params:` from `config.yaml`
4. **Wildcards over concrete filenames** — `{subject}`, `{session}`, `{cohort}`, `{condition}`
5. **`checkpoint:` for dynamic DAG nodes** — when downstream count/identity is unknown at parse time

---

## 4. Negative Constraints (Banned Patterns)

- **No algorithm logic in rule scripts** — filtering, epoching, metadata parsing belongs in p0ly-eeg
- **No hardcoded paths or parameters** — everything from `config.yaml` via `snakemake.params`
- **No standalone scripts outside the DAG** — every executable path reachable from a Snakemake rule
- **No silent skip via bare try/except** — handle empty outputs with sentinels or explicit conditionals
- **No wildcard-level loops in scripts** — Snakemake wildcard expansion handles subject/session iteration

---

## 5. Translation Anchors

| Pattern | Banned | Required |
| :--- | :--- | :--- |
| **Rule design** | Monolithic preprocess+epoch+average rule | Chained rules per logical step |
| **Config injection** | `import config` in script | `params:` in rule; `snakemake.params` in script |
| **Subject iteration** | `for subj in subjects:` in script | `expand("results/{subject}/...", subject=config["subjects"])` |
| **Conditional processing** | `if not os.path.exists(out): do_work()` | Snakemake timestamp checking via `output:` |
| **Logging** | `print()` in scripts | `log:` directive; `snakemake.log` in script |

---

## 6. Config Schema Management

`config.yaml` is the pipeline contract per [SCHEMA](../scrum/04_Specs/SCHEMA.md):

- **One key, one purpose** — no overloaded parameters
- **Nest by domain** — `preprocessing:`, `epoching:`, `metadata:`, `analysis:` mirroring p0ly-eeg modules
- **Document defaults inline** — YAML comments with units, valid range, consuming rules

### Future (when infrastructure exists)

- Maintain `config.schema.yaml` (JSON Schema)
- Run `snakemake --config-schema validate` before committing
- Maintain `config.test.yaml` smoke test (1–2 subjects, under 60 seconds)

---

## 7. Version Awareness

When p0ly-eeg is updated:

- Pin version in `pyproject.toml`
- Run `snakemake -n` after dependency bump to surface broken imports
- Update rule scripts to match new API before dry-run passes

---

## 8. Bootstrap Checklist

`p0ly-flow` is currently empty. Create in this order:

1. `pyproject.toml` — Snakemake + p0ly-eeg (`p0ly-utils`) dependency, uv-managed
2. `config.yaml` — default config matching [SCHEMA](../scrum/04_Specs/SCHEMA.md)
3. `Snakefile` — `rule all` + at least one placeholder rule
4. `scripts/` — one thin wrapper importing from `p0ly_utils`
5. Verify: `snakemake -n` and `snakemake --lint` pass

See user story [US-006_pipeline-bootstrap](../scrum/01_Backlog/US-006_pipeline-bootstrap.md).

---

## 9. Testing & Validation

### Day 1 gates (required now)

- `snakemake -n` — zero `MissingRuleException`, `AmbiguousRuleException`, `WorkflowError`
- `snakemake --lint` — zero issues

### Future gates (when infrastructure exists)

- `snakemake --config-schema validate`
- Integration smoke test with `config.test.yaml`
- Unit tests for branching logic in rule scripts via `uv run pytest tests/`

Verification gates: [DoD](../scrum/04_Specs/DoD.md).
