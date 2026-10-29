#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 15 18:14:16 2026

@author: hafijulislam
"""

import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from scipy.spatial.transform import Rotation as R
from matplotlib.colors import LogNorm
import new_patch_arc2 as patch

PI = np.pi

def sph_to_cart(lat, lon):
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    x = np.cos(lat_rad) * np.cos(lon_rad)
    y = np.cos(lat_rad) * np.sin(lon_rad)
    z = np.sin(lat_rad)
    return np.array([x, y, z])

def rotation_matrix_to_center(new_colat0, new_lon0):
    # Step 1: rotate around Z axis by -lon0
    r1 = R.from_euler('z', -new_lon0, degrees=True)
    # Step 2: rotate around Y axis by 90-lat0
    r2 = R.from_euler('y', 90-new_colat0, degrees=True)
    # Combined rotation
    return r2 * r1

def inverse_rotation_matrix_to_center(rot, xyz_rot):
    """
    Apply inverse rotation to xyz_rot points.
    rot: scipy.spatial.transform.Rotation object used in forward rotation
    xyz_rot: shape (N,3)
    Returns xyz_orig (N,3)
    """
    return rot.inv().apply(xyz_rot)

esa_energy = {
    1: 0.016,
    2: 0.030,
    3: 0.056,
    4: 0.106,
    5: 0.200,
    6: 0.404,
    7: 0.787
}

label_map = {

    "rate": "Sputtering Corrected Rate (counts s$^{-1}$)",
    
    "sput_flux": "Sputtering Corrected Intensity (counts cm$^{-2}$ s$^{-1}$ sr$^{-1}$ keV$^{-1}$)",
    
    "boot_flux": "Bootstrapped Corrected Intensity (counts cm$^{-2}$ s$^{-1}$ sr$^{-1}$ keV$^{-1}$)",

    "rate_var": "Sputtering Corrected Rate Variance (counts$^{2}$ s$^{-2}$)",

    "flux_var": "Sputtering Corrected Intensity Variance (counts$^{2}$ cm$^{-4}$ s$^{-2}$ sr$^{-2}$ keV$^{-2}$)",

    "boot_var": "Bootstrapped Corrected Intensity Variance (counts$^{2}$ cm$^{-4}$ s$^{-2}$ sr$^{-2}$ keV$^{-2}$)"
}

for pp in [75,90,105]:   # 

    work_dir1 = f'./outdir/pivot_{pp}/maps'
    plot_dir = f'./outdir/pivot_{pp}/corrected_plots'

    os.makedirs(plot_dir, exist_ok=True)

    for esa in range(1,8):

        energy = esa_energy[esa] * 1000.0
        energy_str = f"{energy:.1f}"

        files = {

            "rate": f"map_rate_{esa}_Hy_sput_cor.csv",
            "sput_flux": f"map_flux_{esa}_Hy_sput_cor.csv",
            "boot_flux": f"map_flux_{esa}_Hy_boot_cor.csv",

            "rate_var": f"map_rate_{esa}_Hy_sput_var.csv",
            "flux_var": f"map_flux_{esa}_Hy_sput_var.csv",
            "boot_var": f"map_flux_{esa}_Hy_boot_var.csv"
        }

        for key, fname in files.items():

            filename = os.path.join(work_dir1, fname)

            if not os.path.exists(filename):
                continue

            data = np.loadtxt(filename, delimiter=',', skiprows=1)

            vmax = np.nanmax(data)
            if vmax == 0:
                vmax = 100

            vmin = vmax * 1e-3

            lat_center = 5.0
            lon_center = -105.0

            label = label_map[key]
            label = label + f"\nESA {esa}  (E = {energy_str} eV)"

            output = os.path.join(
                plot_dir,
                fname.replace(".csv",".png")
            )

            title = f"Pivot {pp}"

            print(pp, esa, key)

            patch.make_imap_lo_map(
                filename,
                lat_center,
                lon_center,
                vmin,
                vmax,
                output,
                label_colorbar=label,
                plot_title=title
            )















