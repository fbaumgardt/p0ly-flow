"""Aperiodic parameterization + band powers for a timelock x condition (US-011).

Pure I/O shim per p0ly-flow/AGENTS.md: reads every subject's per-condition
spectrum (rule psd_subject) plus the grand-average spectrum (rule
psd_group_average), then calls ``p0ly_eeg.analysis`` helpers —
``fit_aperiodic_channels`` (specparam fixed mode) and ``band_powers`` — and
writes the two flat CSVs. No math here: fitting, band masks, and
normalization live in the library.

Outputs:
  * ``{condition}_desc-psd_params.csv``: one row per (subject, channel) plus a
    ``subject == 'group_average'`` row fit on the grand-average spectrum.
  * ``{condition}_desc-psd_bandpower.csv``: one row per (subject, channel,
    band) — absolute (V²/Hz mean density) and relative (fraction of the
    norm_range mass) power.

Note: no `from __future__ import annotations` — Snakemake's `script:` directive
prepends a preamble before this file's body, and __future__ imports must be the
first statement (flagged during US-007).
"""

from pathlib import Path

import pandas as pd
from mne.time_frequency import Spectrum, read_spectrum
from p0ly_eeg.analysis import band_powers, fit_aperiodic_channels

p = snakemake.params
condition = str(p.condition)
bands = {name: (float(lo), float(hi)) for name, (lo, hi) in p.bands.items()}
# None (config without psd.norm_range) = normalize over the full Welch grid.
norm_range = (
    (float(p.norm_range[0]), float(p.norm_range[1])) if p.norm_range is not None else None
)

subject_spectra = [read_spectrum(path) for path in snakemake.input.subject_psds]  # type: ignore[name-defined]
group_spectrum = read_spectrum(snakemake.input.group_average)  # type: ignore[name-defined]
if not isinstance(group_spectrum, Spectrum):
    raise RuntimeError(f"expected a Spectrum in {snakemake.input.group_average}")  # type: ignore[name-defined]

# Fit range: the spectrum's own Welch window (fmin/fmax come from config).
fit_freq_range = (float(group_spectrum.freqs[0]), float(group_spectrum.freqs[-1]))


def _subject_label(path: str) -> str:
    """``.../sub-001/sub-001_{...}_desc-psd.fif.gz`` -> ``sub-001``."""
    return Path(path).name.split("_")[0]


def _fit_rows(label: str, spectrum: Spectrum) -> list[dict[str, object]]:
    fits = fit_aperiodic_channels(
        spectrum.data,
        spectrum.freqs,
        channel_names=spectrum.ch_names,
        freq_range=fit_freq_range,
    )
    return [
        {
            "subject": label,
            "channel": fit.channel_name,
            "fmin": fit.freq_range[0],
            "fmax": fit.freq_range[1],
            "offset": fit.offset,
            "exponent": fit.exponent,
            # Fixed mode fits no knee; column stays for future knee-capable
            # specparam algorithms (AperiodicFit keeps the field).
            "knee_frequency": fit.knee_frequency,
            "r_squared": fit.r_squared,
            "error_mae": fit.error_mae,
            "n_peaks": len(fit.peak_centers),
            "peak_centers": " ".join(f"{c:g}" for c in fit.peak_centers),
            "peak_powers": " ".join(f"{v:g}" for v in fit.peak_powers),
            "peak_widths": " ".join(f"{w:g}" for w in fit.peak_widths),
        }
        for fit in fits
    ]


def _band_rows(label: str, spectrum: Spectrum) -> list[dict[str, object]]:
    window = norm_range if norm_range is not None else (
        float(spectrum.freqs[0]),
        float(spectrum.freqs[-1]),
    )
    powers = band_powers(spectrum.data, spectrum.freqs, bands, window)
    rows: list[dict[str, object]] = []
    for name, (band_fmin, band_fmax) in bands.items():
        for ch_name, absolute, relative in zip(
            spectrum.ch_names,
            powers[name]["absolute"],
            powers[name]["relative"],
        ):
            rows.append(
                {
                    "subject": label,
                    "channel": ch_name,
                    "band": name,
                    "band_fmin": band_fmin,
                    "band_fmax": band_fmax,
                    "absolute": float(absolute),
                    "relative": float(relative),
                }
            )
    return rows


param_rows: list[dict[str, object]] = []
band_rows: list[dict[str, object]] = []
for path, spectrum in zip(snakemake.input.subject_psds, subject_spectra):  # type: ignore[name-defined]
    if not isinstance(spectrum, Spectrum):
        raise RuntimeError(f"expected a Spectrum in {path}")
    label = _subject_label(str(path))
    param_rows += _fit_rows(label, spectrum)
    band_rows += _band_rows(label, spectrum)
param_rows += _fit_rows("group_average", group_spectrum)
band_rows += _band_rows("group_average", group_spectrum)

pd.DataFrame(
    param_rows,
    columns=[
        "subject",
        "channel",
        "fmin",
        "fmax",
        "offset",
        "exponent",
        "knee_frequency",
        "r_squared",
        "error_mae",
        "n_peaks",
        "peak_centers",
        "peak_powers",
        "peak_widths",
    ],
).to_csv(snakemake.output.params, index=False)  # type: ignore[name-defined]

pd.DataFrame(
    band_rows,
    columns=[
        "subject",
        "channel",
        "band",
        "band_fmin",
        "band_fmax",
        "absolute",
        "relative",
    ],
).to_csv(snakemake.output.bandpower, index=False)  # type: ignore[name-defined]
