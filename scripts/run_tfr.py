"""Per-contrast difference TFR map, cond_first - cond_second (US-012).

Pure I/O shim per p0ly-flow/AGENTS.md: reads the two group-average two-entry
TFR files (rule tfr_group_average — two reads, not 2 x N subject re-reads)
and calls ``p0ly_eeg.analysis.tfr_difference`` for each entry, writing
``group_analysis/{timelock}/{condA}-vs-{condB}_desc-tfrdiff.h5`` —
positional convention: entry [0] = power difference, entry [1] = ITPC
difference. No statistical test lives here (US-012 spike 3: difference maps
only; cluster permutation is a documented US-015 deferred alternative).

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

from mne.time_frequency import read_tfrs, write_tfrs
from p0ly_eeg.analysis import tfr_difference

cond_first_entries = read_tfrs(str(snakemake.input.cond_first))  # type: ignore[name-defined]
cond_second_entries = read_tfrs(str(snakemake.input.cond_second))  # type: ignore[name-defined]
for entries in (cond_first_entries, cond_second_entries):
    if len(entries) != 2 or entries[0].comment != "power" or entries[1].comment != "itpc":
        raise RuntimeError(
            f"expected a two-entry [power, ITPC] TFR file, got "
            f"{len(entries)} entries with comments "
            f"{[e.comment for e in entries]}"
        )
power_diff = tfr_difference(cond_first_entries[0], cond_second_entries[0])
itpc_diff = tfr_difference(cond_first_entries[1], cond_second_entries[1])
# Normalize entry comments to the artifact convention (tfr_difference
# concatenates the operand comments otherwise).
power_diff.comment = "power"
itpc_diff.comment = "itpc"
write_tfrs(snakemake.output.diff, [power_diff, itpc_diff], overwrite=True)  # type: ignore[name-defined]
