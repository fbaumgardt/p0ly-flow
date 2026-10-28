"""Write one subject's within-subject decoding scores (US-030).

Pure I/O shim per p0ly-flow/AGENTS.md: loads the US-017 timelock epochs
(``sub-{subject}_{timelock}_desc-epo.fif.gz``, carrying the aligned trial
metadata) and lets ``p0ly_utils.analysis.decode_epochs`` run the whole
within-subject cross-validated decoding of one categorical metadata target
(``config.yaml decoding`` settings passed via ``params:``). No label parsing,
estimator construction, CV, or scoring logic lives here. Fails loud on invalid
targets, missing labels, or classes with fewer than ``n_splits`` trials (the
library raises before fitting).

Output is a single ``.npz`` archive (no pickled objects):
``scores`` + ``fold_scores`` + ``times`` (plus ``train_times``/``test_times``
in temporal-generalization mode, equal to ``times`` in this story) and the
scalar configuration ``target``, ``classes``, ``class_counts``, ``scoring``,
``chance_level``, ``mode``, ``n_splits``, ``n_epochs``, ``seed`` (NaN when
null), ``estimator``.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import mne
import numpy as np
from p0ly_utils.analysis import decode_epochs

p = snakemake.params  # type: ignore[name-defined]

epochs = mne.read_epochs(snakemake.input.epochs, preload=True)  # type: ignore[name-defined]
result = decode_epochs(
    epochs,
    target=str(p.target),
    mode=str(p.mode),
    estimator=str(p.estimator),
    estimator_params=p.estimator_params,
    n_splits=int(p.n_splits),
    scoring=str(p.scoring),
    seed=None if p.seed is None else int(p.seed),
    n_jobs=int(p.n_jobs),
)

archive = {
    "scores": result.scores,
    "fold_scores": result.fold_scores,
    "times": result.times,
    "target": np.asarray(result.target),
    "classes": np.asarray(result.classes),
    "class_counts": result.class_counts,
    "scoring": np.asarray(result.scoring),
    "chance_level": np.asarray(result.chance_level),
    "mode": np.asarray(result.mode),
    "n_splits": np.asarray(result.n_splits),
    "n_epochs": np.asarray(result.n_epochs),
    "seed": np.asarray(np.nan if result.seed is None else result.seed),
    "estimator": np.asarray(p.estimator),
}
if result.mode == "temporal_generalization":
    # Persisted separately even though train and test share the epoch grid.
    archive["train_times"] = result.times
    archive["test_times"] = result.times

np.savez_compressed(str(snakemake.output.decode), **archive)  # type: ignore[name-defined]
