"""Cross-subject grand average of the two-entry [power, ITPC] TFR files
(US-012).

Pure I/O shim per p0ly-flow/AGENTS.md: reads every subject's per-condition
two-entry TFR file listed by the rule (Snakemake expands the subject set —
no Python subject loop here) and calls ``p0ly_eeg.analysis.group_tfr``
independently for the power and ITPC entries (equal-weight cross-subject
mean with frequency-grid + channel-set guards), writing
``group_analysis/{timelock}/{condition}_desc-tfr_ave.h5`` — positional
convention: entry [0] = power, entry [1] = ITPC.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

from mne.time_frequency import read_tfrs, write_tfrs
from p0ly_eeg.analysis import group_tfr


def _read_entries(path: str) -> tuple[object, object]:
    """Read a two-entry TFR file, verifying the [power, ITPC] convention."""
    entries = read_tfrs(path)
    if len(entries) != 2 or entries[0].comment != "power" or entries[1].comment != "itpc":
        raise RuntimeError(
            f"expected a two-entry [power, ITPC] TFR file in {path}, got "
            f"{len(entries)} entries with comments "
            f"{[e.comment for e in entries]}"
        )
    return entries[0], entries[1]


subject_tfrs = [_read_entries(str(path)) for path in snakemake.input.subject_tfrs]  # type: ignore[name-defined]
power = group_tfr([tfr[0] for tfr in subject_tfrs])
itpc = group_tfr([tfr[1] for tfr in subject_tfrs])
# grand_average concatenates source comments — restore the entry convention.
power.comment = "power"
itpc.comment = "itpc"
write_tfrs(snakemake.output.ave, [power, itpc], overwrite=True)  # type: ignore[name-defined]
