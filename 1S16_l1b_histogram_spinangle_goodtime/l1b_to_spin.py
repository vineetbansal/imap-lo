#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 3 11:53:09 2026

@author: hafijulislam

This code produce spin angle distribution of Counts from the l1b histograms and generates csv file.
"""
from spacepy.pycdf import CDF
import numpy as np
import os
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

data_dir_path = '../input_l1b_histrates'
data_dir = Path(data_dir_path)
goodtime_file = '../input_goodtime/imap_lo_goodtimes.csv'

outdir_hy = './l1b_hist_csv/Hydrogen'
outdir_ox = './l1b_hist_csv/Oxygen'

os.makedirs(outdir_hy,exist_ok=True)
os.makedirs(outdir_ox,exist_ok=True)

epoch0 = datetime(2010, 1, 1, 0, 0, 0)

def met_from_epoch(t):

#    met = (t - epoch0) / 1000.0  # seconds

    e0 = epoch0
    e1 =  t
    dt = e1 - e0
    # numpy / pandas vector case
  # Case 1 — numpy timedelta64
    if isinstance(dt, np.ndarray) and np.issubdtype(dt.dtype, np.timedelta64):
        met = dt / np.timedelta64(1, 's')

    # Case 2 — object array of datetime.timedelta
    elif isinstance(dt, np.ndarray):
        met = np.array([d.total_seconds() for d in dt])

    # Case 3 — pandas Series
    elif hasattr(dt, "dt"):
        met = dt.dt.total_seconds()

    # Case 4 — scalar
    else:
        met = dt.total_seconds()

    return met + 9


    if hasattr(dt, "dtype"):
        met = dt / np.timedelta64(1, 's') + 9
    else:  # scalar datetime.timedelta
        met = dt.total_seconds() + 9

    # this is because we are using an older time kernel (pre 2012)
#    print("met = ",met)
    return met

print("1S16: processing goodtime histogram H and O")

df = pd.read_csv(
        goodtime_file,
        header=None,      # no header row
        usecols=range(14),# read only first 14 columns (up to esa7)
        dtype=str         # read everything as string initially
    )

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
time_start = df['time_start'].to_numpy()
time_end   = df['time_end'].to_numpy()
bin_start  = df['bin_start'].to_numpy()
bin_end    = df['bin_end'].to_numpy()
esa_flags  = df[['esa1','esa2','esa3','esa4','esa5','esa6','esa7']].to_numpy()

ngoodt = len(time_end)
time_end_copy = np.linspace(0,0,ngoodt)
time_end_copy[:] = time_end[:]

for file in data_dir.glob("*.cdf"):
    try:
        file_path = str(file)      
        basename = file.name
        
        cdf = CDF(file_path)
        for element in ['Oxygen','Hydrogen']:
            if element=='Hydrogen':
                el='h'
                outdir=outdir_hy
            else:
                el='o'
                outdir=outdir_ox
                
            esa_dict = {}   # dictionary to store ESA arrays
    
            counts = cdf[f'{el}_counts'][...][:, :, :]
            epoch       = cdf['epoch'][:]
            met = met_from_epoch(epoch)

            unfiltered = {
                'counts': counts
            }

            for esa_idx in range(1, 8):
                esa = esa_idx - 1
                
                for bin in range(0,60):
                    # reset the time_end array
                    time_end[:] = time_end_copy[:]

                    for itime in range(0,ngoodt):
                    # now pull out any goodtime period that has been blown out
                        if esa_flags[itime,esa] == 0:
                            time_end[itime] = time_start[itime]
                        
                        if (bin > bin_end[itime]) or (bin < bin_start[itime] ):
                            time_end[itime] = time_start[itime]

                    met_check  = (met[:, None] >= time_start) & (met[:, None] <= time_end)
                    event_pass = met_check  
                    mask = np.any(event_pass, axis=1) 

#                    for k in ('counts',):
                    unfiltered['counts'][~mask,esa,bin] = 0
                
                nep_cnts = np.zeros((60))
                
                time_end[:] = time_end_copy[:]

                met_check  = (met[:, None] >= time_start) & (met[:, None] <= time_end)
                event_pass = met_check 
                mask = np.any(event_pass, axis=1)
                 
                filtered_cnts = unfiltered['counts'][mask,esa,:] 
                total_cnts = np.sum(filtered_cnts.T, axis=1)

                nep_cnts[0:10] = total_cnts[50:60]
                nep_cnts[10:30] = total_cnts[0:20]
                nep_cnts[30:60] = total_cnts[20:50]
                
                esa_dict[f'ESA{esa_idx}'] = nep_cnts
            
            # Build dataframe
            df_new = pd.DataFrame({
                'SpinBins': range(60),
                **esa_dict
            })
            
            df_new.to_csv(f"{outdir}/{basename}.csv", index=False)
            
    except Exception as e:
        print(f"1S16: Skipping {file.name}: {e}")

