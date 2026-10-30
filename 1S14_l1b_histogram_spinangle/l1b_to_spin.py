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


data_dir_path = '../input_l1b_histrates'
data_dir = Path(data_dir_path)

outdir_hy = './l1b_hist_csv/Hydrogen'
outdir_ox = './l1b_hist_csv/Oxygen'
os.makedirs(outdir_hy,exist_ok=True)
os.makedirs(outdir_ox,exist_ok=True)

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
    
            for esa_idx in range(1, 8):
                esa = esa_idx - 1
                nep_cnts = np.zeros((60))
                
                hcnts = cdf[f'{el}_counts'][...][:, esa, :]
                hcnts = np.sum(hcnts.T, axis=1)
                
                nep_cnts[0:10] = hcnts[50:60]
                nep_cnts[10:30] = hcnts[0:20]
                nep_cnts[30:60] = hcnts[20:50]
                
                esa_dict[f'ESA{esa_idx}'] = nep_cnts
            
            # Build dataframe
            df_new = pd.DataFrame({
                'SpinBins': range(60),
                **esa_dict
            })
            
            df_new.to_csv(f"{outdir}/{basename}.csv", index=False)
            
    except Exception as e:
        print(f"Skipping {file.name}: {e}")

