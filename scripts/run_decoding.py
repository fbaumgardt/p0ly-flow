"""Equal-subject-weight cohort mean of the per-subject decoding scores (US-030).

Pure I/O shim per p0ly-flow/AGENTS.md: reads the per-subject ``desc-decode.npz``
archives listed by the rule (Snakemake expands the cohort subject set — no
Python subject loop here), reconstructs ``p0ly_utils.analysis.DecodingResult``
objects, and lets ``p0ly_utils.analysis.group_decoding`` validate the shared
configuration (target, mode, scoring, class order, chance level, time grid,
score shape) and average the subject-level scores with equal subject weights.
Trials are never pooled across subjects and folds are not treated as subjects;
a single-subject cohort passes through unchanged. Writes
``group_analysis/{timelock}/{cohort}/{target}_desc-decode_ave.npz``.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import numpy as np
from p0ly_utils.analysis import DecodingResult, group_decoding


def _read(path: str) -> DecodingResult:
    """Reload one subject archive (scalars stored as 0-d arrays)."""
    with np.load(path) as archive:
        seed = float(archive["seed"])
        return DecodingResult(
            scores=np.asarray(archive["scores"]),
            fold_scores=np.asarray(archive["fold_scores"]),
            times=np.asarray(archive["times"]),
            target=str(archive["target"]),
            classes=tuple(str(label) for label in archive["classes"]),
            scoring=str(archive["scoring"]),
            chance_level=float(archive["chance_level"]),
            mode=str(archive["mode"]),
            n_splits=int(archive["n_splits"]),
            seed=None if np.isnan(seed) else int(seed),
            n_epochs=int(archive["n_epochs"]),
            class_counts=np.asarray(archive["class_counts"], dtype=np.int64),
        )


group = group_decoding([_read(str(path)) for path in snakemake.input.subject_decodes])  # type: ignore[name-defined]

archive = {
    "scores": group.scores,
    "times": group.times,
    "target": np.asarray(group.target),
    "classes": np.asarray(group.classes),
    "scoring": np.asarray(group.scoring),
    "chance_level": np.asarray(group.chance_level),
    "mode": np.asarray(group.mode),
    "n_subjects": np.asarray(group.n_subjects),
}
if group.mode == "temporal_generalization":
    archive["train_times"] = group.times
    archive["test_times"] = group.times

np.savez_compressed(str(snakemake.output.ave), **archive)  # type: ignore[name-defined]
