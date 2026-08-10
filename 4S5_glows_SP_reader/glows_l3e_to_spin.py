#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
glows_l3e_to_spin.py

Create daily IMAP-Lo-style spin-angle CSV files from GLOWS L3e survival
probability CDF files.

This script follows the structure of l1b_to_spin.py:
  - reads one combined IMAP-Lo good-times CSV
  - reads pointing_file.csv for spin-axis RA/DEC
  - reads share_pivot.csv for pivot angle
  - computes the sky direction for each 6-degree spin bin
  - writes one daily CSV per ESA step under outdir/pivot_<angle>/daily/

Main difference from l1b_to_spin.py:
  - instead of reading Lo L1B histogram counts, it reads GLOWS L3e
    survival probability, interpolates from the GLOWS energy grid to the
    seven IMAP-Lo ESA energies, rebins 1-degree spin bins to 6-degree bins,
    and writes the interpolated survival probability in place of counts.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import cdflib
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d


# -----------------------------------------------------------------------------
# IMAP-Lo ESA energies used for interpolation from the GLOWS energy grid.
# Units must match the units used in the GLOWS energy_grid variable.
# -----------------------------------------------------------------------------
LO_ENERGIES = np.array([
    0.01633,
    0.03047,
    0.05576,
    0.10626,
    0.20004,
    0.40496,
    0.78729,
], dtype=float)

NESA = 7
SPIN_BIN_DEG = 6
NSPIN_6DEG = 360 // SPIN_BIN_DEG
NSPIN_1DEG = 360


# -----------------------------------------------------------------------------
# Geometry routines copied from the l1b_to_spin.py workflow.
# -----------------------------------------------------------------------------
def radec2cart(ra: float, th: float) -> np.ndarray:
    x = np.cos(np.radians(ra)) * np.sin(np.radians(th))
    y = np.sin(np.radians(ra)) * np.sin(np.radians(th))
    z = np.cos(np.radians(th))
    return np.array([x, y, z])


def equatorial_to_ecliptic(alpha: float, delta: float) -> tuple[float, float]:
    """Convert equatorial RA/DEC to ecliptic longitude/latitude."""
    epsilon_0 = 23.43929111  # J2000 obliquity, degrees

    alpha_rad = np.radians(alpha)
    delta_rad = np.radians(delta)
    epsilon_rad = np.radians(epsilon_0)

    numerator = (
        np.sin(alpha_rad) * np.cos(epsilon_rad)
        + np.tan(delta_rad) * np.sin(epsilon_rad)
    )
    denominator = np.cos(alpha_rad)

    lambda_ecl_rad = np.arctan2(numerator, denominator)
    beta_ecl_rad = np.arcsin(
        np.sin(delta_rad) * np.cos(epsilon_rad)
        - np.cos(delta_rad) * np.sin(epsilon_rad) * np.sin(alpha_rad)
    )

    lambda_ecl = np.degrees(lambda_ecl_rad) % 360
    beta_ecl = np.degrees(beta_ecl_rad)

    return lambda_ecl, beta_ecl


def create_ra_dec(s_ra: float, s_dec: float, pivot_angle: float) -> tuple[list[float], list[float]]:
    """Create ecliptic longitude/latitude for the 60 6-degree bins."""
    spin_ra, spin_dec = s_ra, s_dec
    spin_th = 90.0 - spin_dec

    # Standard NEP direction in J2000, same convention as l1b_to_spin.py.
    nep_ra, nep_dec = 270, 66.56
    nep_th = 90.0 - nep_dec

    a_spine = np.radians(pivot_angle)

    def norm(v: np.ndarray) -> np.ndarray:
        return v / np.linalg.norm(v)

    e_nep = norm(radec2cart(nep_ra, nep_th))
    e_av_spin = norm(radec2cart(spin_ra, spin_th))

    e_perp_pole = e_nep - np.dot(e_nep, e_av_spin) * e_av_spin
    e_perp_pole = norm(e_perp_pole)

    e_perp_ram = np.cross(e_av_spin, e_perp_pole)
    e_perp_ram = norm(e_perp_ram)

    bin_edges = np.arange(0, 366, 6)
    bin_centers = 0.5 * (bin_edges[1:] + bin_edges[:-1])

    raf, decf = [], []
    for angle in bin_centers:
        x, y, z = (
            np.cos(a_spine) * e_av_spin
            + np.sin(a_spine) * np.cos(np.radians(angle)) * e_perp_pole
            + np.sin(a_spine) * np.sin(np.radians(angle)) * e_perp_ram
        )

        eq_ra = np.degrees(np.arctan2(y, x))
        eq_dec = np.degrees(np.arcsin(z))
        ra, dec = equatorial_to_ecliptic(eq_ra, eq_dec)
        raf.append(ra)
        decf.append(dec)

    return raf, decf


# -----------------------------------------------------------------------------
# Date, filename, and table helpers.
# -----------------------------------------------------------------------------
def extract_yyyymmdd(filename: str) -> str:
    """Extract YYYYMMDD from a GLOWS filename."""
    m = re.search(r"_(\d{8})-repoint", filename)
    if m:
        return m.group(1)

    # Fallback for names split similarly to l1b_to_spin.py.
    parts = filename.split("_")
    for part in parts:
        m2 = re.match(r"(20\d{6})", part)
        if m2:
            return m2.group(1)

    raise ValueError(f"Could not extract YYYYMMDD from filename: {filename}")


def yyyymmdd_to_yyyyddd(yyyymmdd: str) -> str:
    date = datetime.strptime(yyyymmdd, "%Y%m%d")
    return f"{date.year}{date.timetuple().tm_yday:03d}"


def extract_repoint(filename: str) -> str:
    m = re.search(r"-repoint([^_]+)", filename)
    return m.group(1) if m else ""


def read_pointing(pointing_file: Path) -> pd.DataFrame:
    pointing_cols = ["YD", "spin_ra", "spin_dec"]
    return pd.read_csv(pointing_file, names=pointing_cols, skiprows=1)


def read_pivot_table(pivot_csv: Path) -> pd.DataFrame:
    return pd.read_csv(pivot_csv)


# -----------------------------------------------------------------------------
# Good-time handling.
# This follows l1b_to_spin.py but actually uses the exposure estimate as the
# output exposure because GLOWS survival-probability files do not contain Lo
# histogram exposure_time_6deg.
# -----------------------------------------------------------------------------
def estimate_exposure_time(goodtime_file: Path, yd: int, esa: int) -> pd.Series:
    cols = [
        "YD", "gd_start", "gd_end", "bin_start", "bin_end", "Instrument",
        "E-Step1", "E-Step2", "E-Step3", "E-Step4", "E-Step5", "E-Step6",
        "E-Step7", "Comment",
    ]

    df_all = pd.read_csv(goodtime_file, names=cols)
    df = df_all[df_all["YD"] == yd]
    if df.empty:
        raise ValueError(f"No matching rows found for {yd} in good-time file")

    result = np.zeros((NESA, NSPIN_6DEG), dtype=float)

    for _, row in df.iterrows():
        gd_start = float(row["gd_start"])
        gd_end = float(row["gd_end"])

        # Same convention as l1b_to_spin.py: distribute each interval over
        # 7 ESA steps and 60 spin bins, then apply E-step and bin masks.
        dt_per_esa_per_bin = (gd_end - gd_start) / (NESA * NSPIN_6DEG)

        bin_start = int(row["bin_start"])
        bin_end = int(row["bin_end"])

        for i in range(1, NESA + 1):
            arr = np.zeros(NSPIN_6DEG, dtype=float)
            arr[bin_start:bin_end + 1] = dt_per_esa_per_bin * float(row[f"E-Step{i}"])
            result[i - 1] += arr

    result_df = pd.DataFrame(
        result.T,
        columns=[f"E-Step{i}" for i in range(1, NESA + 1)],
    )
    return result_df[f"E-Step{esa}"]


def rotate_spin_to_nep_order(values_60: np.ndarray | pd.Series) -> np.ndarray:
    """Apply the same spin-angle -> NEP-angle reordering used in l1b_to_spin.py."""
    values_60 = np.asarray(values_60, dtype=float)
    if values_60.shape[0] != NSPIN_6DEG:
        raise ValueError(f"Expected 60 spin bins, got shape {values_60.shape}")

    out = np.zeros(NSPIN_6DEG, dtype=float)
    out[0:10] = values_60[50:60]
    out[10:30] = values_60[0:20]
    out[30:60] = values_60[20:50]
    return out


# -----------------------------------------------------------------------------
# GLOWS L3e survival probability handling.
# -----------------------------------------------------------------------------
def read_glows_survival_probability(glows_file: Path) -> tuple[np.ndarray, np.ndarray]:
    """
    Read GLOWS survival probability and energy grid.

    Expected common case:
      surv_prob shape after removing singleton dimensions: (n_energy, 360)
      energy_grid shape: (n_energy,)
    """
    cdf = cdflib.CDF(str(glows_file))

    surv_prob = np.asarray(cdf.varget("surv_prob"), dtype=float)
    energy_grid = np.asarray(cdf.varget("energy_grid"), dtype=float).squeeze()

    # Remove singleton dimensions such as leading epoch dimension.
    surv_prob = np.squeeze(surv_prob)

    if energy_grid.ndim != 1:
        raise ValueError(f"energy_grid should be 1-D, got shape {energy_grid.shape}")

    # Make sure survival probability is organized as (energy, spin).
    if surv_prob.ndim != 2:
        raise ValueError(f"surv_prob should be 2-D after squeeze, got shape {surv_prob.shape}")

    if surv_prob.shape[0] == energy_grid.size:
        pass
    elif surv_prob.shape[1] == energy_grid.size:
        surv_prob = surv_prob.T
    else:
        raise ValueError(
            "Could not match surv_prob energy dimension to energy_grid: "
            f"surv_prob shape={surv_prob.shape}, energy_grid size={energy_grid.size}"
        )

    if surv_prob.shape[1] != NSPIN_1DEG:
        raise ValueError(
            f"Expected 360 1-degree spin bins in surv_prob, got shape {surv_prob.shape}"
        )

    return surv_prob, energy_grid


def interpolate_energy_to_lo(surv_prob: np.ndarray, glows_energies: np.ndarray) -> np.ndarray:
    """Interpolate GLOWS survival probability onto the 7 IMAP-Lo ESA energies."""
    f = interp1d(
        np.log(glows_energies),
        surv_prob,
        axis=0,
        kind="linear",
        bounds_error=False,
        fill_value="extrapolate",
    )

    sp_interp = f(np.log(LO_ENERGIES))

    # Survival probability should remain physically bounded.
    return np.clip(sp_interp, 1e-6, 1.0)


def rebin_spin_1deg_to_6deg(sp_interp: np.ndarray) -> np.ndarray:
    """Convert shape (7, 360) to shape (7, 60) by averaging each 6 bins."""
    if sp_interp.shape != (NESA, NSPIN_1DEG):
        raise ValueError(f"Expected interpolated shape (7, 360), got {sp_interp.shape}")

    reshaped = sp_interp.reshape(NESA, NSPIN_6DEG, SPIN_BIN_DEG)
    return reshaped.mean(axis=2)


# -----------------------------------------------------------------------------
# Main processing.
# -----------------------------------------------------------------------------
def process_files(args: argparse.Namespace) -> None:
    glows_dir = Path(args.glows_dir)
    out_dir = Path(args.out_dir)
    pointing_file = Path(args.pointing_file)
    goodtime_file = Path(args.goodtime_file)
    pivot_csv = Path(args.pivot_csv)

    for required in [glows_dir, pointing_file, goodtime_file, pivot_csv]:
        if not required.exists():
            print(f"Required path not found: {required}")
            sys.exit(1)

    for pivot_angle in args.pivot_dirs:
        os.makedirs(out_dir / f"pivot_{pivot_angle}" / "daily", exist_ok=True)

    df_point = read_pointing(pointing_file)
    df_pivot = read_pivot_table(pivot_csv)

    glows_files = sorted(glows_dir.rglob("*.cdf"))
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y%m%d")
        filtered = []
        for f in glows_files:
            try:
                dt = datetime.strptime(extract_yyyymmdd(f.name), "%Y%m%d")
            except ValueError:
                continue
            if dt >= start_date:
                filtered.append(f)
        glows_files = filtered

    print(f"Found {len(glows_files)} GLOWS L3e CDF files")

    for glows_file in glows_files:
        try:
            basename = glows_file.name
            yyyymmdd = extract_yyyymmdd(basename)
            yd = yyyymmdd_to_yyyyddd(yyyymmdd)
            int_yd = int(yd)

            print(f"Processing DOY: {yd}  file: {basename}")

            # Spin-axis information.
            df_p = df_point[df_point["YD"] == int_yd]
            if df_p.empty:
                raise ValueError(f"No matching rows found for {yd} in pointing file")

            s_ra = df_p["spin_ra"].astype(float).values[0]
            s_dec = df_p["spin_dec"].astype(float).values[0]

            # Pivot angle.
            df_pp = df_pivot[df_pivot["DOY"] == int_yd]
            if df_pp.empty:
                raise ValueError(f"No matching rows found for {yd} in pivot file")

            pivot = float(df_pp["Pivot"].values[0])
            pivot_str = f"pivot_{int(pivot)}"
            os.makedirs(out_dir / pivot_str / "daily", exist_ok=True)

            # Same sky-coordinate calculation as l1b_to_spin.py.
            ra, dec = create_ra_dec(s_ra, s_dec, pivot)
            seq_ra, seq_dec = equatorial_to_ecliptic(s_ra, s_dec)

            # Read and process GLOWS survival probability.
            surv_prob, glows_energies = read_glows_survival_probability(glows_file)
            sp_interp = interpolate_energy_to_lo(surv_prob, glows_energies)
            sp_6deg = rebin_spin_1deg_to_6deg(sp_interp)

            # Same bin centers as l1b_to_spin.py output after NEP ordering.
            nep_angles = np.linspace(0, 360, NSPIN_6DEG + 1)
            bin_centers = 0.5 * (nep_angles[1:] + nep_angles[:-1])

            for esa in range(1, NESA + 1):
                # Survival probability replaces the l1b_to_spin.py counts column.
                # Apply the same spin-angle -> NEP-angle reordering as l1b_to_spin.py.
                sp_nep = rotate_spin_to_nep_order(sp_6deg[esa - 1])

                # Exposure comes from the combined good-time file because GLOWS L3e
                # is not a Lo histogram CDF with exposure_time_6deg.
                expo_spin = estimate_exposure_time(goodtime_file, int_yd, esa)
                expo_nep = rotate_spin_to_nep_order(expo_spin)

                df_new = pd.DataFrame()
                df_new["bins"] = bin_centers
                df_new["survival_probability"] = sp_nep
                df_new["ra"] = ra
                df_new["dec"] = dec
                df_new["expo"] = expo_nep
                df_new["spin_ra"] = seq_ra
                df_new["spin_dec"] = seq_dec

                # Provenance columns for map manifest.
                df_new["date_yyyymmdd"] = yyyymmdd
                df_new["yd"] = yd
                df_new["repoint"] = extract_repoint(basename)
                df_new["pivot"] = int(pivot)
                df_new["glows_product"] = "l3e_survival_probability_lo"
                df_new["glows_filename"] = basename
                df_new["glows_path"] = str(glows_file.resolve())

                out_file = out_dir / pivot_str / "daily" / f"data_SP_YD_{yd}_esa{esa}.csv"
                df_new.to_csv(out_file, index=False)

        except Exception as exc:
            print(f"Skipping {glows_file.name}: {exc}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create Lo-style daily spin-angle files from GLOWS L3e survival probability CDFs."
    )

    parser.add_argument(
        "--glows-dir",
        default="./glows/l3e",
        help="Directory containing GLOWS L3e survival-probability CDF files.",
    )
    parser.add_argument(
        "--out-dir",
        default="./outdir_glows",
        help="Output directory. Files are written under pivot_<angle>/daily/.",
    )
    parser.add_argument(
        "--pointing-file",
        default="./config_files/pointing_file.csv",
        help="CSV with columns YD, spin_ra, spin_dec; same format used by l1b_to_spin.py.",
    )
    parser.add_argument(
        "--goodtime-file",
        default="./config_files/imap_lo_goodtimes_2.csv",
        help="Combined Lo good-times CSV; same format used by l1b_to_spin.py.",
    )
    parser.add_argument(
        "--pivot-csv",
        default="./config_files/share_pivot.csv",
        help="CSV with DOY and Pivot columns; same format used by l1b_to_spin.py.",
    )
    parser.add_argument(
        "--start-date",
        default=None,
        help="Optional first date to process, in YYYYMMDD format, e.g. 20251108.",
    )
    parser.add_argument(
        "--pivot-dirs",
        nargs="+",
        default=["75", "90", "105"],
        help="Pivot output directories to pre-create. Other pivots are created automatically if found.",
    )

    return parser


if __name__ == "__main__":
    process_files(build_arg_parser().parse_args())
