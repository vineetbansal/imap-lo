#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov  2 17:10:13 2025

@author: hafijulislam
"""

# >>> import cdflib
# >>> cdf = cdflib.CDF("./input/imap_lo_l1a_de_20260120-repoint00132_v001.cdf")
# >>> cdf.cdf_info()
# CDFInfo(CDF=PosixPath('/Users/nschwadron/data/imap_pipeline2/1R3-CDF-spinphaseDEWTime/input/imap_lo_l1a_de_20260120-repoint00132_v001.cdf'), Version='3.9.0', Encoding=6, Majority='Row_major', rVariables=[], zVariables=['met', 'de_count', 'passes', 'coincidence_type', 'de_time', 'esa_step', 'mode', 'tof0', 'tof1', 'tof2', 'tof3', 'cksm', 'pos', 'shcoarse', 'epoch', 'direct_events', 'direct_events_label'], Attributes=[{'Acknowledgement': 'Global'}, {'Data_type': 'Global'}, {'Data_version': 'Global'}, {'Descriptor': 'Global'}, {'Discipline': 'Global'}, {'File_naming_convention': 'Global'}, {'HTTP_LINK': 'Global'}, {'Instrument_type': 'Global'}, {'LINK_TITLE': 'Global'}, {'Logical_file_id': 'Global'}, {'Logical_source': 'Global'}, {'Logical_source_description': 'Global'}, {'Mission_group': 'Global'}, {'PI_affiliation': 'Global'}, {'PI_name': 'Global'}, {'Project': 'Global'}, {'Rules_of_use': 'Global'}, {'Source_name': 'Global'}, {'TEXT': 'Global'}, {'Repointing': 'Global'}, {'Start_date': 'Global'}, {'Parents': 'Global'}, {'ground_software_version': 'Global'}, {'Generation_date': 'Global'}, {'Generated_by': 'Global'}, {'DEPEND_0': 'Variable'}, {'CATDESC': 'Variable'}, {'DISPLAY_TYPE': 'Variable'}, {'FIELDNAM': 'Variable'}, {'FILLVAL': 'Variable'}, {'FORMAT': 'Variable'}, {'LABLAXIS': 'Variable'}, {'UNITS': 'Variable'}, {'VALIDMIN': 'Variable'}, {'VALIDMAX': 'Variable'}, {'VAR_TYPE': 'Variable'}, {'DEPEND_1': 'Variable'}, {'LABL_PTR_1': 'Variable'}, {'TIME_BASE': 'Variable'}, {'RESOLUTION': 'Variable'}, {'TIME_SCALE': 'Variable'}, {'REFERENCE_POSITION': 'Variable'}, {'DICT_KEY': 'Variable'}, {'MONOTON': 'Variable'}, {'SCALETYP': 'Variable'}], Copyright='\nCommon Data Format (CDF)\nhttps://cdf.gsfc.nasa.gov\nSpace Physics Data Facility\nNASA/Goddard Space Flight Center\nGreenbelt, Maryland 20771 USA\n(User support: gsfc-cdf-support@lists.nasa.gov)\n', Checksum=False, Num_rdim=0, rDim_sizes=[], Compressed=False, LeapSecondUpdate=None)
# 'met', 'de_count', 'passes', 'coincidence_type', 'de_time', 'esa_step', 'mode', 'tof0', 'tof1', 'tof2', 'tof3', 'cksm', 'pos', 'shcoarse', 'epoch', 'direct_events', 'direct_events_label'

import pandas as pd
import numpy as np
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from spacepy import pycdf
from spacepy.time import Ticktock
import re
from scipy.optimize import curve_fit
import os

TOF3_L = [ 11.0, 7.0, 3.5, 0.0 ]
TOF3_H = [15.0, 11.0, 7.0, 3.5 ]
# TOF_0, TOF_1, TOF_2
E_PEAK_H = [ 20.0, 10.0, 10.0 ]
H_PEAK_L = [ 20.0, 10.0, 10.0 ]
H_PEAK_H = [ 70.0, 50.0, 40.0 ]
CO_PEAK_L = [ 100.0, 60.0, 60.0   ]
CO_PEAK_H = [ 270.0, 150.0, 150.0 ]
#  for GOLD, TOF2 < 15, TOF2 < 35 and > 35

# EU = C0 + C1 * ADC
# ADC_TOF = [C0, C1]
ADC_TOF0 = [5.5252E-01 ,   1.6837E-01]
ADC_TOF1 = [-7.2018E-01,  1.6512E-01]
ADC_TOF2 = [3.7442E-01,    1.6641E-01]
ADC_TOF3 = [4.6726E-01,    1.7144E-01]

CHKSM_LB = -21
CHKSM_RB = -6

PI = np.pi

VERY_SMALL = 1.0e-30

epoch0 = datetime(2010, 1, 1, 0, 0, 0)

cols = ['shcoarse', 'absent', 'timestamp', 'egy', 'mode', 'TOF0', 'TOF1', 'TOF2', 'TOF3', 'checksum', 'position']

data_dir_path = '../input_l1b_histrates'
data_dir = Path(data_dir_path)
goodtime_file = '../input_goodtime/imap_lo_goodtimes.csv'

hk_dir = Path('../input_hk')

outdir_hy = Path('./l1b_hist_fit_csv/Hydrogen')
outdir_ox = Path('./l1b_hist_fit_csv/Oxygen')

outdir_hy.mkdir(parents=True, exist_ok=True)
outdir_ox.mkdir(parents=True, exist_ok=True)

def parse_key_version(filename):
    m = re.search(r'(\d{8}-repoint\d+)_v(\d+)', filename)
    if not m:
        return None, None
    key = m.group(1)
    version = int(m.group(2))
    return key, version

def get_pname(pivot):
    if 85 < pivot < 95:
        return '90'
    elif 70 < pivot < 80:
        return '75'
    elif 100 < pivot < 110:
        return '105'
    return 'unknown'

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

    # compute fallback index near 90 deg
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

    # compute fallback index near 90 deg
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
    peak = norm * dx / (np.sqrt(2.0*np.pi)*(sigma+VERY_SMALL) )
    # this is the peak rate in the top bin

    return mu, sigma, peak

# moment uncertainty algorithms ...
#    unc_mean_o = mean_o / np.sqrt(sum_o + small)
#    dev_o = np.sqrt(np.abs(sum_dev_o / (sum_o + small) - mean_o**2))
#    unc_dev_o = np.sqrt( dev_o**2 / np.sqrt(sum_o + small)  + unc_mean_o**2 ) 
#    peak_o = sum_o * 6.0 / (np.sqrt(2.0 * np.pi) * (dev_o + small)) # 6 from 6 deg integration
#    cnt_o = peak_o
#    peak_o = peak_o / (expo + small)
#    unc_o = peak_o / np.sqrt(cnt_o + small)

def compute_moments_wunc(theta_deg, y, exposure_bin):
    yuse = np.clip(y, 0.0, None)
    dx = theta_deg[1] - theta_deg[0]
    norm = np.sum(yuse)
    cnts = exposure_bin * yuse
    sum_cnts = np.sum(cnts)

    if norm <= 0:
        return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan


    mu = np.sum(theta_deg * yuse) / norm
    # choice of 12 deg as the intrinsic width based on 6º resolution. a 1 count uncertainty within 2 bins = 1 bin + 2 x 0.5 bins
    dmu = 12.0 / np.sqrt(sum_cnts + VERY_SMALL)
    sigma = np.sqrt(np.sum(yuse * (theta_deg - mu) ** 2) / norm)
    dsigma = np.sqrt( sigma**2 / np.sqrt(sum_cnts + VERY_SMALL)  + dmu**2 ) 
    peak = norm * dx / (np.sqrt(2.0*np.pi)*(sigma+VERY_SMALL) )
    cnt_peak = peak * sum_cnts / (norm + VERY_SMALL) 
    dpeak = peak / np.sqrt( cnt_peak + VERY_SMALL )
    # this is the peak rate in the top bin

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
            maxfev=10000
        )
        A, mu, sigma, C = popt
        sigma = abs(sigma)
        peak = A + C
        return mu, sigma, peak, C
    except Exception:
        return np.nan, np.nan, np.nan, np.nan


def do_gaussian_fit_local_wunc(theta_deg, y, dy, half_width=30.0):
    if np.all(y <= 0):
        return (np.nan, np.nan, np.nan, np.nan,
                np.nan, np.nan, np.nan, np.nan,
                np.nan, np.nan)

    xw, yw, peak_angle = select_peak_window(theta_deg, y, half_width=half_width)

    # apply the same window to dy
    theta_unwrapped = unwrap_angles(theta_deg, peak_angle)
    keep = np.abs(theta_unwrapped - peak_angle) <= half_width
    dyw = np.asarray(dy)[keep]

    if len(xw) < 4:
        return (np.nan, np.nan, np.nan, np.nan,
                np.nan, np.nan, np.nan, np.nan,
                np.nan, np.nan)

    # protect against zero/negative uncertainties
    dyw = np.asarray(dyw, dtype=float)
    bad = ~np.isfinite(dyw) | (dyw <= 0)
    if np.any(bad):
        dyw = dyw.copy()
        dyw[bad] = np.nan

    if np.all(~np.isfinite(dyw)):
        return (np.nan, np.nan, np.nan, np.nan,
                np.nan, np.nan, np.nan, np.nan,
                np.nan, np.nan)

    # replace any bad points with a large uncertainty
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
            maxfev=10000
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
            A, A_unc
        )

    except Exception:
        return (np.nan, np.nan, np.nan, np.nan,
                np.nan, np.nan, np.nan, np.nan,
                np.nan, np.nan)

def parse_hist_metadata(filename):
    """
    Example:
    imap_lo_l1b_histrates_20260217-repoint00160_v002.cdf
    """
    m = re.search(r'(\d{8})-repoint(\d+)_v(\d+)', filename)
    if not m:
        return None, None, None
    file_date = m.group(1)
    repoint = m.group(2)
    version = m.group(3)
    return file_date, repoint, version

def ensure_header(csvfile):
    if (not csvfile.exists()) or (csvfile.stat().st_size == 0):
        with open(csvfile, 'w') as f:
            print(
                "file_date,YYYYDOY,repoint,version,pivot,pname,element,esa,"
                "exposure_s,peak_angle_bin,"
                "mu_mom,sigma_mom,peak_mom,"
                "mu_fit,sigma_fit,peak_fit,bg_fit",
                file=f
            )

def ensure_header_wunc(csvfile):
    if (not csvfile.exists()) or (csvfile.stat().st_size == 0):
        with open(csvfile, 'w') as f:
            print(
                "file_date,YYYYDOY,repoint,version,pivot,pname,element,esa,"
                "exposure_s,peak_angle_bin,"
                "mu_mom,dmu_mom,sigma_mom,dsigma_mom,peak_mom,dpeak_mom,"
                "mu_fit,dmu_fit,sigma_fit,dsigma_fit,peak_fit,dpeak_fit,bg_fit,dbg_fit",
                file=f
            )


def write_result_line(fout, result):
    print(
        f"{result['esa']},"
        f"{result['mu_mom']:.3f},{result['sigma_mom']:.3f},{result['peak_mom']:.6e},"
        f"{result['mu_fit']:.3f},{result['sigma_fit']:.3f},{result['peak_fit']:.6e},{result['bg_fit']:.6e}",
        file=fout
    )

def replace_matching_line(outfile, new_line, file_date, repoint, esa_name):
    lines = []
    last_match = None

    if os.path.exists(outfile):
        with open(outfile, "r") as fin:
            lines = fin.readlines()

        for i, line in enumerate(lines):
            parts = line.rstrip("\n").split(",")

            if len(parts) >= 8:
                if (
                    parts[0] == str(file_date) and
                    parts[2] == str(repoint) and
                    parts[7] == str(esa_name)
                ):
                    last_match = i

    if last_match is None:
        lines.append(new_line + "\n")
    else:
        lines[last_match] = new_line + "\n"

    with open(outfile, "w") as fout:
        fout.writelines(lines)

#file = "/Users/hafijulislam/Library/CloudStorage/Box-Box/First_light_maps/DN/Instrument_FM1_playback_301_ILO_SCI_DE_dec_20251102T170018_DN.csv"

epoch = datetime(2010, 1, 1, 0, 0, 0)


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

print("3S2: processing goodtime histogram H and O")

df = pd.read_csv(
        goodtime_file,
        header=None,      # no header row
        usecols=range(14),# read only first 14 columns (up to esa7)
        dtype=str         # read everything as string initially
    )

print("goodtime_file = ", goodtime_file)

    # Assign column names
df.columns = [
        "date","time_start","time_end","bin_start","bin_end",
        "inst","esa1","esa2","esa3","esa4","esa5","esa6","esa7","bla"
    ]

    # Convert numeric columns to int
numeric_cols = ["date","time_start","time_end","bin_start","bin_end",
                    "esa1","esa2","esa3","esa4","esa5","esa6","esa7"]
df[numeric_cols] = df[numeric_cols].astype(int)

    # 'inst' stays as string
inst = df['inst'].to_numpy()
time_start = df['time_start'].to_numpy().copy()
time_end   = df['time_end'].to_numpy().copy()
bin_start  = df['bin_start'].to_numpy().copy()
bin_end    = df['bin_end'].to_numpy().copy()
esa_flags  = df[['esa1','esa2','esa3','esa4','esa5','esa6','esa7']].to_numpy().copy()

ngoodt = len(time_end)
time_end_copy = time_end.copy()

nep = (3.0 + 6.0 * np.arange(60, dtype=float)) % 360.0

manifest_file = Path('./l1b_hist_fit_csv/processed_files.txt')
processed = set()

if manifest_file.exists():
    with open(manifest_file, 'r') as f:
        processed = {line.strip() for line in f if line.strip()}

for key in sorted(hist_latest):
    hist_file = hist_latest[key][1]
    hk_entry = hk_latest.get(key)

    if hk_entry is None:
        print(f"Missing HK for {hist_file.name}")
        continue

    hk_file = hk_entry[1]

    process_id = f"{key}|hist_v{hist_latest[key][0]}|hk_v{hk_latest[key][0]}"
    if process_id in processed:
        print("3S2 Skipping already processed:", process_id)
        continue

    print("3S2 Processing hist file and HK file:", hist_file, hk_file )

    hk_file = hk_entry[1]
    cdf_hk = pycdf.CDF(str(hk_file))

    try:
        epoch_hk = cdf_hk['epoch']
        tt = Ticktock(epoch_hk, 'CDF')
        times = np.array(tt.UTC)

        t0_hk = times[0]
        start_time_hk = t0_hk + timedelta(hours=3)
        end_time_hk = t0_hk + timedelta(hours=15)
        mask_hk = (times >= start_time_hk) & (times <= end_time_hk)

        # --- pivot ---
        try:
            pri = cdf_hk['pcc_coarse_pot_pri'][...]
            pivot = np.nanmedian(pri[mask_hk])
            if np.isnan(pivot):
                pivot = 90.0
        except Exception:
            pivot = 90.0

        # --- spin period ---
        try:
            spin_period = cdf_hk['spin_period'][...]
            tspin = np.nanmedian(spin_period[mask_hk])
            if np.isnan(tspin):
                tspin = 15.0
        except Exception:
            tspin = 15.0

    except Exception:
        # catastrophic HK failure
        pivot = 90.0
        tspin = 15.0
    finally:
        cdf_hk.close()

    pname = get_pname(pivot)
    
    cdf = pycdf.CDF(str(hist_file))
    
    epoch = cdf['epoch'][:]
    yr1  = epoch[0].year
    doy1 = int(doy_fraction(epoch[0]) )
    sdoy1 = f"{doy1:03d}"
    date1 = f"{yr1}{sdoy1}"

    for element in ['Oxygen','Hydrogen']:
        if element=='Hydrogen':
            el='h'
            outdir = outdir_hy / pname
        else:
            el='o'
            outdir = outdir_ox / pname

        outdir.mkdir(parents=True, exist_ok=True)
    
        counts = cdf[f'{el}_counts'][...][:, :, :]
        epoch       = cdf['epoch'][:]
        met = met_from_epoch(epoch)

        # ------------------------------------------
        # Now process ESA1..ESA4 and write results
        # ------------------------------------------

        file_date, repoint, version = parse_hist_metadata(hist_file.name)
        if file_date is None:
            file_date = "unknown"
            repoint = "unknown"
            version = "unknown"

        theta_deg = nep.copy()   # use your NEP-centered angle array

        for esa_name in ['ESA1', 'ESA2', 'ESA3', 'ESA4', 'ESA5', 'ESA6', 'ESA7']:

            # Estimate exposure for this ESA after filtering
            # Number of surviving histogram blocks contributing to this ESA
            esa_num = int(esa_name.replace('ESA', ''))
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
                expo[bin] = np.count_nonzero(mask) * 4.0 * tspin / ( 60.0 * 7.0 )

            nep_cnts = np.zeros(60)
            nep_expo = np.zeros(60)

            nep_cnts[0:10] = total_cnts[50:60]
            nep_cnts[10:30] = total_cnts[0:20]
            nep_cnts[30:60] = total_cnts[20:50]

            nep_expo[0:10] = expo[50:60]
            nep_expo[10:30] = expo[0:20]
            nep_expo[30:60] = expo[20:50]
            
            rates = nep_cnts / (nep_expo + VERY_SMALL)
            drates = rates / np.sqrt(nep_cnts + VERY_SMALL)

            if not np.any(rates > 0):
                continue

            valid_expo = nep_expo[nep_expo > 0]
            if len(valid_expo) > 0:
                exposure_s = np.mean(valid_expo)
            else:
                exposure_s = 0.0
            
            # restrict both moments and fit to peak +/- 30 deg
            #theta_local, rates_local, peak_angle = select_peak_window(
            #    theta_deg, rates, half_width=30.0
            #)

            theta_local, rates_local, exposure_local, peak_angle = select_peak_window_wexp(
                theta_deg, rates, nep_expo, half_width=30.0
            )
            
            # mu_mom, sigma_mom, peak_mom = compute_moments(theta_local, rates_local)
            mu_mom, dmu_mom, sigma_mom, dsigma_mom, peak_mom, dpeak_mom = compute_moments_wunc(theta_local, rates_local, exposure_local)

            mu_fit, sigma_fit, peak_fit, bg_fit, mu_unc, sigma_unc, peak_unc, C_unc, A, A_unc = do_gaussian_fit_local_wunc(theta_deg, rates, drates, half_width=30.0)

#            mu_fit, sigma_fit, peak_fit, bg_fit = do_gaussian_fit_local(
#                theta_deg, rates, half_width=30.0
#            )

            # directory structure: Hydrogen/90/ESA1/
            esa_dir = outdir / esa_name
            esa_dir.mkdir(parents=True, exist_ok=True)

            # one cumulative file per species/pivot/ESA
            outfile = esa_dir / f"{element}_{pname}_{esa_name}.csv"
            ensure_header_wunc(outfile)

            new_line = (
                f"{file_date},{date1},{repoint},{version},"
                f"{pivot:.3f},{pname},{element},{esa_name},"
                f"{exposure_s:.3f},{peak_angle:.3f},"
                f"{mu_mom:.6f},{dmu_mom:.6f},{sigma_mom:.6f},{dsigma_mom:.6f},{peak_mom:.6e},{dpeak_mom:.6e},"
                f"{mu_fit:.6f},{mu_unc:.6f},{sigma_fit:.6f},{sigma_unc:.6f},"
                f"{A:.6e},{A_unc:.6e},{bg_fit:.6e},{C_unc:.6e}"
            )

            replace_matching_line(
                outfile,
                new_line,
                file_date,
                repoint,
                esa_name 
            )

            print(
                    f"3S2: ",
                    f"{file_date},{date1},{repoint},{version},"
                    f"{pivot:.3f},{pname},{element},{esa_name},"
                    f"{exposure_s:.3f},{peak_angle:.3f},"
                    f"{mu_mom:.6f},{sigma_mom:.6f},{peak_mom:.6e},"
                    f"{mu_fit:.6f},{sigma_fit:.6f},{peak_fit:.6e},{bg_fit:.6e}"
                )


    if process_id not in processed:
        processed.add(process_id)
        with open(manifest_file, 'a') as f:
            f.write(process_id + "\n")
