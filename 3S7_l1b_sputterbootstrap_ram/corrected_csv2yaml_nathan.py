#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import csv
import os
from datetime import datetime, timedelta, timezone

# Use same ESA energies as csv2yaml_extended.py (in keV)
esa_energy = {
    1: 0.02,
    2: 0.03,
    3: 0.06,
    4: 0.11,
    5: 0.20,
    6: 0.41,
    7: 0.79,
}

label_map = {
    "flux": "Intensity (cm -2 s -1 sr -1 keV -1)",
    "fser": "Systematic Uncertainty cm -2 s -1 sr -1 keV -1)",
    "fsel": "Lower Systematic Uncertainty cm -2 s -1 sr -1 keV -1)",
    "fseu": "Upper Systematic Uncertainty cm -2 s -1 sr -1 keV -1)",
    "rate": "Rate (s -1)",
    "expo": "Exposure Time (s)",
    "fvar": "Variance Intensity (cm -4 s -2 sr -2 keV -2)",
    "rvar": "Variance Rate (s -2)"
}


def latest_monday_tag():
    """Return (year, end_yyyymmdd, version_tag) using last Monday in UTC."""
    today = datetime.now(timezone.utc)
    days_since_monday = today.weekday()
    last_monday = today - timedelta(days=days_since_monday)
    year = last_monday.strftime("%Y")
    year_short = last_monday.strftime("%y")
    doy = last_monday.strftime("%j")
    end_day = last_monday.strftime("%Y%m%d")
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
    """Write YAML-like output from a CSV matrix."""
    data_rows = []
    with open(csv_file, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)  # ignore header row
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
            "detailed_display_text: 'IMAP-Lo corrected maps', "
            f"uniqueness_index: {uniqueness_index}, "
            f"color_bar_title: {label}, "
            "mask_value: 0}\n"
        )
        f.write(
            "metadata: {"
            f"name: IMAP-Lo SC Frame Pivot {pivot} {species}corr maps_{tag} {metadata}, "
            "SMOOTHING_LEVEL: 0.0, "
            "Descriptor: IMAP-Lo, "
            "Mission_group: IMAP}\n"
        )
        f.write("data:\n")
        for row in data_rows:
            f.write("- [" + ", ".join(row) + "]\n")


# --- Config for corrected maps ---
species = "H"  # corrected maps are for H
year, end_day, tag = latest_monday_tag()
start_day = "20251108"
sec_layr = f"{start_day}_{end_day}_lo_{year}"

# 1st layer suffix -> 2nd layer descriptor
# S = sputtered flux, R = sputtered rate, B = bootstrapped flux
DATA_TYPES = [
    ("S", "sput_flux", "sput_flux"),
    ("R", "sput_rate", "sput_rate"),
    ("E", "sput_fser", "sput_fser"),
    ("D", "sput_fsel", "sput_fsel"),
    ("G", "sput_fseu", "sput_fseu"),
    ("B", "boot_flux", "boot_flux"),
    ("U", "boot_fser", "boot_fser"),
    ("L", "boot_fsel", "boot_fsel"),
    ("T", "boot_fseu", "boot_fseu"),
]


for pp in [75, 90, 105]:
    pp_str = f"p{pp:03d}"

    # Corrected maps live under this pivot-specific directory
    work_dir = f"./outdir/pivot_{pp}/maps"

    # CAVA-like output directory colocated with corrected_maps
    base_cava = "./outdir/cava_corr"

    # Create all 1st-layer dirs: cava_txt_lo_Hcorr_{tag}{pp_str}{suffix}
    yaml_dirs = {}
    for suffix, _, desc in DATA_TYPES:
        d = (
            f"{base_cava}/cava_txt_lo_{species}corr_"
            f"{tag}{pp_str}{suffix}/{sec_layr}_{desc}"
        )
        yaml_dirs[desc] = d
        os.makedirs(d, exist_ok=True)

    for esa in range(1, 8):
        energy = esa_energy[esa]
        print(pp, esa)

        expo_file = os.path.join(work_dir, f"map_expo_esa{esa}.csv")
        if not os.path.exists(expo_file):
            print("fubar .. ")
            continue

        # Sputtered corrected flux (flux + expo + variance)
        sput_flux = os.path.join(work_dir, f"map_flux_{esa}_Hy_sput_cor.csv")
        sput_flux_var = os.path.join(work_dir, f"map_flux_{esa}_Hy_sput_var.csv")

        if os.path.exists(sput_flux) and os.path.exists(sput_flux_var):
            for csv_src, stem, lbl in [
                (sput_flux, "flux", label_map["flux"]),
                (expo_file, "exposure", label_map["expo"]),
                (sput_flux_var, "variance", label_map["fvar"]),
            ]:
                if os.path.exists(csv_src):
                    out = os.path.join(
                        yaml_dirs["sput_flux"],
                        f"IMAPLo-{energy}Kev-{stem}.txt",
                    )
                    csv_to_map_yaml(
                        csv_file=csv_src,
                        output_file=out,
                        energy_value=energy,
                        map_year=year,
                        label=lbl,
                        pivot=pp,
                        metadata="sput_flux",
                        species=species,
                    )

        # Sputtered corrected sys err (fser + expo + variance)
        sput_fser = os.path.join(work_dir, f"map_flux_{esa}_Hy_sput_unc.csv")
        sput_fser_var = os.path.join(work_dir, f"map_flux_{esa}_Hy_sput_var.csv")

        if os.path.exists(sput_fser) and os.path.exists(sput_fser_var):
            for csv_src, stem, lbl in [
                (sput_fser, "flux", label_map["fser"]),
                (expo_file, "exposure", label_map["expo"]),
                (sput_flux_var, "variance", label_map["fvar"]),
            ]:
                if os.path.exists(csv_src):
                    out = os.path.join(
                        yaml_dirs["sput_fser"],
                        f"IMAPLo-{energy}Kev-{stem}.txt",
                    )
                    csv_to_map_yaml(
                        csv_file=csv_src,
                        output_file=out,
                        energy_value=energy,
                        map_year=year,
                        label=lbl,
                        pivot=pp,
                        metadata="sput_fser",
                        species=species,
                    )

        # Sputtered corrected lower sys err (fsel + expo + variance)
        sput_fsel = os.path.join(work_dir, f"map_flux_{esa}_Hy_sput_unl.csv")
        sput_fsel_var = os.path.join(work_dir, f"map_flux_{esa}_Hy_sput_var.csv")

        if os.path.exists(sput_fsel) and os.path.exists(sput_fsel_var):
            for csv_src, stem, lbl in [
                (sput_fsel, "flux", label_map["fsel"]),
                (expo_file, "exposure", label_map["expo"]),
                (sput_flux_var, "variance", label_map["fvar"]),
            ]:
                if os.path.exists(csv_src):
                    out = os.path.join(
                        yaml_dirs["sput_fsel"],
                        f"IMAPLo-{energy}Kev-{stem}.txt",
                    )
                    csv_to_map_yaml(
                        csv_file=csv_src,
                        output_file=out,
                        energy_value=energy,
                        map_year=year,
                        label=lbl,
                        pivot=pp,
                        metadata="sput_fsel",
                        species=species,
                    )

        # Sputtered corrected upper sys err (fseu + expo + variance)
        sput_fseu = os.path.join(work_dir, f"map_flux_{esa}_Hy_sput_unu.csv")
        sput_fseu_var = os.path.join(work_dir, f"map_flux_{esa}_Hy_sput_var.csv")

        if os.path.exists(sput_fseu) and os.path.exists(sput_fseu_var):
            for csv_src, stem, lbl in [
                (sput_fseu, "flux", label_map["fseu"]),
                (expo_file, "exposure", label_map["expo"]),
                (sput_flux_var, "variance", label_map["fvar"]),
            ]:
                if os.path.exists(csv_src):
                    out = os.path.join(
                        yaml_dirs["sput_fseu"],
                        f"IMAPLo-{energy}Kev-{stem}.txt",
                    )
                    csv_to_map_yaml(
                        csv_file=csv_src,
                        output_file=out,
                        energy_value=energy,
                        map_year=year,
                        label=lbl,
                        pivot=pp,
                        metadata="sput_fseu",
                        species=species,
                    )

        # Sputtered corrected rate (rate + expo + variance)
        sput_rate = os.path.join(work_dir, f"map_rate_{esa}_Hy_sput_cor.csv")
        sput_rate_var = os.path.join(work_dir, f"map_rate_{esa}_Hy_sput_var.csv")

        if os.path.exists(sput_rate) and os.path.exists(sput_rate_var):
            for csv_src, stem, lbl in [
                (sput_rate, "flux", label_map["rate"]),
                (expo_file, "exposure", label_map["expo"]),
                (sput_rate_var, "variance", label_map["rvar"]),
            ]:
                if os.path.exists(csv_src):
                    out = os.path.join(
                        yaml_dirs["sput_rate"],
                        f"IMAPLo-{energy}Kev-{stem}.txt",
                    )
                    csv_to_map_yaml(
                        csv_file=csv_src,
                        output_file=out,
                        energy_value=energy,
                        map_year=year,
                        label=lbl,
                        pivot=pp,
                        metadata="sput_rate",
                        species=species,
                    )

        # Bootstrapped corrected flux (flux + expo + variance)
        boot_flux = os.path.join(work_dir, f"map_flux_{esa}_Hy_boot_cor.csv")
        boot_flux_var = os.path.join(work_dir, f"map_flux_{esa}_Hy_boot_var.csv")

        if os.path.exists(boot_flux) and os.path.exists(boot_flux_var):
            for csv_src, stem, lbl in [
                (boot_flux, "flux", label_map["flux"]),
                (expo_file, "exposure", label_map["expo"]),
                (boot_flux_var, "variance", label_map["fvar"]),
            ]:
                if os.path.exists(csv_src):
                    out = os.path.join(
                        yaml_dirs["boot_flux"],
                        f"IMAPLo-{energy}Kev-{stem}.txt",
                    )
                    csv_to_map_yaml(
                        csv_file=csv_src,
                        output_file=out,
                        energy_value=energy,
                        map_year=year,
                        label=lbl,
                        pivot=pp,
                        metadata="boot_flux",
                        species=species,
                    )

        # Bootstrap corrected sys err (fser + expo + variance)
        boot_fser = os.path.join(work_dir, f"map_flux_{esa}_Hy_boot_unc.csv")
        boot_fser_var = os.path.join(work_dir, f"map_flux_{esa}_Hy_boot_var.csv")

        if os.path.exists(boot_fser) and os.path.exists(boot_fser_var):
            for csv_src, stem, lbl in [
                (boot_fser, "flux", label_map["fser"]),
                (expo_file, "exposure", label_map["expo"]),
                (boot_fser_var, "variance", label_map["fvar"]),
            ]:
                if os.path.exists(csv_src):
                    out = os.path.join(
                        yaml_dirs["boot_fser"],
                        f"IMAPLo-{energy}Kev-{stem}.txt",
                    )
                    csv_to_map_yaml(
                        csv_file=csv_src,
                        output_file=out,
                        energy_value=energy,
                        map_year=year,
                        label=lbl,
                        pivot=pp,
                        metadata="boot_fser",
                        species=species,
                    )

        # Bootstrap corrected lower sys err (fsel + expo + variance)
        boot_fsel = os.path.join(work_dir, f"map_flux_{esa}_Hy_boot_unl.csv")
        boot_fsel_var = os.path.join(work_dir, f"map_flux_{esa}_Hy_boot_var.csv")

        if os.path.exists(boot_fsel) and os.path.exists(boot_fsel_var):
            for csv_src, stem, lbl in [
                (boot_fsel, "flux", label_map["fsel"]),
                (expo_file, "exposure", label_map["expo"]),
                (boot_fsel_var, "variance", label_map["fvar"]),
            ]:
                if os.path.exists(csv_src):
                    out = os.path.join(
                        yaml_dirs["boot_fsel"],
                        f"IMAPLo-{energy}Kev-{stem}.txt",
                    )
                    csv_to_map_yaml(
                        csv_file=csv_src,
                        output_file=out,
                        energy_value=energy,
                        map_year=year,
                        label=lbl,
                        pivot=pp,
                        metadata="boot_fsel",
                        species=species,
                    )

        # Bootstrap corrected upper sys err (fseu + expo + variance)
        boot_fseu = os.path.join(work_dir, f"map_flux_{esa}_Hy_boot_unu.csv")
        boot_fseu_var = os.path.join(work_dir, f"map_flux_{esa}_Hy_boot_var.csv")

        if os.path.exists(boot_fseu) and os.path.exists(boot_fseu_var):
            for csv_src, stem, lbl in [
                (boot_fseu, "flux", label_map["fseu"]),
                (expo_file, "exposure", label_map["expo"]),
                (boot_fseu_var, "variance", label_map["fvar"]),
            ]:
                if os.path.exists(csv_src):
                    out = os.path.join(
                        yaml_dirs["boot_fseu"],
                        f"IMAPLo-{energy}Kev-{stem}.txt",
                    )
                    csv_to_map_yaml(
                        csv_file=csv_src,
                        output_file=out,
                        energy_value=energy,
                        map_year=year,
                        label=lbl,
                        pivot=pp,
                        metadata="boot_fseu",
                        species=species,
                    )
