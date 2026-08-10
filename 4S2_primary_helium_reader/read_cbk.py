import os
import re
import glob
import numpy as np
import pandas as pd
from pathlib import Path


PIVOT_ANGLES_TO_WRITE = [75.0, 90.0, 105.0]




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

    # fallback: get repoint/pivot from filename
    base = os.path.basename(fname)

    # repoint
    if "repoint" not in meta:
        m = re.search(r"repoint(\d+)", base)
        if m:
            meta["repoint"] = int(m.group(1))

    # yyyy.frac
    m = re.search(r"_(\d{4}\.\d+)_", base)
    if m:
        meta["time_yyyy_frac"] = float(m.group(1))

    # pivot angle
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

    # leap-year aware
    days_in_year = 366 if pd.Timestamp(f"{year}-12-31").dayofyear == 366 else 365

    return 1.0 + frac * days_in_year

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
    }


def summarize_directory(
    indir,
    pattern="simColl6d_*.dat",
    outdir="simcoll_results",
    pivot_angles_to_write=None,
):
    from pathlib import Path

    if pivot_angles_to_write is None:
        pivot_angles_to_write = [75.0, 90.0, 105.0]

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    files = sorted(glob.glob(os.path.join(indir, pattern)))

    rows = []
    for fname in files:
        rows.append(summarize_simcoll_file(fname))

    out = pd.DataFrame(rows)

    out = out.sort_values(["pivot_angle", "repoint"], na_position="last")

    # One master file with everything
    master_file = outdir / "simcoll_sums_all_pivots.csv"
    out.to_csv(master_file, index=False)

    # One file per requested pivot angle
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
        pivot_angles_to_write=PIVOT_ANGLES_TO_WRITE
    )

    print(dfout)
    print()
    print("Wrote simcoll_sums.csv")