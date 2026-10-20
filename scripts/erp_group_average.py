"""Write the cross-subject grand average for a timelock x condition (US-010).

Pure I/O shim per p0ly-flow/AGENTS.md: reads every subject's per-condition
evoked file listed by the rule (Snakemake expands the subject set — no Python
subject loop here) and calls ``p0ly_utils.analysis.grand_average`` for the
equal-weight cross-subject mean (every subject contributes equally regardless
of trial count), writing ``group_analysis/{timelock}/{condition}_desc-ave.fif.gz``.
The group average keeps every channel; cluster permutation contrasts are
separate (rule run_erp / scripts/erp.py).

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

import mne
from p0ly_utils.analysis import grand_average

evokeds = [mne.read_evokeds(path)[0] for path in snakemake.input.subject_averages]  # type: ignore[name-defined]
average = grand_average(evokeds)
average.save(snakemake.output.ave, overwrite=True)  # type: ignore[name-defined]
