#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 25 17:06:47 2026

@author: hafijulislam
"""

import csv
import os
from datetime import datetime, timedelta, timezone

esa_energy = {
    1: 16,
    2: 30,
    3: 56,
    4: 106,
    5: 200,
    6: 404,
    7: 787
}

label_map = {
    "cnts": "Counts",
    "rate": "Rate (#/s)",
    "backrate": "Rate (#/s)",
    "expo": "Exposure Time (s)",
    "stbg": "Signal/Ubiq-Bkgd",
    "fser": "Sys Unc Intensity",
    "func": "Unc Intensity",
    "fvar": "Variance Intensity (#/cm4 s2 sr2 keV2)",
    "runc": "Unc Rate",
    "rvar": "Variance Rate (#/s2)",
    "flux": "Intensity (#/cm2 s sr keV)"
}


def latest_monday_tag():

    today = datetime.now(timezone.utc)

    # Monday = 0, Sunday = 6
    days_since_monday = today.weekday()
    last_monday = today - timedelta(days=days_since_monday)

    year = last_monday.strftime('%Y')
    year_short = last_monday.strftime("%y")
    doy = last_monday.strftime("%j")
    
    end_day = last_monday.strftime('%Y%m%d')

    return year,end_day,f"v{year_short}DOY{doy}"

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
    metadata="flux"
):
    data_rows = []


    with open(csv_file, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)  # 10–59, not used
        for row in reader:
            formatted_row = [
                f"{float(x):.3E}" if float(x) != 0 else "0.000E+00"
                for x in row
            ]
            data_rows.append(formatted_row)
            
    _,_,tag = latest_monday_tag()

    # ----------------------------
    # Write YAML-like output
    # ----------------------------
    with open(output_file, "w") as f:
        f.write(
            "map_information: {"
            f"energy_value: '{energy_value}', "
            "energy_unit: eV, "
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
            f"name: IMAP-Lo SC Frame Pivot {pivot} H maps_{tag} {metadata}, "
            "SMOOTHING_LEVEL: 0.0, "
            "Descriptor: IMAP-Lo, "
            "Mission_group: IMAP}\n"
        )

        f.write("data:\n")
        for row in data_rows:
            f.write("- [" + ", ".join(row) + "]\n")

year,end_day,tag = latest_monday_tag()
start_day = '20251108'
sec_layr = f'{start_day}_{end_day}_lo_{year}'

for pp in [75,90,105]:
    if pp == 75:
        pp_str = 'p075'
    if pp == 90:
        pp_str = 'p090'
    if pp == 105:
        pp_str = 'p105'
    work_dir1 = f'./outdir/pivot_{pp}/maps'
    # yaml_dir_flux = f'./outdir/pivot_{pp}/yaml/cava_txt_lo_H_{tag}{pp_str}F/{sec_layr}_flux'
    # yaml_dir_rate = f'./outdir/pivot_{pp}/yaml/cava_txt_lo_H_{tag}{pp_str}R/{sec_layr}_rate'
    # yaml_dir_cnts = f'./outdir/pivot_{pp}/yaml/cava_txt_lo_H_{tag}{pp_str}C/{sec_layr}_cnts'
    
    yaml_dir_flux = f'./outdir/cava/cava_txt_lo_H_{tag}{pp_str}F/{sec_layr}_flux'
    yaml_dir_rate = f'./outdir/cava/cava_txt_lo_H_{tag}{pp_str}R/{sec_layr}_rate'
    yaml_dir_cnts = f'./outdir/cava/cava_txt_lo_H_{tag}{pp_str}C/{sec_layr}_cnts'
    
    os.makedirs(yaml_dir_flux, exist_ok=True)
    os.makedirs(yaml_dir_rate, exist_ok=True)
    os.makedirs(yaml_dir_cnts, exist_ok=True)
    
    for esa in range(1,8):
        print(pp,esa)
        for tt in ["expo","rate","flux","fvar","fser","rvar","cnts"]:#,"stbg","func","runc",,"rvar"]:
                filename = os.path.join(work_dir1, f"map_{tt}_esa{esa}.csv")
                energy = esa_energy[esa]
                label = label_map[tt]
                base_filename = os.path.splitext(os.path.basename(filename))[0]
                
                if tt=='expo':
                    tt='exposure'
                    outputs = [ os.path.join(yaml_dir_rate, f"IMAPLo-{energy}ev-{tt}.txt"),
                                os.path.join(yaml_dir_flux, f"IMAPLo-{energy}ev-{tt}.txt") ] 
                if tt=='cnts':
                    outputs = [ os.path.join(yaml_dir_cnts, f"IMAPLo-{energy}ev-flux.txt"),
                                os.path.join(yaml_dir_cnts, f"IMAPLo-{energy}ev-exposure.txt"), 
                                os.path.join(yaml_dir_cnts, f"IMAPLo-{energy}ev-variance.txt")] 
                
                if tt=="rvar":
                    tt='variance'
                    outputs = [ os.path.join(yaml_dir_rate, f"IMAPLo-{energy}ev-{tt}.txt") ]
                    
                if tt=="fvar":
                    tt='variance'
                    outputs = [ os.path.join(yaml_dir_flux, f"IMAPLo-{energy}ev-{tt}.txt") ]
                
                if tt=="fser":
                    outputs = [ os.path.join(yaml_dir_flux, f"IMAPLo-{energy}ev-{tt}.txt") ]
                    
                if tt=="flux":
                    tt='flux'
                    outputs = [ os.path.join(yaml_dir_flux, f"IMAPLo-{energy}ev-{tt}.txt") ]
                    
                if tt =='rate':
                    tt='flux'       
                    outputs = [ os.path.join(yaml_dir_rate, f"IMAPLo-{energy}ev-{tt}.txt") ]
                
                for output in outputs:
                    name = output
                    fst_str = name.split('/')[-2]
                    des = fst_str.split('_')[-1]
                    csv_to_map_yaml(
                        csv_file=filename,
                        output_file=output,
                        energy_value=energy,
                        map_year=year,
                        label=label,
                        pivot=pp,
                        metadata=des
                    )
