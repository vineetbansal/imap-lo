#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  7 11:53:09 2026

@author: hafijulislam

This code produce spin angle distribution from the l1b histograms.
"""
from spacepy.pycdf import CDF
from spacepy import pycdf
import numpy as np
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
import pandas as pd, re, shutil
import spiceypy
from imap_processing.spice.time import ttj2000ns_to_met

# The good-time boundaries are real spacecraft MET, so the histogram epochs have
# to be converted with SPICE to be comparable to them.  Subtracting a naive
# 2010-01-01 from the UTC epoch instead is off by -8.409 s (TT-UTC plus the leap
# seconds since the MET epoch), which silently drops 734 of 23850 cycles across
# the 158 days in the archive -- up to 14% of a thin day.
_SPICE_DIR = Path(__file__).parent.parent / "input_SPICE"


def furnish_kernels():
    """Load the leap-second and spacecraft-clock kernels the MET conversion needs."""
    if spiceypy.ktotal("all") == 0:
        for rel in ("lsk/naif0012.tls", "sclk/imap_sclk_0153.tsc"):
            path = _SPICE_DIR / rel
            if not path.exists():
                raise FileNotFoundError(f"required SPICE kernel missing: {path}")
            spiceypy.furnsh(str(path))


def epoch_to_met(epoch):
    """Convert CDF epochs (datetimes) to spacecraft MET seconds via SPICE."""
    return ttj2000ns_to_met(pycdf.lib.v_datetime_to_tt2000(np.asarray(epoch)))


class NoGoodTimes(Exception):
    """A day the goodtimes product has no intervals for; there is nothing to map."""

def radec2cart(ra,th):

    x = np.cos(np.radians(ra)) * np.sin(np.radians(th))
    y = np.sin(np.radians(ra)) * np.sin(np.radians(th))
    z = np.cos(np.radians(th))
    
    return np.array([x,y,z])

def equatorial_to_ecliptic(alpha, delta):
    
    # Obliquity of ecliptic at J2000.0 epoch
    epsilon_0 = 23.43929111  # degrees
    
    alpha_rad = np.radians(alpha)
    delta_rad = np.radians(delta)
    epsilon_rad = np.radians(epsilon_0)
    
    numerator = np.sin(alpha_rad) * np.cos(epsilon_rad) + np.tan(delta_rad) * np.sin(epsilon_rad)
    denominator = np.cos(alpha_rad)
    
    # Calculate ecliptic longitude
    lambda_ecl_rad = np.arctan2(numerator, denominator)
    
    # Calculate ecliptic latitude
    beta_ecl_rad = np.arcsin(np.sin(delta_rad) * np.cos(epsilon_rad) - 
                            np.cos(delta_rad) * np.sin(epsilon_rad) * np.sin(alpha_rad))
    

    lambda_ecl = np.degrees(lambda_ecl_rad)
    beta_ecl = np.degrees(beta_ecl_rad)

    lambda_ecl = lambda_ecl % 360
    
    return lambda_ecl, beta_ecl

def create_ra_dec(s_ra,s_dec,pivot_angle):
    
    spin_ra,spin_dec = s_ra,s_dec # Using inertial pointing file give spin axis information
    spin_th = 90.0 - spin_dec

    nep_ra,nep_dec = 270, 66.56 # Standard NEP direction in J2000
    nep_th = 90.0 - nep_dec

    a_spine_deg = pivot_angle
    a_spine = np.radians(a_spine_deg) 
    
    def norm(v):
        return v / np.linalg.norm(v)

    e_nep      = norm(radec2cart(nep_ra, nep_th))
    e_av_spin  = norm(radec2cart(spin_ra, spin_th))
    
    e_perp_pole = e_nep - np.dot(e_nep, e_av_spin) * e_av_spin
    e_perp_pole = norm(e_perp_pole)
    
    e_perp_ram  = np.cross(e_av_spin, e_perp_pole)
    e_perp_ram  = norm(e_perp_ram)
    
    bin_edges = np.arange(0,366,6)
    bin_centers = 0.5 * (bin_edges[1:]+bin_edges[:-1])
    raf,decf = [],[]
    for i in bin_centers:
        
        x,y,z = np.cos(a_spine)*e_av_spin+np.sin(a_spine)*np.cos(np.radians(i))*e_perp_pole + np.sin(a_spine)*np.sin(np.radians(i))*e_perp_ram

        eq_ra = np.degrees(np.arctan2(y,x))
        eq_dec =np.degrees( np.arcsin(z))
        ra,dec = equatorial_to_ecliptic(eq_ra,eq_dec)
        raf.append(ra)
        decf.append(dec)
    
    return raf,decf

GOODTIME_COLS = ["YD","gd_start","gd_end","bin_start","bin_end","Instrument"] + \
                [f"E-Step{i}" for i in range(1, 8)] + ["Comment"]


def select_goodtimes(filename, YD, repoint=None):
    """The goodtime rows belonging to one pointing.

    A day can carry more than one repointing -- 2026-097 has repoint00209 and
    repoint00211 -- and the goodtimes product covers them separately.  Selecting
    on the day alone pairs a pointing's histogram counts with another pointing's
    good times, which is how repoint00211's counts came to be mapped against
    repoint00209's windows.  lo_l2 keys its inputs by repointing
    (_complete_pointings), so the match is made on the repointing here too, and a
    pointing the goodtimes product does not cover is dropped rather than guessed
    at.
    """
    df = pd.read_csv(filename, names=GOODTIME_COLS)
    df = df[df['YD'] == YD]
    if df.empty:
        raise NoGoodTimes(f"No matching rows found for {YD} in Goodtime file")

    if repoint is not None:
        df = df[df['Comment'].astype(str).str.contains(f"repoint{repoint}", regex=False)]
        if df.empty:
            raise NoGoodTimes(f"Goodtime file covers {YD} but not repoint{repoint}")
    return df


def estimate_exposure_time(filename,YD, esa, repoint=None):
    df = select_goodtimes(filename, YD, repoint)

    result = np.zeros((7,60))
    start_arr = []
    end_arr = []
    
    for _, row in df.iterrows():
        # Ensure numerical types for subtraction; convert if needed
        gd_end = float(row['gd_end'])
        gd_start = float(row['gd_start'])
        start_arr.append(gd_start)
        end_arr.append(gd_end)
        dt = (gd_end - gd_start) / (7 * 60)
        for i in range(1, 7 + 1):
            dist = dt * row[f'E-Step{i}']
            arr = np.zeros(60)
            arr[int(row['bin_start']):int(row['bin_end']) + 1] = dist
            result[i-1] += arr
    
    # Convert to DataFrame for clarity
    bin_indices = np.arange(60)
    result_df = pd.DataFrame(result.T, columns=[f'E-Step{i}' for i in range(1, 7+1)])
    result_df['bin'] = bin_indices
    
    return start_arr,end_arr,result_df[f'E-Step{esa}']

def goodtime_pivot(filename, YD, repoint=None):
    """Read the pivot angle the L1B goodtimes product recorded for this pointing.

    This is what both the cone geometry and the pivot_{75,90,105} routing are
    built from.  The measured pivot is 74.990 / 90.096 / 104.944, and
    imap_processing's lo_l2 uses that measured value.  Feeding it 90.000 instead
    of 90.096 moves the boresight ring by a tenth of a degree, which flips bins
    across pixel boundaries and shifts the intensity of ~11% of pixels by more
    than 20%.

    share_pivot.csv carries the nominal pointing group as *planned*, one row per
    day, and the plan is not always what flew: repoint00128 (2026-016) and
    repoint00341 (2026-227) both flew at 90.096 on days the plan calls 75 and
    105.  A daily calendar cannot express a pivot change that lands on a mid-day
    repointing, so routing by it filed repoint00128's daily files under pivot_75
    and dropped that whole pointing from the pivot_90 map -- silently, since a
    misrouted day is not a failed one.  Routing by the measured value instead
    keeps the geometry and the destination directory from disagreeing.
    """
    df = select_goodtimes(filename, YD, repoint)

    pivots = df['Comment'].astype(str).str.extract(r"pivot=([\d.]+)")[0].dropna().astype(float)
    if pivots.empty:
        raise ValueError(f"Goodtime file records no pivot= for {YD}")
    if pivots.nunique() > 1:
        raise ValueError(f"Goodtime file disagrees on the pivot for {YD}: "
                         f"{sorted(pivots.unique())}")
    return float(pivots.iloc[0])

def route_by_pivot(data_dir, pivot_csv):

    m = dict(zip(*(pd.read_csv(pivot_csv)[["DOY", "Pivot"]].values.T)))
    p = re.compile(r"(20\d{5})")

    for f in Path(data_dir).glob("*.csv"):
        g = p.search(f.name)
        if g and int(g.group(1)) in m:
            shutil.move(str(f), Path(data_dir) / f"pivot_{m[int(g.group(1))]}" / f.name)

## Input files

# file_path = '/Users/hafijulislam/UNH/imap-data-access/l1b_histrates/imap_lo_l1b_histrates_20251214-repoint00078_v001.cdf'
# file_path = '/Users/hafijulislam/Library/CloudStorage/GoogleDrive-hislam09@gmail.com/My Drive/UNH/imap-data-access/l1b_histrates/imap_lo_l1b_histrates_20260114-repoint00126_v001.cdf'
data_dir_path = '../input_l1b_histrates'
data_dir = Path(data_dir_path)

## Make output directories
for x in [75,90,105]:
    os.makedirs(f'./outdir/pivot_{x}/daily', exist_ok=True)

furnish_kernels()

# A day that fails here is a whole pointing missing from the map, and a pointing
# is a median 49% of the exposure of every pixel its boresight ring crossed --
# dropping one moves those pixels' intensity by a median 25%.  So the failures
# are collected and reported at the end rather than scrolling past, and the run
# exits non-zero if any day was lost.
skipped_days = []

for file in data_dir.glob("*.cdf"):
    try:
        file_path = str(file)
        
        # basename = os.path.basename(file_path)
        basename = file.name
        
        pointing_file = './config_files/pointing_file.csv'
        goodtime_file = './config_files/imap_lo_goodtimes_2.csv'
        
        for f in [pointing_file, goodtime_file]:
            if not os.path.exists(f):
                print(f"File not found: {f}")
                sys.exit(1)
        
        pointing_cols = ['YD', 'spin_ra','spin_dec']
        df_point = pd.read_csv(pointing_file, names=pointing_cols, skiprows=1)
        
        ## Convert yyyymmdd to YYYYDOY
        
        yymmdd = basename.split('_')[4].split('-')[0]
        date = datetime.strptime(yymmdd, "%Y%m%d")
        YD = f"{date.year}{date.timetuple().tm_yday:03d}"
        int_YD = int(YD)

        repoint = basename.split("-repoint")[1].split("_")[0] if "-repoint" in basename else None

        print(f"Processing DOY: {YD} repoint{repoint}")

        ### -----------------
        ## Ask the goodtimes product first: a pointing with no intervals is one
        ## lo_l2 drops too, so it must not be reported as a lost pointing below.
        ##
        ## The cone geometry and the pivot_{75,90,105} group the daily file is
        ## written to both come from the pivot the L1B goodtimes product
        ## measured, which is what lo_l2 uses -- see goodtime_pivot().  The
        ## measured values are 74.990 / 90.096 / 104.944, so rounding names the
        ## group without consulting the planning calendar.
        PIVOT_ANGLE = goodtime_pivot(goodtime_file, int_YD, repoint)
        pivot = round(PIVOT_ANGLE)

        ## Grab spin axis information from the pointing file

        df_p = df_point[df_point['YD']==int_YD]
        if df_p.empty:
            raise ValueError(f"No matching rows found for {YD} in the pointing file")

        s_ra = df_p['spin_ra'].astype(float).values[0]
        s_dec = df_p['spin_dec'].astype(float).values[0]

        pivot_str = f"pivot_{pivot}"

        ra,dec = create_ra_dec(s_ra,s_dec,PIVOT_ANGLE)
        
        cdf = CDF(file_path)
        
        
        for ESA in range(1,8):
            
            nep_cnts = np.zeros((60))
            nep_expo = np.zeros((60))
            
            ## Filter through Goodtime, create masking
            start_arr,end_arr,expo = estimate_exposure_time(goodtime_file ,int_YD, ESA, repoint)
            
            epoch_sec = cdf['epoch'][:]
            met_sec = epoch_to_met(epoch_sec)

            mask = np.zeros_like(epoch_sec,dtype=bool)

            for start, end in zip(start_arr, end_arr):
                mask |= (met_sec >= start) & (met_sec <= end)
            
            ### Extract values from cdf
            esa = ESA-1
            hcnts = cdf['o_counts'][...][mask,esa,:]
            exposure = np.sum(cdf['exposure_time_6deg'][...][mask,esa,:].T,axis=1)
            
            ## If No filter is appled then uncomment below
            # hcnts = cdf['o_counts'][...][:,esa,:]
            # exposure = np.sum(cdf['exposure_time_6deg'][...][:,esa,:].T,axis=1)
            
            ## Sum over filtered time blocks
            hcnts = np.sum(hcnts.T,axis=1)
            
            ## Convert from Spin Angle to NEP angle
            nep_cnts[0:10] = hcnts[50:60]
            nep_cnts[10:30] = hcnts[0:20]
            nep_cnts[30:60] = hcnts[20:50]
            
            nep_expo[0:10] = exposure[50:60]
            nep_expo[10:30] = exposure[0:20]
            nep_expo[30:60] = exposure[20:50]
            
            nep_rates = nep_cnts/nep_expo
            
            nep_angles = np.linspace(0,360,61)
            bin_centers = 0.5 * (nep_angles[1:] + nep_angles[:-1])
            
            ## Spin axis into ECLIPJ2000
            seq_ra,seq_dec = equatorial_to_ecliptic(s_ra,s_dec)
            
            df_new = pd.DataFrame()
            
            df_new['bins'] = bin_centers
            df_new['counts'] = nep_cnts
            df_new['ra'] = ra
            df_new['dec'] = dec
            df_new['expo'] = nep_expo
            df_new['spin_ra'] = seq_ra
            df_new['spin_dec'] = seq_dec

            # Provenance columns for map manifest
            df_new['date_yyyymmdd'] = yymmdd
            df_new['yd'] = YD
            df_new['repoint'] = repoint if repoint is not None else ""
            df_new['pivot'] = pivot
            df_new['pivot_measured'] = PIVOT_ANGLE
            df_new['l1b_product'] = "histrates"
            df_new['l1b_filename'] = basename
            df_new['l1b_path'] = str(Path(file_path).resolve())

            stem = f"data_YD_{YD}" + (f"_repoint{repoint}" if repoint is not None else "")
            df_new.to_csv(f"./outdir/{pivot_str}/daily/{stem}_esa{ESA}.csv", index=False)

    except NoGoodTimes as e:
        # lo_l2 has nothing to accumulate for these days either, so they are an
        # expected drop rather than a lost pointing.
        print(f"  no good times, nothing to map: {file.name} ({e})")
    except Exception as e:
        skipped_days.append((file.name, f"{type(e).__name__}: {e}"))

if skipped_days:
    print(f"\n{len(skipped_days)} day(s) produced no daily files -- each one is a whole "
          f"pointing missing from the map:")
    for name, err in skipped_days:
        print(f"  {name}: {err}")
    sys.exit(1)

print("\nall days with good times were mapped")

## Move files into specific directory
# route_by_pivot(
#     data_dir="./outdir",
#     pivot_csv="./input/share_pivot.csv"
# )
