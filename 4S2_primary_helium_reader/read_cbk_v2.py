#!/usr/bin/env python3

import os
import re
import glob
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.optimize import curve_fit


PIVOT_ANGLES_TO_WRITE = [75.0, 90.0, 105.0]

FIT_FORM = (
    "speed2(theta) = "
    "A1*exp(kappa1*cos(rad(theta - mu1_deg))) "
    "+ A2*exp(kappa2*cos(rad(theta - mu2_deg)))"
)


def read_simcoll_file(fname):
    meta = {}
    data_lines = []

    with open(fname, "r") as f:
        for line in f:
            s = line.strip()

            if not s:
                continue

            if s.startswith("#"):
                if "Axis to the Sun" in s:
                    for key in ["alpha_ecl", "delta_Ecl", "delta_Ax", "repoint"]:
                        m = re.search(rf"{key}\s*=\s*([+-]?\d+(?:\.\d*)?)", s)
                        if m:
                            val = m.group(1)
                            meta[key] = int(val) if key == "repoint" else float(val)
                continue

            data_lines.append(s)

    cols = [
        "spin",
        "flux",
        "speed",
        "speed2",
        "speed3",
        "lon_ecl",
        "lat_ecl",
    ]

    data = np.array([[float(x) for x in row.split()] for row in data_lines])
    df = pd.DataFrame(data, columns=cols)

    base = os.path.basename(fname)

    if "repoint" not in meta:
        m = re.search(r"repoint(\d+)", base)
        if m:
            meta["repoint"] = int(m.group(1))

    m = re.search(r"_(\d{4}\.\d+)_", base)
    if m:
        meta["time_yyyy_frac"] = float(m.group(1))

    if "delta_Ax" not in meta:
        m = re.search(r"_(\d+(?:\.\d+)?)\.dat$", base)
        if m:
            meta["delta_Ax"] = float(m.group(1))

    return df, meta


def yyyy_frac_to_doy(yf):
    """
    Convert fractional year like 2025.950 to day-of-year.
    Returns 1-based DOY.
    """
    year = int(yf)
    frac = yf - year

    days_in_year = 366 if pd.Timestamp(f"{year}-12-31").dayofyear == 366 else 365

    return 1.0 + frac * days_in_year


def von_mises_component(theta_deg, A, mu_deg, kappa):
    """
    One von Mises-like component.

    theta_deg : spin angle in degrees
    A         : scale factor
    mu_deg    : center angle in degrees
    kappa     : concentration parameter

    Note:
    Peak contribution is A * exp(kappa), not simply A.
    """
    theta = np.radians(theta_deg)
    mu = np.radians(mu_deg)
    return A * np.exp(kappa * np.cos(theta - mu))


def double_von_mises(theta_deg, A1, mu1, k1, A2, mu2, k2):
    """
    Double von Mises fit form:

    speed2(theta) =
        A1 * exp(kappa1 * cos(rad(theta - mu1_deg)))
      + A2 * exp(kappa2 * cos(rad(theta - mu2_deg)))
    """
    return (
        von_mises_component(theta_deg, A1, mu1, k1)
        + von_mises_component(theta_deg, A2, mu2, k2)
    )


def nan_fit_result():
    names = [
        "A1", "mu1_deg", "kappa1",
        "A2", "mu2_deg", "kappa2",
    ]

    out = {}

    for name in names:
        out[name] = np.nan
        out[f"{name}_err"] = np.nan

    out["peak1_height"] = np.nan
    out["peak2_height"] = np.nan
    out["rms"] = np.nan
    out["R"] = np.nan
    out["R2"] = np.nan

    return out


def fit_speed2_double_von_mises(df):
    """
    Fit speed2 as a function of spin angle using two von Mises terms.

    Returns fitted parameters, 1-sigma uncertainties, RMS residual,
    correlation coefficient R, and R^2.
    """
    x = df["spin"].to_numpy(dtype=float)
    y = df["speed2"].to_numpy(dtype=float)

    good = np.isfinite(x) & np.isfinite(y)
    x = x[good]
    y = y[good]

    names = [
        "A1", "mu1_deg", "kappa1",
        "A2", "mu2_deg", "kappa2",
    ]

    if len(x) < 10:
        return nan_fit_result()

    ymax = np.nanmax(y)

    if not np.isfinite(ymax) or ymax <= 0:
        return nan_fit_result()

    # Primary component guess: strongest observed peak
    A10 = ymax
    mu10 = x[np.nanargmax(y)]

    # Secondary component guess: roughly opposite side
    A20 = 0.15 * A10
    mu20 = (mu10 + 180.0) % 360.0

    p0 = [
        A10, mu10, 3.0,
        A20, mu20, 2.0,
    ]

    bounds_lower = [
        0.0, 0.0, 0.01,
        0.0, 0.0, 0.01,
    ]

    bounds_upper = [
        np.inf, 360.0, 100.0,
        np.inf, 360.0, 100.0,
    ]

    try:
        popt, pcov = curve_fit(
            double_von_mises,
            x,
            y,
            p0=p0,
            bounds=(bounds_lower, bounds_upper),
            maxfev=50000,
        )

        perr = np.sqrt(np.diag(pcov))

        yfit = double_von_mises(x, *popt)
        resid = y - yfit
        rms = np.sqrt(np.mean(resid**2))

        if len(y) > 1 and np.std(y) > 0 and np.std(yfit) > 0:
            R = np.corrcoef(y, yfit)[0, 1]
            R2 = R**2
        else:
            R = np.nan
            R2 = np.nan

        out = {}

        for name, val, err in zip(names, popt, perr):
            out[name] = val
            out[f"{name}_err"] = err

        A1, mu1, k1, A2, mu2, k2 = popt

        out["peak1_height"] = A1 * np.exp(k1)
        out["peak2_height"] = A2 * np.exp(k2)
        out["rms"] = rms
        out["R"] = R
        out["R2"] = R2

        return out

    except Exception as e:
        print(f"WARNING: speed2 double von Mises fit failed: {e}")
        return nan_fit_result()


def summarize_simcoll_file(fname):
    df, meta = read_simcoll_file(fname)

    sum_flux = df["flux"].sum()

    sum_flux_over_v3 = (df["flux"] / df["speed3"]).sum()

    ratio = sum_flux_over_v3 / sum_flux if sum_flux != 0 else np.nan

    time_yyyy_frac = meta.get("time_yyyy_frac", np.nan)

    if np.isfinite(time_yyyy_frac):
        doy = yyyy_frac_to_doy(time_yyyy_frac)
    else:
        doy = np.nan

    fit = fit_speed2_double_von_mises(df)

    return {
        "file": os.path.basename(fname),
        "repoint": meta.get("repoint", np.nan),
        "pivot_angle": meta.get("delta_Ax", np.nan),
        "time_yyyy_frac": meta.get("time_yyyy_frac", np.nan),
        "doy": doy,
        "alpha_ecl": meta.get("alpha_ecl", np.nan),
        "delta_Ecl": meta.get("delta_Ecl", np.nan),

        "sum_flux": sum_flux,
        "sum_flux_over_v3": sum_flux_over_v3,
        "sum_flux_over_v3_div_sum_flux": ratio,

        "speed2_fit_form": FIT_FORM,

        "speed2_vm_A1": fit["A1"],
        "speed2_vm_A1_err": fit["A1_err"],
        "speed2_vm_mu1_deg": fit["mu1_deg"],
        "speed2_vm_mu1_deg_err": fit["mu1_deg_err"],
        "speed2_vm_kappa1": fit["kappa1"],
        "speed2_vm_kappa1_err": fit["kappa1_err"],
        "speed2_vm_peak1_height": fit["peak1_height"],

        "speed2_vm_A2": fit["A2"],
        "speed2_vm_A2_err": fit["A2_err"],
        "speed2_vm_mu2_deg": fit["mu2_deg"],
        "speed2_vm_mu2_deg_err": fit["mu2_deg_err"],
        "speed2_vm_kappa2": fit["kappa2"],
        "speed2_vm_kappa2_err": fit["kappa2_err"],
        "speed2_vm_peak2_height": fit["peak2_height"],

        "speed2_vm_rms": fit["rms"],
        "speed2_vm_R": fit["R"],
        "speed2_vm_R2": fit["R2"],
    }


def write_fit_info_file(outdir):
    fit_info_file = outdir / "speed2_double_von_mises_fit_info.csv"

    with open(fit_info_file, "w") as f:
        f.write("# Double von Mises fit applied to speed2 column as a function of spin angle.\n")
        f.write(f"# fit_form,{FIT_FORM}\n")
        f.write("# theta is spin angle in degrees.\n")
        f.write("# mu1_deg and mu2_deg are angular centers in degrees.\n")
        f.write("# kappa1 and kappa2 are concentration parameters; larger kappa means narrower peak.\n")
        f.write("# A1 and A2 are scale factors, not literal peak heights.\n")
        f.write("# Peak contribution height for each component is A*exp(kappa).\n")
        f.write("# Parameter uncertainties are 1-sigma estimates from sqrt(diag(covariance_matrix)) returned by scipy.optimize.curve_fit.\n")
        f.write("# R is the correlation coefficient between speed2 data and fitted model.\n")
        f.write("# R2 is R squared.\n")
        f.write("parameter,description\n")
        f.write("A1,scale factor of first von Mises component\n")
        f.write("A1_err,1-sigma uncertainty on A1\n")
        f.write("mu1_deg,center angle of first component in degrees\n")
        f.write("mu1_deg_err,1-sigma uncertainty on mu1_deg\n")
        f.write("kappa1,concentration/narrowness of first component\n")
        f.write("kappa1_err,1-sigma uncertainty on kappa1\n")
        f.write("peak1_height,A1*exp(kappa1)\n")
        f.write("A2,scale factor of second von Mises component\n")
        f.write("A2_err,1-sigma uncertainty on A2\n")
        f.write("mu2_deg,center angle of second component in degrees\n")
        f.write("mu2_deg_err,1-sigma uncertainty on mu2_deg\n")
        f.write("kappa2,concentration/narrowness of second component\n")
        f.write("kappa2_err,1-sigma uncertainty on kappa2\n")
        f.write("peak2_height,A2*exp(kappa2)\n")
        f.write("rms,root-mean-square residual of fit\n")
        f.write("R,correlation coefficient between data and fit\n")
        f.write("R2,correlation coefficient squared\n")

    print(f"Wrote {fit_info_file}")


def summarize_directory(
    indir,
    pattern="simColl6d_*.dat",
    outdir="simcoll_results",
    pivot_angles_to_write=None,
):
    if pivot_angles_to_write is None:
        pivot_angles_to_write = [75.0, 90.0, 105.0]

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    write_fit_info_file(outdir)

    files = sorted(glob.glob(os.path.join(indir, pattern)))

    rows = []

    for fname in files:
        rows.append(summarize_simcoll_file(fname))

    out = pd.DataFrame(rows)

    if len(out) > 0:
        out = out.sort_values(["pivot_angle", "repoint"], na_position="last")

    master_file = outdir / "simcoll_sums_all_pivots.csv"
    out.to_csv(master_file, index=False)

    for pivot in pivot_angles_to_write:
        this = out[np.isclose(out["pivot_angle"], pivot, rtol=0, atol=1e-6)]

        pivot_tag = f"{pivot:g}".replace(".", "p")
        outfile = outdir / f"simcoll_sums_pivot{pivot_tag}.csv"

        this.to_csv(outfile, index=False)

        print(f"Wrote {outfile} with {len(this)} rows")

    print(f"Wrote {master_file} with {len(out)} rows")

    return out


if __name__ == "__main__":

    indir = "../input_m1a_pr_helium"

    outdir = Path("output")

    outdir.mkdir(parents=True, exist_ok=True)

    dfout = summarize_directory(
        indir,
        pattern="simColl6d_*.dat",
        outdir="./output",
        pivot_angles_to_write=PIVOT_ANGLES_TO_WRITE,
    )

    print(dfout)
    print()
    print("Wrote simcoll summary files")