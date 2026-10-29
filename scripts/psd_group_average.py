"""Write the cross-subject grand-average spectrum for a timelock x condition
(US-011).

Pure I/O shim per p0ly-flow/AGENTS.md: reads every subject's per-condition
spectrum file listed by the rule (Snakemake expands the subject set — no
Python subject loop here) and calls ``p0ly_eeg.analysis.group_psd`` for the
equal-weight cross-subject mean (frequency-grid + channel-set guards),
writing ``group_analysis/{timelock}/{condition}_desc-psd_ave.h5``.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

from mne.time_frequency import read_spectrum
from p0ly_eeg.analysis import group_psd

spectra = [read_spectrum(path) for path in snakemake.input.subject_psds]  # type: ignore[name-defined]
average = group_psd(spectra)
average.save(snakemake.output.ave, overwrite=True)  # type: ignore[name-defined]
