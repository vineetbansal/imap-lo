#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan  3 21:04:46 2026

@author: hafijulislam
"""

import os
import glob
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# -----------------------------
# Configuration
# -----------------------------

# -----------------------------
# Helper: infer file type
# -----------------------------
def infer_file_type(filename):
    name = filename.lower()
    for key in TYPE_MAP:
        if key in name:
            return key
    return "unknown"

# -----------------------------
# Header builder
# -----------------------------
def build_header(file_type, hmin, hmax):
    now = datetime.now().strftime("%a %b %d %H:%M:%S %Y")

    meta = TYPE_MAP.get(
        file_type,
        {"h_title": "Unknown", "desc": "unknown"}
    )

    header_lines = [
        "27:30x60:-5.0x-5.0:7x6:0:9",
        "",
        now,
        "",
        "flux_translate",
        "",
        " -s matrix",
        "",
        " -0 dec (addresses incr. downwards)",
        " -1 ra (addresses incr. left->right)",
        "",
        f" h_min={hmin:.8f} h_max={hmax:.8f} h_title='{meta['h_title']}'",
        " min_0=-90 max_0=90 num_0=30 title_0='Dec (deg)'",
        " min_1=0 max_1=360 num_1=60 title_1='R.A. (deg)'",
        f" desc=\"'{meta['desc']}'\"",
        " skyframe=ECLIPJ2000 posframe=J2000",
        "",
        " chat=0 smearspread='0/0/0' calc='0/0/0'",
        " frame_epoch=914561779.587 resp_class=lo_triple "
        "zaxis_ra_deg=+274.476346 zaxis_dec_deg=-22.782473",
        " ram_ra_deg=+186.7725 ram_dec_deg=-3.2847 "
        "mtype_list='40' energy_list='21,41'",
        " check_mt_list='40' check_species='20' rate_factor='1000' "
        "e_nominal='0.015'",
        "",
        "",
        "",
        "",
        "",
        ""
    ]

    return ["# " + line for line in header_lines[:27]]

for pp in [75,90,105]:
    
    INPUT_DIR = f'./outdir/pivot_{pp}/maps'
    OUTPUT_DIR = f'./outdir/pivot_{pp}/txt_maps/'

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Mapping file type → header description
    TYPE_MAP = {
        "cats": {
            "h_title": "Total Counts",
            "desc": "counts"
        },
        "expo": {
            "h_title": "Exposure Time",
            "desc": "exposure (s)"
        },
        "flux": {
            "h_title": "Flux",
            "desc": "flux (1 / cm^2 s sr keV)"
        },
        "rate": {
            "h_title": "Rate",
            "desc": "rate ( 1/s)"
        }
    }
    
    
    # -----------------------------
    # Batch processing
    # -----------------------------
    csv_files = Path(INPUT_DIR).glob("*.csv")
    
    input_dir = Path(INPUT_DIR)
    
    # if not csv_files:
    #     raise RuntimeError(f"No CSV files found in {INPUT_DIR}")
    
    for csv_file in input_dir.glob("*.csv"):

        fname = os.path.basename(csv_file)
    
        # Infer type from filename
        file_type = infer_file_type(fname)
    
        # Read CSV
        df = pd.read_csv(csv_file)
    
        data = df.to_numpy(dtype=float)
    
        if data.shape != (30, 60):
            raise Warning(f"{fname}: Expected 30x60, got {data.shape}")
            continue
    
        # Compute h_min / h_max
        h_min = np.nanmin(data)
        h_max = np.nanmax(data)
    
        # Build header
        header = build_header(file_type, h_min, h_max)
    
        # Output filename
        out_name = os.path.splitext(fname)[0] + ".txt"
        out_path = os.path.join(OUTPUT_DIR, out_name)
    
        # with open(f'/Users/hafijulislam/UNH/csv_to_isoc/converted/map_cnts_esa{esa}.txt', "w") as f:
        with open(out_path, "w") as f:    
            f.write("\n".join(header) + "\n")
            for row in data:
                f.write("\t".join(f"{val:.6e}" for val in row) + "\n")
    
    print(f"Converted Maps for Pivot {pp}")
