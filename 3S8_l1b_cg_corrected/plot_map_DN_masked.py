#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import os
from pathlib import Path
import new_patch_arc2 as patch
import pandas as pd

esa_energy = {
    1: 0.016, 2: 0.030, 3: 0.056, 4: 0.106,
    5: 0.200, 6: 0.404, 7: 0.787, 8: 1.821
}

label_map = {
    "cnts": "Counts",
    "rate": "Rate (counts s$^{-1}$)",
    "backrate": "Rate (counts s$^{-1}$)",
    "expo": "Exposure Time (sec)",
    "stbg": "Signal/Ubiq-Bkgd",
    "func": "Unc Intensity",
    "fser": "Flux Sys Uncertainty",
    "fvar": "Variance Intensity",
    "fvto": "Variance Total",
    "runc": "Unc Rate",
    "rvar": "Variance Rate",
    "flux": "Intensity (counts cm$^{-2}$ s$^{-1}$ sr$^{-1}$ keV$^{-1}$)",
    "cosalpha": "cos(alpha), alpha angle between Ram and Boresight",
}


def finite_positive_max(data):
    vals = data[np.isfinite(data) & (data > 0)]
    if vals.size == 0:
        return None
    return np.nanmax(vals)


def finite_max_abs(data):
    vals = data[np.isfinite(data)]
    if vals.size == 0:
        return None
    return np.nanmax(np.abs(vals))


def get_vmin_vmax(data, tt, esa):
    """
    Return safe vmin/vmax even when map contains NaNs.
    For log maps, require positive finite values.
    """

    if tt == "expo":
        vmax = finite_positive_max(data)
        if vmax is None:
            return None, None
        return 1e-1, vmax

    if tt == "cosalpha":
        vmax = finite_max_abs(data)
        if vmax is None or vmax <= 0:
            return None, None
        return -vmax, vmax

    # Log-scaled products
    vmax = finite_positive_max(data)
    if vmax is None:
        return None, None

    if esa in [3, 4]:
        vmin = vmax * 1e-4
    elif esa in [1, 2]:
        vmin = vmax * 1e-3
    else:
        vmin = vmax * 1e-2

    # Guard against bad LogNorm limits
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin <= 0 or vmax <= vmin:
        return None, None

    return vmin, vmax


# MAIN

lat_center = 5.0
lon_center = -105.0

# products_to_plot = ["flux"]
products_to_plot = [
     "cgflux", "cgfunc", "cgfvar" 
 ]

for pp in [75, 90, 105]:

    work_dir = Path(f"./outdir/pivot_{pp}/masked_maps")
    plot_dir = Path(f"./outdir/pivot_{pp}/masked_plots")
    plot_dir.mkdir(parents=True, exist_ok=True)

    for esa in range(1, 8):
        print(f"ESA {esa}")

        for tt in products_to_plot:

            # Adjust this if your masked files have different names
            filename = work_dir / f"map_{tt}_esa{esa}.csv"

            if not filename.exists():
                print(f"  SKIP missing file: {filename}")
                continue

            # data = np.loadtxt(filename, delimiter=",", skiprows=1)
            df = pd.read_csv(filename)
            data = df.to_numpy()

            if not np.any(np.isfinite(data)):
                print(f"  SKIP {tt} ESA{esa}: all values are NaN")
                continue

            vmin, vmax = get_vmin_vmax(data, tt, esa)

            if vmin is None or vmax is None:
                print(f"  SKIP {tt} ESA{esa}: no valid plotting range")
                continue

            output = plot_dir / f"map_{tt}_esa{esa}.png"

            label = label_map.get(tt, tt)
            energy_ev = esa_energy[esa] * 1000.0
            label = label + f" [ECLIPJ2000] at ESA (eV) = {energy_ev:.2f}"

            title = f"Pivot:{pp}"

            print(f"  plotting {tt} ESA{esa}: vmin={vmin:.3e}, vmax={vmax:.3e}")

            patch.make_imap_lo_map(
                    str(filename),
                    lat_center,
                    lon_center,
                    vmin,
                    vmax,
                    str(output),
                    label_colorbar=label,
                    plot_title=title,
                )