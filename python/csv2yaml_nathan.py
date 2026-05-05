#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 18 2026
@author: hafijulislam

"""

import csv
import os
from datetime import datetime, timedelta, timezone

hy_esa_energy = {
    1: 0.02,
    2: 0.03,
    3: 0.06,
    4: 0.11,
    5: 0.20,
    6: 0.41,
    7: 0.79
}

ox_esa_energy = {
    1: 0.02,
    2: 0.04,
    3: 0.07,
    4: 0.14,
    5: 0.27,
    6: 0.59,
    7: 1.14
}
label_map = {
    "cnts": "Counts",
    "expo": "Exposure Time (s)",
    "stbg": "Signal/Background",
    "svar": "Variance Signal/Background",
    "flux": "Intensity (cm -2 s -1 sr -1 keV -1)",
    "fvar": "Variance Intensity (cm -4 s -2 sr -2 keV -2)",
    "fvto": "VarTotal Intensity (cm -4 s -2 sr -2 keV -2)",
    "rate": "Rate (s -1)",
    "rvar": "Variance Rate (s -2)",
    "fser": "Sys Int Uncertainty (cm -2 s -1 sr -1 keV -1)"
}


def latest_monday_tag():
    today = datetime.now(timezone.utc)
    days_since_monday = today.weekday()
    last_monday = today - timedelta(days=days_since_monday)
    year = last_monday.strftime('%Y')
    year_short = last_monday.strftime("%y")
    doy = last_monday.strftime("%j")
    end_day = last_monday.strftime('%Y%m%d')
    return year, end_day, f"v{year_short}DOY{doy}"


def csv_to_map_yaml(
    csv_file,
    output_file,
    energy_value="56",
    epoch_date="2025-11-08T00:00:00+00:00",
    epoch_time_delta=259200,
    map_year="2026",
    uniqueness_index=0,
    label="Flux",
    pivot="90",
    metadata="flux",
    species="H",
):
    """Write YAML-like output from CSV. metadata includes full descriptor (e.g. flux, rate+expo)."""
    data_rows = []
    with open(csv_file, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            formatted_row = [
                f"{float(x):.3E}" if float(x) != 0 else "0.000E+00"
                for x in row
            ]
            data_rows.append(formatted_row)

    _, _, tag = latest_monday_tag()

    with open(output_file, "w") as f:
        f.write(
            "map_information: {"
            f"energy_value: '{energy_value}', "
            "energy_unit: KeV, "
            f"epoch_date: '{epoch_date}', "
            f"epoch_time_delta: {epoch_time_delta}, "
            f"map_display_text: '{map_year}', "
            "detailed_display_text: 'IMAP-Lo initial maps', "
            f"uniqueness_index: {uniqueness_index}, "
            f"color_bar_title: {label}, "
            "mask_value: 0}\n"
        )
        f.write(
            "metadata: {"
            f"name: IMAP-Lo SC Frame Pivot {pivot} {species} maps_{tag} {metadata}, "
            "SMOOTHING_LEVEL: 0.0, "
            "Descriptor: IMAP-Lo, "
            "Mission_group: IMAP}\n"
        )
        f.write("data:\n")
        for row in data_rows:
            f.write("- [" + ", ".join(row) + "]\n")


# --- Config ---
species_list = ["H", "O"] 
year, end_day, tag = latest_monday_tag()
start_day = '20251108'
sec_layr = f'{start_day}_{end_day}_lo_{year}'

# 1st layer suffix -> 2nd layer descriptor
# C=cnts, F=flux (variance view), R=rate (variance view), B=stbg, E=expo, V=fvar, U=rvar, W=fvto (as in Wotal)
DATA_TYPES = {
    "C": "cnts",
    "F": "flux",
    "R": "rate",
    "B": "stbg",
    "E": "expo",
    "V": "fvar",
    "U": "rvar",
    "S": "fser",
    "X": "flxu"
}
for species in species_list:
    for pp in [75, 90, 105]:
        pp_str = f"p{pp:03d}"
        if species=="H":
            work_dir1 = f'../3S2_l1b_quickmaps/outdir/pivot_{pp}/maps'
            base_cava = '../3S2_l1b_quickmaps/outdir/cava'
        else:
            work_dir1 = f'../3S3_l1b_Oxy_quickmaps/outdir/pivot_{pp}/maps'
            base_cava = '../3S3_l1b_Oxy_quickmaps/outdir/cava'
        

        # Create all 1st-layer dirs: cava_txt_lo_H_{tag}{pp_str}{suffix}
        yaml_dirs = {}
        for suffix, desc in DATA_TYPES.items():
            d = f'{base_cava}/cava_txt_lo_{species}_{tag}{pp_str}{suffix}/{sec_layr}_{desc}'
            yaml_dirs[desc] = d
            os.makedirs(d, exist_ok=True)

        for esa in range(1, 8):
            if species=="H":
                energy = hy_esa_energy[esa]
            else:
                energy = ox_esa_energy[esa]
            print(pp, esa)

            # --- Shared exposure (used by flux, rate, stbg, func, runc, cunc) ---
            expo_file = os.path.join(work_dir1, f"map_expo_esa{esa}.csv")
            if not os.path.exists(expo_file):
                continue

            # --- Flux variance view: "flux" and "variance" both use variance map; expo is exposure ---
            flux_file = os.path.join(work_dir1, f"map_flux_esa{esa}.csv")
            fvar_file = os.path.join(work_dir1, f"map_fvar_esa{esa}.csv")
            if os.path.exists(flux_file) and os.path.exists(fvar_file) and os.path.exists(expo_file):
                for csv_src, stem, lbl in [
                    (flux_file, "flux", label_map["flux"]),
                    (expo_file, "exposure", label_map["expo"]),
                    (fvar_file, "variance", label_map["fvar"]),
                ]:
                    if os.path.exists(csv_src):
                        out = os.path.join(yaml_dirs["flux"], f"IMAPLo-{energy}KeV-{stem}.txt")
                        csv_to_map_yaml(csv_file=csv_src, output_file=out, energy_value=energy, map_year=year,
                                        label=lbl, pivot=pp, metadata="flux", species=species)
                        
            # --- New (5/1/2026) Flux variance total: This total variance includes statistical and systematic error
            fvto_file = os.path.join(work_dir1, f"map_fvto_esa{esa}.csv")
            if os.path.exists(flux_file) and os.path.exists(fvto_file) and os.path.exists(expo_file):
                for csv_src, stem, lbl in [
                    (flux_file, "flux", label_map["flux"]),
                    (expo_file, "exposure", label_map["expo"]),
                    (fvto_file, "variance", label_map["fvto"]),
                ]:
                    if os.path.exists(csv_src):
                        out = os.path.join(yaml_dirs["flxu"], f"IMAPLo-{energy}KeV-{stem}.txt")
                        csv_to_map_yaml(csv_file=csv_src, output_file=out, energy_value=energy, map_year=year,
                                        label=lbl, pivot=pp, metadata="fvto", species=species)

            # --- Rate variance view: "flux" and "variance" both use variance map; expo is exposure ---
            rate_file = os.path.join(work_dir1, f"map_rate_esa{esa}.csv")
            rvar_file = os.path.join(work_dir1, f"map_rvar_esa{esa}.csv")
            if os.path.exists(rate_file) and os.path.exists(rvar_file) and os.path.exists(expo_file):
                for csv_src, stem, lbl in [
                    (rate_file, "flux", label_map["rate"]),
                    (expo_file, "exposure", label_map["expo"]),
                    (rvar_file, "variance", label_map["rvar"]),
                ]:
                    if os.path.exists(csv_src):
                        out = os.path.join(yaml_dirs["rate"], f"IMAPLo-{energy}KeV-{stem}.txt")
                        csv_to_map_yaml(csv_file=csv_src, output_file=out, energy_value=energy, map_year=year,
                                        label=lbl, pivot=pp, metadata="rate", species=species)

            # --- Cnts: cnts + expo + variance (use cnts as variance if no cnts_var) ---
            cnts_file = os.path.join(work_dir1, f"map_cnts_esa{esa}.csv")
            cnts_var_src = cnts_file
            if os.path.exists(cnts_file):
                for csv_src, stem, lbl in [
                    (cnts_file, "flux", label_map["cnts"]),
                    (expo_file, "exposure", label_map["expo"]),
                    (cnts_var_src, "variance", label_map["cnts"]),
                ]:
                    out = os.path.join(yaml_dirs["cnts"], f"IMAPLo-{energy}KeV-{stem}.txt")
                    csv_to_map_yaml(csv_file=csv_src, output_file=out, energy_value=energy, map_year=year,
                                    label=lbl, pivot=pp, metadata="cnts", species=species)

            # --- Stbg (B): stbg as flux, expo, stbg variance from precomputed svar map ---
            stbg_file = os.path.join(work_dir1, f"map_stbg_esa{esa}.csv")
            svar_file = os.path.join(work_dir1, f"map_svar_esa{esa}.csv")
            if os.path.exists(stbg_file):
                for csv_src, stem, lbl in [
                    (stbg_file, "flux", label_map["stbg"]),
                    (expo_file, "exposure", label_map["expo"]),
                    (svar_file, "variance", label_map["svar"]),
                ]:
                    out = os.path.join(yaml_dirs["stbg"], f"IMAPLo-{energy}KeV-{stem}.txt")
                    csv_to_map_yaml(csv_file=csv_src, output_file=out, energy_value=energy, map_year=year,
                                    label=lbl, pivot=pp, metadata="stbg", species=species)

            # --- Expo (E): expo as flux, expo as exposure, expo variance (no dedicated file yet) ---
            if os.path.exists(expo_file):
                for csv_src, stem, lbl in [
                    (expo_file, "flux", label_map["expo"]),
                    (expo_file, "exposure", label_map["expo"]),
                    (expo_file, "variance", label_map["expo"]),
                ]:
                    out = os.path.join(yaml_dirs["expo"], f"IMAPLo-{energy}KeV-{stem}.txt")
                    csv_to_map_yaml(csv_file=csv_src, output_file=out, energy_value=energy, map_year=year,
                                    label=lbl, pivot=pp, metadata="expo", species=species)

            # Standalone variance products (like cunc): func (from flux variance) and runc (from rate variance)
            if os.path.exists(fvar_file):
                for csv_src, stem, lbl in [
                    (fvar_file, "flux", label_map["fvar"]),
                    (expo_file, "exposure", label_map["expo"]),
                    (fvar_file, "variance", label_map["fvar"]),
                ]:
                    if os.path.exists(csv_src):
                        out = os.path.join(yaml_dirs["fvar"], f"IMAPLo-{energy}KeV-{stem}.txt")
                        csv_to_map_yaml(csv_file=csv_src, output_file=out, energy_value=energy, map_year=year,
                                        label=lbl, pivot=pp, metadata="fvar", species=species)
                        
            fser_file = os.path.join(work_dir1, f"map_fser_esa{esa}.csv")            
            if os.path.exists(fser_file):
                for csv_src, stem, lbl in [
                    (fser_file, "flux", label_map["fser"]),
                    (expo_file, "exposure", label_map["expo"]),
                    (fvar_file, "variance", label_map["fvar"]),
                ]:
                    if os.path.exists(csv_src):
                        out = os.path.join(yaml_dirs["fser"], f"IMAPLo-{energy}KeV-{stem}.txt")
                        csv_to_map_yaml(csv_file=csv_src, output_file=out, energy_value=energy, map_year=year,
                                        label=lbl, pivot=pp, metadata="fser", species=species)

            if os.path.exists(rvar_file):
                for csv_src, stem, lbl in [
                    (rvar_file, "flux", label_map["rvar"]),
                    (expo_file, "exposure", label_map["expo"]),
                    (rvar_file, "variance", label_map["rvar"]),
                ]:
                    if os.path.exists(csv_src):
                        out = os.path.join(yaml_dirs["rvar"], f"IMAPLo-{energy}KeV-{stem}.txt")
                        csv_to_map_yaml(csv_file=csv_src, output_file=out, energy_value=energy, map_year=year,
                                        label=lbl, pivot=pp, metadata="rvar", species=species)