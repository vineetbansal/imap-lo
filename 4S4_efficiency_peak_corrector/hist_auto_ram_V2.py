#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov  2 17:10:13 2025

Modified:
- Reads speed2 double-von-Mises fit summary files from SPEED2_FIT_DIR.
- Matches fit rows by repoint and pivot angle.
- Adds a placeholder efficiency function based on the von-Mises fit parameters.
- Writes the placeholder efficiency and fit parameters into the histogram fit CSV output.

@author: hafijulislam
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from spacepy import pycdf
from spacepy.time import Ticktock
import re
from scipy.optimize import curve_fit
import os
import shutil
from pathlib import Path

TOF3_L = [11.0, 7.0, 3.5, 0.0]
TOF3_H = [15.0, 11.0, 7.0, 3.5]

# TOF_0, TOF_1, TOF_2
E_PEAK_H = [20.0, 10.0, 10.0]
H_PEAK_L = [20.0, 10.0, 10.0]
H_PEAK_H = [70.0, 50.0, 40.0]
CO_PEAK_L = [100.0, 60.0, 60.0]
CO_PEAK_H = [270.0, 150.0, 150.0]

# EU = C0 + C1 * ADC
ADC_TOF0 = [5.5252E-01, 1.6837E-01]
ADC_TOF1 = [-7.2018E-01, 1.6512E-01]
ADC_TOF2 = [3.7442E-01, 1.6641E-01]
ADC_TOF3 = [4.6726E-01, 1.7144E-01]


ESA_ENERGY_EV = {
    "ESA1": 16.33,
    "ESA2": 30.47,
    "ESA3": 55.76,
    "ESA4": 106.3,
    "ESA5": 200.0,
    "ESA6": 405.0,
    "ESA7": 787.3,
}

COEFFS = [1.05374034, 0.60124388, 0.32879538, 0.38521193, 0.24047775, 0.7991292]

CHKSM_LB = -21
CHKSM_RB = -6

PI = np.pi
VERY_SMALL = 1.0e-30

epoch0 = datetime(2010, 1, 1, 0, 0, 0)

MHE = 4.002602 * 1.66053906660e-24  # g
EV  = 1.602176634e-12               # erg/eV

cols = [
    "shcoarse", "absent", "timestamp", "egy", "mode",
    "TOF0", "TOF1", "TOF2", "TOF3", "checksum", "position",
]

data_dir_path = "../input_l1b_histrates"
data_dir = Path(data_dir_path)
goodtime_file = "../input_goodtime/imap_lo_goodtimes.csv"
hk_dir = Path("../input_hk")

# -----------------------------------------------------------------
# Start fresh: remove all previous output products
# ------------------------------------------------------------------

START_FRESH = True

output_root = Path("./l1b_hist_fit_csv")

if START_FRESH and output_root.exists():
    print(f"Removing previous output directory: {output_root}")
    shutil.rmtree(output_root)

# Recreate directory structure
outdir_hy = output_root / "Hydrogen"
outdir_ox = output_root / "Oxygen"

outdir_hy.mkdir(parents=True, exist_ok=True)
outdir_ox.mkdir(parents=True, exist_ok=True)

# Directory containing files like:
#   simcoll_sums_pivot75.csv
#   simcoll_sums_pivot90.csv
#   simcoll_sums_pivot105.csv
# Change this if your simcoll summary files live somewhere else.
SPEED2_FIT_DIR = Path("../4S2_primary_helium_reader/output")

def parse_key_version(filename):
    m = re.search(r"(\d{8}-repoint\d+)_v(\d+)", filename)
    if not m:
        return None, None
    key = m.group(1)
    version = int(m.group(2))
    return key, version

def get_pname(pivot):
    if 85 < pivot < 95:
        return "90"
    elif 70 < pivot < 80:
        return "75"
    elif 100 < pivot < 110:
        return "105"
    return "unknown"


def read_speed2_fit_table(fit_dir=SPEED2_FIT_DIR):
    """
    Read speed2 double-von-Mises fit summary files.

    Expected files:
        simcoll_sums_pivot75.csv
        simcoll_sums_pivot90.csv
        simcoll_sums_pivot105.csv

    Required columns:
        repoint, pivot_angle,
        speed2_vm_A1, speed2_vm_mu1_deg, speed2_vm_kappa1,
        speed2_vm_A2, speed2_vm_mu2_deg, speed2_vm_kappa2

    Optional columns:
        speed2_vm_R, speed2_vm_R2, speed2_vm_rms, uncertainties, peak heights
    """
    fit_dir = Path(fit_dir)
    files = sorted(fit_dir.glob("simcoll_sums_pivot*.csv"))

    if len(files) == 0:
        print(f"WARNING: no speed2 fit files found in {fit_dir}")
        return pd.DataFrame()

    dfs = []
    for f in files:
        try:
            dfi = pd.read_csv(f)
            dfi["fit_source_file"] = f.name
            dfs.append(dfi)
        except Exception as e:
            print(f"WARNING: could not read speed2 fit file {f}: {e}")

    if len(dfs) == 0:
        return pd.DataFrame()

    fit_df = pd.concat(dfs, ignore_index=True)

    required = [
        "repoint", "pivot_angle",
        "speed2_vm_A1", "speed2_vm_mu1_deg", "speed2_vm_kappa1",
        "speed2_vm_A2", "speed2_vm_mu2_deg", "speed2_vm_kappa2",
    ]
    missing = [c for c in required if c not in fit_df.columns]
    if missing:
        print(f"WARNING: speed2 fit table is missing columns: {missing}")

    return fit_df


def get_speed2_fit_row(fit_df, repoint, pname, file_date=None):
    """
    Get speed2 fit row matching repoint and pivot name.

    Matching priority:
      1. repoint + pivot_angle
      2. if file_date is available and the fit table has a file/date column,
         prefer matching date as a tie-breaker.

    pname is expected to be '75', '90', or '105'.
    """
    if fit_df is None or len(fit_df) == 0:
        return None

    if pname == "unknown":
        return None

    try:
        pivot_target = float(pname)
        repoint_int = int(repoint)
    except Exception:
        return None

    needed = {"repoint", "pivot_angle"}
    if not needed.issubset(set(fit_df.columns)):
        return None

    rep = pd.to_numeric(fit_df["repoint"], errors="coerce")
    piv = pd.to_numeric(fit_df["pivot_angle"], errors="coerce")
    m = (rep == repoint_int) & np.isclose(piv, pivot_target, atol=2.0)
    this = fit_df[m].copy()

    if len(this) == 0:
        return None

    # If multiple rows match, prefer matching date if possible.
    if file_date is not None and len(this) > 1:
        file_date_str = str(file_date)

        if "file" in this.columns:
            mdate = this["file"].astype(str).str.contains(file_date_str, regex=False)
            if np.any(mdate):
                this = this[mdate]
        elif "date" in this.columns:
            mdate = this["date"].astype(str) == file_date_str
            if np.any(mdate):
                this = this[mdate]

    return this.iloc[0]


def arbitrary_efficiency_from_speed2_vm_fit(fit_row, esa_name, element):
    """
    Placeholder efficiency function based on the speed2 double-von-Mises fit.

    Replace the body of this function later with the real instrument/physics
    efficiency model.
    """
    if fit_row is None:
        return np.nan

    try:
        A1 = float(fit_row["speed2_vm_A1"])
        k1 = float(fit_row["speed2_vm_kappa1"])
        A2 = float(fit_row["speed2_vm_A2"])
        k2 = float(fit_row["speed2_vm_kappa2"])
    except Exception:
        return np.nan

    if not np.all(np.isfinite([A1, k1, A2, k2])):
        return np.nan

    # For A*exp(kappa*cos(theta-mu)), peak contribution is A*exp(kappa).
    peak1 = A1 * np.exp(k1)
    peak2 = A2 * np.exp(k2)

    # ESA and element hooks are intentionally included for future use.
    esa_num = int(esa_name.replace("ESA", ""))
    element_factor = 1.0 if element == "Hydrogen" else 1.0
    esa_factor = 1.0 + 0.0 * esa_num

    # Arbitrary placeholder. Replace this line later.
    eff = element_factor * esa_factor * (peak1 + peak2) / (1.0 + k1 + k2)
    return eff


def get_fit_value(fit_row, colname):
    """Safely get a scalar fit value for output."""
    if fit_row is None:
        return np.nan
    try:
        return float(fit_row.get(colname, np.nan))
    except Exception:
        return np.nan


def get_fit_source_file(fit_row):
    if fit_row is None:
        return ""
    try:
        return str(fit_row.get("fit_source_file", ""))
    except Exception:
        return ""


def doy_fraction(t):
    start = datetime(t.year, 1, 1)
    return (t - start).total_seconds() / 86400.0 + 1


def met_from_epoch(t):
    try:
        return np.array([(ti - epoch0).total_seconds() + 9 for ti in t], dtype=float)
    except TypeError:
        return (t - epoch0).total_seconds() + 9


def gaussian(x, A, mu, sigma, C):
    return A * np.exp(-0.5 * ((x - mu) / sigma) ** 2) + C


def unwrap_angles(theta_deg, center_deg):
    return ((theta_deg - center_deg + 180.0) % 360.0) - 180.0 + center_deg


def select_peak_window(theta_deg, y, half_width=30.0):
    ipeak = np.argmax(y)
    peak_angle = theta_deg[ipeak]

    i90 = np.argmin(np.abs(theta_deg - 90.0))
    if np.abs(peak_angle - 90.0) > 12.0:
        ipeak = i90
        peak_angle = theta_deg[ipeak]

    theta_unwrapped = unwrap_angles(theta_deg, peak_angle)
    keep = np.abs(theta_unwrapped - peak_angle) <= half_width
    return theta_unwrapped[keep], y[keep], peak_angle


def select_peak_window_wexp(theta_deg, y, exposure, half_width=30.0):
    ipeak = np.argmax(y)
    peak_angle = theta_deg[ipeak]

    i90 = np.argmin(np.abs(theta_deg - 90.0))
    if np.abs(peak_angle - 90.0) > 12.0:
        ipeak = i90
        peak_angle = theta_deg[ipeak]

    theta_unwrapped = unwrap_angles(theta_deg, peak_angle)
    keep = np.abs(theta_unwrapped - peak_angle) <= half_width
    return theta_unwrapped[keep], y[keep], exposure[keep], peak_angle


def compute_moments(theta_deg, y):
    yuse = np.clip(y, 0.0, None)
    dx = theta_deg[1] - theta_deg[0]
    norm = np.sum(yuse)

    if norm <= 0:
        return np.nan, np.nan, np.nan

    mu = np.sum(theta_deg * yuse) / norm
    sigma = np.sqrt(np.sum(yuse * (theta_deg - mu) ** 2) / norm)
    peak = norm * dx / (np.sqrt(2.0 * np.pi) * (sigma + VERY_SMALL))
    return mu, sigma, peak


def compute_moments_wunc(theta_deg, y, exposure_bin):
    yuse = np.clip(y, 0.0, None)
    dx = theta_deg[1] - theta_deg[0]
    norm = np.sum(yuse)
    cnts = exposure_bin * yuse
    sum_cnts = np.sum(cnts)

    if norm <= 0:
        return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan

    mu = np.sum(theta_deg * yuse) / norm
    dmu = 12.0 / np.sqrt(sum_cnts + VERY_SMALL)
    sigma = np.sqrt(np.sum(yuse * (theta_deg - mu) ** 2) / norm)
    dsigma = np.sqrt(sigma**2 / np.sqrt(sum_cnts + VERY_SMALL) + dmu**2)
    peak = norm * dx / (np.sqrt(2.0 * np.pi) * (sigma + VERY_SMALL))
    cnt_peak = peak * sum_cnts / (norm + VERY_SMALL)
    dpeak = peak / np.sqrt(cnt_peak + VERY_SMALL)
    return mu, dmu, sigma, dsigma, peak, dpeak


def do_gaussian_fit_local(theta_deg, y, half_width=30.0):
    if np.all(y <= 0):
        return np.nan, np.nan, np.nan, np.nan

    xw, yw, peak_angle = select_peak_window(theta_deg, y, half_width=half_width)
    if len(xw) < 4:
        return np.nan, np.nan, np.nan, np.nan

    C0 = np.min(yw)
    A0 = np.max(yw) - C0
    mu0 = xw[np.argmax(yw)]
    sigma0 = 12.0

    try:
        popt, pcov = curve_fit(
            gaussian,
            xw,
            yw,
            p0=[A0, mu0, sigma0, C0],
            maxfev=10000,
        )
        A, mu, sigma, C = popt
        sigma = abs(sigma)
        peak = A + C
        return mu, sigma, peak, C
    except Exception:
        return np.nan, np.nan, np.nan, np.nan


def do_gaussian_fit_local_wunc(theta_deg, y, dy, half_width=30.0):
    nan_return = (
        np.nan, np.nan, np.nan, np.nan,
        np.nan, np.nan, np.nan, np.nan,
        np.nan, np.nan,
    )

    if np.all(y <= 0):
        return nan_return

    xw, yw, peak_angle = select_peak_window(theta_deg, y, half_width=half_width)

    theta_unwrapped = unwrap_angles(theta_deg, peak_angle)
    keep = np.abs(theta_unwrapped - peak_angle) <= half_width
    dyw = np.asarray(dy)[keep]

    if len(xw) < 4:
        return nan_return

    dyw = np.asarray(dyw, dtype=float)
    bad = ~np.isfinite(dyw) | (dyw <= 0)
    if np.any(bad):
        dyw = dyw.copy()
        dyw[bad] = np.nan

    if np.all(~np.isfinite(dyw)):
        return nan_return

    finite_dyw = dyw[np.isfinite(dyw)]
    large_unc = np.nanmax(finite_dyw) if len(finite_dyw) > 0 else 1.0
    dyw[~np.isfinite(dyw)] = large_unc * 1.0e6

    C0 = np.min(yw)
    A0 = np.max(yw) - C0
    mu0 = xw[np.argmax(yw)]
    sigma0 = 12.0

    try:
        popt, pcov = curve_fit(
            gaussian,
            xw,
            yw,
            p0=[A0, mu0, sigma0, C0],
            sigma=dyw,
            absolute_sigma=True,
            maxfev=10000,
        )

        A, mu, sigma, C = popt
        sigma = abs(sigma)
        peak = A + C

        perr = np.sqrt(np.diag(pcov))
        A_unc, mu_unc, sigma_unc, C_unc = perr
        sigma_unc = abs(sigma_unc)

        peak_var = pcov[0, 0] + pcov[3, 3] + 2.0 * pcov[0, 3]
        peak_unc = np.sqrt(max(0.0, peak_var))

        return (
            mu, sigma, peak, C,
            mu_unc, sigma_unc, peak_unc, C_unc,
            A, A_unc,
        )
    except Exception:
        return nan_return


def parse_hist_metadata(filename):
    """
    Example:
    imap_lo_l1b_histrates_20260217-repoint00160_v002.cdf
    """
    m = re.search(r"(\d{8})-repoint(\d+)_v(\d+)", filename)
    if not m:
        return None, None, None
    file_date = m.group(1)
    repoint = m.group(2)
    version = m.group(3)
    return file_date, repoint, version


def ensure_header(csvfile):
    if (not csvfile.exists()) or (csvfile.stat().st_size == 0):
        with open(csvfile, "w") as f:
            print(
                "file_date,YYYYDOY,days_since_2025,repoint,version,pivot,pname,element,esa,"
                "exposure_s,peak_angle_bin,"
                "mu_mom,sigma_mom,peak_mom,"
                "mu_fit,sigma_fit,peak_fit,bg_fit",
                file=f,
            )


def ensure_header_wunc(csvfile):
    if (not csvfile.exists()) or (csvfile.stat().st_size == 0):
        with open(csvfile, "w") as f:
            print(
                "file_date,YYYYDOY,days_since_2025,repoint,version,pivot,pname,element,esa,"
                "exposure_s,peak_angle_bin,"
                "mu_mom,dmu_mom,sigma_mom,dsigma_mom,peak_mom,dpeak_mom,"
                "mu_fit,dmu_fit,sigma_fit,dsigma_fit,peak_fit(A),dpeak_fit(dA),bg_fit,dbg_fit,"
                "speed2_eff_placeholder,"
                "speed2_vm_A1,speed2_vm_A1_err,"
                "speed2_vm_mu1_deg,speed2_vm_mu1_deg_err,"
                "speed2_vm_kappa1,speed2_vm_kappa1_err,"
                "speed2_vm_peak1_height,"
                "speed2_vm_A2,speed2_vm_A2_err,"
                "speed2_vm_mu2_deg,speed2_vm_mu2_deg_err,"
                "speed2_vm_kappa2,speed2_vm_kappa2_err,"
                "speed2_vm_peak2_height,"
                "speed2_vm_rms,speed2_vm_R,speed2_vm_R2,"
                "speed2_fit_source_file",
                file=f,
            )


def write_result_line(fout, result):
    print(
        f"{result['esa']},"
        f"{result['mu_mom']:.3f},{result['sigma_mom']:.3f},{result['peak_mom']:.6e},"
        f"{result['mu_fit']:.3f},{result['sigma_fit']:.3f},{result['peak_fit']:.6e},{result['bg_fit']:.6e}",
        file=fout,
    )

def replace_matching_line(outfile, new_line, file_date, repoint, esa_name):
    header = None
    data_lines = []

    if os.path.exists(outfile):
        with open(outfile, "r") as fin:
            lines = fin.readlines()

        if lines:
            header = lines[0]
            data_lines = lines[1:]

    # Remove any existing matching row
    kept = []
    for line in data_lines:
        parts = line.rstrip("\n").split(",")
        if len(parts) >= 8 and (
            parts[0] == str(file_date)
            and parts[2] == str(repoint)
            and parts[7] == str(esa_name)
        ):
            continue
        kept.append(line.rstrip("\n"))

    # Add new row
    kept.append(new_line)

    # Sort by YYYYDOY, then repoint, then version
    def sort_key(line):
        parts = line.split(",")
        try:
            yyyydoy = int(parts[1])
        except Exception:
            yyyydoy = 9999999

        try:
            rep = int(parts[2])
        except Exception:
            rep = 999999

        try:
            ver = int(parts[3])
        except Exception:
            ver = 999999

        return (yyyydoy, rep, ver)

    kept = sorted(kept, key=sort_key)

    with open(outfile, "w") as fout:
        if header is not None:
            fout.write(header)
        fout.write("\n".join(kept) + "\n")

def von_mises_component(theta_deg, A, mu_deg, kappa):
    """
    A * exp(kappa * cos(theta - mu))
    theta and mu are in degrees.
    """
    theta = np.radians(theta_deg)
    mu = np.radians(mu_deg)

    return A * np.exp(kappa * np.cos(theta - mu))


def double_von_mises_speed2(theta_deg, fit_row):
    """
    Evaluate the fitted speed2 double-von-Mises model.
    """
    if fit_row is None:
        return np.full_like(np.asarray(theta_deg, dtype=float), np.nan)

    theta = np.asarray(theta_deg, dtype=float)

    A1 = float(fit_row["speed2_vm_A1"])
    mu1 = float(fit_row["speed2_vm_mu1_deg"])
    k1 = float(fit_row["speed2_vm_kappa1"])

    A2 = float(fit_row["speed2_vm_A2"])
    mu2 = float(fit_row["speed2_vm_mu2_deg"])
    k2 = float(fit_row["speed2_vm_kappa2"])

    return (
        von_mises_component(theta, A1, mu1, k1)
        + von_mises_component(theta, A2, mu2, k2)
    )

def response_function(x, coeffs):
    A, xc1, sig1, B, xc2, sig2 = coeffs
    x = np.asarray(x, dtype=float)
    x_safe = np.clip(x, 1e-10, None)
    log_x = np.log(x_safe)
    
    mu1 = np.log(np.clip(xc1, 1e-8, None))
    peak1 = A * np.exp(-0.5 * ((log_x - mu1) / sig1)**2)
    
    mu2 = np.log(np.clip(xc2, 1e-8, None))
    peak2 = B * np.exp(-0.5 * ((log_x - mu2) / sig2)**2)
    
    return peak1 + peak2

def compute_efficiency(theta_deg, speed2_fit_row, esa_name, element):
    """
    Placeholder efficiency correction derived from the double-von-Mises
    fit to speed2.

    Returns an efficiency array with the same shape as theta_deg.

    Current placeholder behavior:
      efficiency(theta) = speed2_fit(theta) / max(speed2_fit)

    This gives:
      max efficiency = 1
      lower speed2 response regions receive larger rate corrections

    Later, replace the normalization/expression below with the real
    physical efficiency model.
    """
    theta = np.asarray(theta_deg, dtype=float)

    esa_energy_ev = ESA_ENERGY_EV.get(esa_name, np.nan)

    speed2_model = double_von_mises_speed2(theta, speed2_fit_row)
    energy_isn = 0.5*speed2_model*1.0e10*MHE/EV
    x_eff = esa_energy_ev / energy_isn

    debug_energy = True

    if debug_energy and esa_name == "ESA3":
        print()
        print("EFF ENERGY DEBUG (ESA3):")
        print(f"  file_date={file_date} repoint={repoint} element={element}")
        print(f"  ESA_energy_eV = {esa_energy_ev:.3f}")

        print(
            f"  energy_isn [eV]: min={np.nanmin(energy_isn):.3e} "
            f"max={np.nanmax(energy_isn):.3e} "
            f"mean={np.nanmean(energy_isn):.3e}"
        )

        print(
            f"  x_eff = ESA/E_ISN: min={np.nanmin(x_eff):.3e} "
            f"max={np.nanmax(x_eff):.3e} "
            f"mean={np.nanmean(x_eff):.3e}"
        )

        # optional: print a few bins around peak
        if np.any(np.isfinite(energy_isn)):
            ipeak = int(np.nanargmax(speed2_model))
            idxs = [(ipeak + j) % len(theta_deg) for j in range(-2, 3)]

            print("  bin theta_deg   E_ISN[eV]    x_eff")
            for ii in idxs:
                print(
                    f"  {ii:02d}  {theta_deg[ii]:8.3f}  "
                    f"{energy_isn[ii]:12.5e}  {x_eff[ii]:12.5e}"
                )
        print()

    eff_model = response_function(x_eff, COEFFS)

    if np.all(~np.isfinite(eff_model)):
        return np.ones_like(theta)

    eff_model = np.asarray(eff_model, dtype=float)

    bad = ~np.isfinite(eff_model) | (eff_model <= 0)
    if np.all(bad):
        return np.ones_like(theta)

    max_eff = np.nanmax(eff_model[~bad])

    if not np.isfinite(max_eff) or max_eff <= 0:
        return np.ones_like(theta)

    efficiency = eff_model / max_eff

    # protect against division explosions later
    efficiency = np.clip(efficiency, 1.0e-6, 1.0)

    return efficiency


# -----------------------------------------------------------------------------
# Main processing
# -----------------------------------------------------------------------------

epoch = datetime(2010, 1, 1, 0, 0, 0)
ref_date = datetime(2025, 1, 1)

hk_latest = {}
for hk_file in hk_dir.glob("*.cdf"):
    key, ver = parse_key_version(hk_file.name)
    if key is None:
        continue
    if (key not in hk_latest) or (ver > hk_latest[key][0]):
        hk_latest[key] = (ver, hk_file)

hist_latest = {}
for file in data_dir.glob("*.cdf"):
    key, ver = parse_key_version(file.name)
    if key is None:
        continue
    if (key not in hist_latest) or (ver > hist_latest[key][0]):
        hist_latest[key] = (ver, file)

print("4S4: processing goodtime histogram H and O")

df = pd.read_csv(
    goodtime_file,
    header=None,
    usecols=range(14),
    dtype=str,
)

print("goodtime_file = ", goodtime_file)

df.columns = [
    "date", "time_start", "time_end", "bin_start", "bin_end",
    "inst", "esa1", "esa2", "esa3", "esa4", "esa5", "esa6", "esa7", "bla",
]

numeric_cols = [
    "date", "time_start", "time_end", "bin_start", "bin_end",
    "esa1", "esa2", "esa3", "esa4", "esa5", "esa6", "esa7",
]
df[numeric_cols] = df[numeric_cols].astype(int)

inst = df["inst"].to_numpy()
time_start = df["time_start"].to_numpy().copy()
time_end = df["time_end"].to_numpy().copy()
bin_start = df["bin_start"].to_numpy().copy()
bin_end = df["bin_end"].to_numpy().copy()
esa_flags = df[["esa1", "esa2", "esa3", "esa4", "esa5", "esa6", "esa7"]].to_numpy().copy()

ngoodt = len(time_end)
time_end_copy = time_end.copy()

nep = (3.0 + 6.0 * np.arange(60, dtype=float)) % 360.0

# Read speed2 double-von-Mises fit files once, before processing histograms.
speed2_fit_df = read_speed2_fit_table(SPEED2_FIT_DIR)
print(f"Read {len(speed2_fit_df)} speed2 fit rows from {SPEED2_FIT_DIR}")

for key in sorted(hist_latest):
    hist_file = hist_latest[key][1]
    hk_entry = hk_latest.get(key)

    if hk_entry is None:
        print(f"Missing HK for {hist_file.name}")
        continue

    hk_file = hk_entry[1]


    print("4S4 Processing hist file and HK file:", hist_file, hk_file)

    cdf_hk = pycdf.CDF(str(hk_file))
    try:
        epoch_hk = cdf_hk["epoch"]
        tt = Ticktock(epoch_hk, "CDF")
        times = np.array(tt.UTC)

        t0_hk = times[0]
        start_time_hk = t0_hk + timedelta(hours=3)
        end_time_hk = t0_hk + timedelta(hours=15)
        mask_hk = (times >= start_time_hk) & (times <= end_time_hk)

        try:
            pri = cdf_hk["pcc_coarse_pot_pri"][...]
            pivot = np.nanmedian(pri[mask_hk])
            if np.isnan(pivot):
                pivot = 90.0
        except Exception:
            pivot = 90.0

        try:
            spin_period = cdf_hk["spin_period"][...]
            tspin = np.nanmedian(spin_period[mask_hk])
            if np.isnan(tspin):
                tspin = 15.0
        except Exception:
            tspin = 15.0

    except Exception:
        pivot = 90.0
        tspin = 15.0
    finally:
        cdf_hk.close()

    pname = get_pname(pivot)

    cdf = pycdf.CDF(str(hist_file))
    try:
        epoch = cdf["epoch"][:]
        yr1 = epoch[0].year
        doy1 = int(doy_fraction(epoch[0]))
        sdoy1 = f"{doy1:03d}"
        date1 = f"{yr1}{sdoy1}"

        days_since_2025 = (
            (epoch[0] - ref_date).days
        ) + 1

        file_date, repoint, version = parse_hist_metadata(hist_file.name)
        if file_date is None:
            file_date = "unknown"
            repoint = "unknown"
            version = "unknown"

        speed2_fit_row = get_speed2_fit_row(
            speed2_fit_df,
            repoint=repoint,
            pname=pname,
            file_date=file_date,
        )

        if speed2_fit_row is None:
            print(
                f"WARNING: no speed2 VM fit row found for "
                f"file_date={file_date}, repoint={repoint}, pname={pname}"
            )
            speed2_fit_source_file = ""
        else:
            speed2_fit_source_file = get_fit_source_file(speed2_fit_row)

        for element in ["Oxygen", "Hydrogen"]:
            if element == "Hydrogen":
                el = "h"
                outdir = outdir_hy / pname
            else:
                el = "o"
                outdir = outdir_ox / pname

            outdir.mkdir(parents=True, exist_ok=True)

            counts = cdf[f"{el}_counts"][...][:, :, :]
            epoch = cdf["epoch"][:]
            met = met_from_epoch(epoch)

            theta_deg = nep.copy()

            for esa_name in ["ESA1", "ESA2", "ESA3", "ESA4", "ESA5", "ESA6", "ESA7"]:
                esa_num = int(esa_name.replace("ESA", ""))
                esa_col = esa_num - 1

                total_cnts = np.zeros(60, dtype=float)
                expo = np.zeros(60, dtype=float)

                for bin in range(60):
                    time_end[:] = time_end_copy[:]

                    for itime in range(ngoodt):
                        if esa_flags[itime, esa_col] == 0:
                            time_end[itime] = time_start[itime]

                        if (bin > bin_end[itime]) or (bin < bin_start[itime]):
                            time_end[itime] = time_start[itime]

                    met_check = (met[:, None] >= time_start) & (met[:, None] <= time_end)
                    mask = np.any(met_check, axis=1)

                    total_cnts[bin] = np.sum(counts[mask, esa_col, bin])
                    expo[bin] = np.count_nonzero(mask) * 4.0 * tspin / (60.0 )

                nep_cnts = np.zeros(60)
                nep_expo = np.zeros(60)

                nep_cnts[0:10] = total_cnts[50:60]
                nep_cnts[10:30] = total_cnts[0:20]
                nep_cnts[30:60] = total_cnts[20:50]

                nep_expo[0:10] = expo[50:60]
                nep_expo[10:30] = expo[0:20]
                nep_expo[30:60] = expo[20:50]


                rates_raw = nep_cnts / (nep_expo + VERY_SMALL)
                drates_raw = rates_raw / np.sqrt(nep_cnts + VERY_SMALL)

                efficiency = compute_efficiency(theta_deg, speed2_fit_row, esa_name, element)
                eff_safe = np.clip(efficiency, 1.0e-6, None)

                rates = rates_raw / eff_safe
                drates = drates_raw / eff_safe

                # -------------------------------
                # DEBUG: rates before/after correction near peak
                # -------------------------------
                debug_efficiency = True

                if debug_efficiency and np.any(rates_raw > 0):
                    ipeak = int(np.nanargmax(rates_raw))

                    # show +/- 3 bins around raw peak, with wrap-around
                    idxs = [(ipeak + j) % len(rates_raw) for j in range(-3, 4)]

                    print()
                    print(
                        f"EFF DEBUG: {file_date} repoint={repoint} "
                        f"{element} {esa_name} pivot={pivot:.3f} pname={pname}"
                    )
                    print(
                        f"  raw peak bin={ipeak}, theta={theta_deg[ipeak]:.3f}, "
                        f"raw_rate={rates_raw[ipeak]:.6e}, "
                        f"eff={eff_safe[ipeak]:.6e}, "
                        f"corr_rate={rates[ipeak]:.6e}"
                    )
                    print("  bin theta_deg    counts       expo_s       eff          raw_rate      corr_rate     ratio")
                    for ii in idxs:
                        ratio = rates[ii] / (rates_raw[ii] + VERY_SMALL)
                        print(
                            f"  {ii:02d}  {theta_deg[ii]:8.3f}  "
                            f"{nep_cnts[ii]:10.3f}  {nep_expo[ii]:10.3f}  "
                            f"{eff_safe[ii]:10.3e}  "
                            f"{rates_raw[ii]:12.5e}  {rates[ii]:12.5e}  {ratio:9.3f}"
                        )
                    print()

                if not np.any(rates > 0):
                    continue

                valid_expo = nep_expo[nep_expo > 0]
                if len(valid_expo) > 0:
                    exposure_s = np.mean(valid_expo)
                else:
                    exposure_s = 0.0

                theta_local, rates_local, exposure_local, peak_angle = select_peak_window_wexp(
                    theta_deg,
                    rates,
                    nep_expo,
                    half_width=30.0,
                )

                (
                    mu_mom,
                    dmu_mom,
                    sigma_mom,
                    dsigma_mom,
                    peak_mom,
                    dpeak_mom,
                ) = compute_moments_wunc(theta_local, rates_local, exposure_local)

                (
                    mu_fit,
                    sigma_fit,
                    peak_fit,
                    bg_fit,
                    mu_unc,
                    sigma_unc,
                    peak_unc,
                    C_unc,
                    A,
                    A_unc,
                ) = do_gaussian_fit_local_wunc(theta_deg, rates, drates, half_width=30.0)

                speed2_eff = arbitrary_efficiency_from_speed2_vm_fit(
                    speed2_fit_row,
                    esa_name=esa_name,
                    element=element,
                )

                speed2_A1 = get_fit_value(speed2_fit_row, "speed2_vm_A1")
                speed2_A1_err = get_fit_value(speed2_fit_row, "speed2_vm_A1_err")
                speed2_mu1 = get_fit_value(speed2_fit_row, "speed2_vm_mu1_deg")
                speed2_mu1_err = get_fit_value(speed2_fit_row, "speed2_vm_mu1_deg_err")
                speed2_k1 = get_fit_value(speed2_fit_row, "speed2_vm_kappa1")
                speed2_k1_err = get_fit_value(speed2_fit_row, "speed2_vm_kappa1_err")
                speed2_peak1 = get_fit_value(speed2_fit_row, "speed2_vm_peak1_height")

                speed2_A2 = get_fit_value(speed2_fit_row, "speed2_vm_A2")
                speed2_A2_err = get_fit_value(speed2_fit_row, "speed2_vm_A2_err")
                speed2_mu2 = get_fit_value(speed2_fit_row, "speed2_vm_mu2_deg")
                speed2_mu2_err = get_fit_value(speed2_fit_row, "speed2_vm_mu2_deg_err")
                speed2_k2 = get_fit_value(speed2_fit_row, "speed2_vm_kappa2")
                speed2_k2_err = get_fit_value(speed2_fit_row, "speed2_vm_kappa2_err")
                speed2_peak2 = get_fit_value(speed2_fit_row, "speed2_vm_peak2_height")

                speed2_rms = get_fit_value(speed2_fit_row, "speed2_vm_rms")
                speed2_R = get_fit_value(speed2_fit_row, "speed2_vm_R")
                speed2_R2 = get_fit_value(speed2_fit_row, "speed2_vm_R2")

                esa_dir = outdir / esa_name
                esa_dir.mkdir(parents=True, exist_ok=True)

                outfile = esa_dir / f"{element}_{pname}_{esa_name}.csv"
                ensure_header_wunc(outfile)

                new_line = (
                    f"{file_date},{date1},{days_since_2025},{repoint},{version},"
                    f"{pivot:.3f},{pname},{element},{esa_name},"
                    f"{exposure_s:.3f},{peak_angle:.3f},"
                    f"{mu_mom:.6f},{dmu_mom:.6f},{sigma_mom:.6f},{dsigma_mom:.6f},{peak_mom:.6e},{dpeak_mom:.6e},"
                    f"{mu_fit:.6f},{mu_unc:.6f},{sigma_fit:.6f},{sigma_unc:.6f},"
                    f"{A:.6e},{A_unc:.6e},{bg_fit:.6e},{C_unc:.6e},"
                    f"{speed2_eff:.6e},"
                    f"{speed2_A1:.6e},{speed2_A1_err:.6e},"
                    f"{speed2_mu1:.6f},{speed2_mu1_err:.6f},"
                    f"{speed2_k1:.6f},{speed2_k1_err:.6f},"
                    f"{speed2_peak1:.6e},"
                    f"{speed2_A2:.6e},{speed2_A2_err:.6e},"
                    f"{speed2_mu2:.6f},{speed2_mu2_err:.6f},"
                    f"{speed2_k2:.6f},{speed2_k2_err:.6f},"
                    f"{speed2_peak2:.6e},"
                    f"{speed2_rms:.6e},{speed2_R:.6f},{speed2_R2:.6f},"
                    f"{speed2_fit_source_file}"
                )

                with open(outfile, "a") as fout:
                    fout.write(new_line + "\n")

                print(
                    "4S4 : ",
                    f"{file_date},{date1},{repoint},{version},"
                    f"{pivot:.3f},{pname},{element},{esa_name},"
                    f"{exposure_s:.3f},{peak_angle:.3f},"
                    f"{mu_mom:.6f},{sigma_mom:.6f},{peak_mom:.6e},"
                    f"{mu_fit:.6f},{sigma_fit:.6f},{peak_fit:.6e},{bg_fit:.6e},"
                    f"speed2_eff={speed2_eff:.6e}, speed2_R={speed2_R:.6f}",
                )

    finally:
        cdf.close()

