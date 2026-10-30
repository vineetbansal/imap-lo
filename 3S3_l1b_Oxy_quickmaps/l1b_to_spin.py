#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  7 11:53:09 2026

@author: hafijulislam

This code produce spin angle distribution from the l1b histograms.
"""
from spacepy.pycdf import CDF
import numpy as np
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
import pandas as pd, re, shutil

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

def estimate_exposure_time(filename,YD, esa):
    cols = ["YD","gd_start","gd_end","bin_start","bin_end","Instrument",	"E-Step1",	"E-Step2",	"E-Step3",	"E-Step4",	"E-Step5",	"E-Step6",	"E-Step7",	"Comment"]
    
    df1 = pd.read_csv(filename,names=cols)
    
    df = df1[df1['YD']==YD]
    if df.empty:
        raise ValueError(f"No matching rows found for {YD} in Goodtime file")
    
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

for file in data_dir.glob("*.cdf"):
    try:
        file_path = str(file)
        
        # basename = os.path.basename(file_path)
        basename = file.name
        
        pointing_file = './config_files/pointing_file.csv'
        goodtime_file = './config_files/imap_lo_goodtimes_2.csv'
        pivot_csv = "./config_files/share_pivot.csv"
        
        for f in [pointing_file, goodtime_file, pivot_csv]:
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
        
        print(f"Processing DOY: {YD}")
        
        ## Grab spin axis information from the pointing file
        
        df_p = df_point[df_point['YD']==int_YD]
        if df_p.empty:
            raise ValueError(f"No matching rows found for {YD} in the pointing file")
        
        s_ra = df_p['spin_ra'].astype(float).values[0]
        s_dec = df_p['spin_dec'].astype(float).values[0]
        
        ### -----------------
        df_pivot = pd.read_csv(pivot_csv)
        df_pp=df_pivot[df_pivot['DOY']==int_YD]
        pivot = df_pp['Pivot'].astype(float).values[0]
        
        PIVOT_ANGLE = pivot
        
        pivot_str = f"pivot_{int(pivot)}"
        
        ra,dec = create_ra_dec(s_ra,s_dec,PIVOT_ANGLE)
        
        cdf = CDF(file_path)
        
        
        for ESA in range(1,8):
            
            nep_cnts = np.zeros((60))
            nep_expo = np.zeros((60))
            
            ## Filter through Goodtime, create masking
            start_arr,end_arr,expo = estimate_exposure_time(goodtime_file ,int_YD, ESA)
            
            met_epoch = datetime(2010, 1, 1, 0, 0, 0)
            epoch_sec = cdf['epoch'][:]
            met_sec = []
            
            for x in range(len(epoch_sec)):
                ss = (epoch_sec[x]-met_epoch).total_seconds()
                met_sec.append(ss)
            
            met_sec = np.asarray(met_sec, dtype=float)    
            mask = np.zeros_like(epoch_sec,dtype=bool)
            
            for start, end in zip(start_arr, end_arr):
                mask |= (met_sec >= start) & (met_sec <= end)
            
            ### Extract values from cdf
            esa = ESA-1
            hcnts = cdf['o_counts'][...][mask,esa,:]
            exposure = np.sum(cdf['exposure_time_6deg'][...][mask,esa,:].T,axis=1)
            
            ## If No filter is appled then uncomment below
            # hcnts = cdf['h_counts'][...][:,esa,:]
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
            # df_new['expo'] = expo.values
            df_new['expo'] = nep_expo
            df_new['spin_ra'] = seq_ra
            df_new['spin_dec'] = seq_dec
            
            df_new.to_csv(f"./outdir/{pivot_str}/daily/data_YD_{YD}_esa{ESA}.csv", index=False)
        
    except Exception as e:
        print(f"Skipping {file.name}: {e}")

## Move files into specific directory
# route_by_pivot(
#     data_dir="./outdir",
#     pivot_csv="./input/share_pivot.csv"
# )
