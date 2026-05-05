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
    7: 0.787,
    8: 1.821
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
        "flux": "Intensity (counts cm$^{-2}$ s$^{-1}$ sr$^{-1}$ keV$^{-1}$)"
    }

# MAIN 

for pp in [75,90,105]:
    work_dir1 = f'./outdir/pivot_{pp}/maps'
    plot_dir = f'./outdir/pivot_{pp}/plots'
    os.makedirs(plot_dir, exist_ok=True)
    
    for esa in range(1,8):
        print(esa)
        for tt in ["expo","rate","flux","cnts","fser","func","runc","fvar","fvto","rvar","stbg"]:
                filename = os.path.join(work_dir1, f"map_{tt}_esa{esa}.csv")
                data = np.loadtxt(filename, delimiter=',', skiprows=1)

                base_filename = os.path.splitext(os.path.basename(filename))[0]
                output = os.path.join(plot_dir, f"map_{tt}_esa{esa}.png")
                print(tt)

                if tt =="expo":
                    vmax = np.max(data)
                    vmin = 1e-1

                if tt in ["cnts", "rate", "flux", "fvar", "fvto", "fser", "stbg", "func", "runc", "rvar"]:
                    if esa==5:
                        vmax = np.max(data)
                        vmin = vmax * 1e-2
                    elif esa==4 or esa==3:
                        vmax = np.max(data)
                        vmin = vmax * 1e-4
                    elif esa==1 or esa==2:
                        vmax = np.max(data)
                        vmin = vmax * 1e-3
                    elif esa==6:
                        vmax = np.max(data)
                        vmin = vmax * 1e-2
                    else:
                        vmax = np.max(data)
                        vmin = vmax * 1e-2

                lat_center = 5.0 
                lon_center = -105.0

                label = label_map[tt]
    #                       "Intensity (counts cm$^{-2}$ s$^{-1}$ sr$^{-1}$ keV$^{-1}$)")
                value = esa_energy[esa] * 1000.0
                s = f"{value:.2f}"
                label = label + f'[ECLIPJ2000] at ESA (eV) = {s}'
#                print(label)
                title = f'Pivot:{pp}'
                patch.make_imap_lo_map(filename, lat_center, lon_center, vmin, vmax,output,label_colorbar=label,plot_title=title)



















