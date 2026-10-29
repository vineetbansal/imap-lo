
#!/usr/bin/python
"""
Created on Wed Mar 18 2026
@author: hafijulislam

"""

import numpy as np
import argparse
from scipy.optimize import curve_fit
import random
import datetime
from spacepy.pycdf import CDF
import pandas as pd
import os
from pathlib import Path

PI = np.pi

# ESA Steps
nesa = 7
nalpha = 40
nphi = 3600
dang = 0.1 * PI /180.0
deg = 6.0
nra = 60
ncolat = 30
nmap = nra*ncolat*nesa



eff_h = 1.0

esa_energy = {
    1: 0.019,
    2: 0.037,
    3: 0.071,
    4: 0.141,
    5: 0.274,
    6: 0.585,
    7: 1.135
}
gf ={
    1: 3.11E-05,
    2: 5.01E-05,
    3: 8.41E-05,
    4: 1.36E-04,
    5: 2.07E-04,
    6: 3.87E-04,
    7: 5.99E-04
    }

old_gf = {
    1: 1.24e-4,
    2: 1.27e-4,
    3: 1.56e-4,
    4: 1.95e-4,
    5: 2.55e-4,
    6: 3.45e-4,
    7: 4.04e-4
}



## Get background Rate

def get_brate(YD,esa):
    
    backfile = './config_files/imap_lo_O_background.csv'
    
    df = pd.read_csv(backfile,sep=',', names=['YD','start','end','bin_start','bin_end','Lo','esa1','esa2','esa3','esa4','esa5','esa6','esa7','type'])
    
    brate = df[(df['YD']==int(YD)) & (df['type']=='rate')][f'esa{esa}'].values[0]
    
    return brate

for pp in [75,90,105]:
    work_dir1 = f'./outdir/pivot_{pp}/daily'
    map_dir = f"./outdir/pivot_{pp}/maps/"
    
    os.makedirs(map_dir, exist_ok=True)
    
    data_dir = Path(work_dir1)
    
    print(f"Making Maps for Pivot {pp}")
    
    for esa in range(1,8):
        print(esa)
        
        h_cnts_map = np.zeros((30,60))        
        exposure = np.zeros((30,60))

        h_rate_map = np.zeros((30,60))
        h_rate_var = np.zeros((30,60))

        h_flux_map = np.zeros((30,60))
        h_fvar_map = np.zeros((30,60))

        back_rate_map = np.zeros((30,60))
        back_rate_var = np.zeros((30,60))
        back_flux_map = np.zeros((30,60))
        back_flux_var = np.zeros((30,60))
        
        stonoise_map = np.zeros((30,60))
        stonoise_var_map = np.zeros((30,60))
        
    
        for filepath in data_dir.glob(f'*esa{esa}.csv'):
            
            file = str(filepath)            
            filename = file.split('/')[-1]
            YD = filename.split('_')[2]

            df = pd.read_csv(file)
            ps_ra = df['ra'].values
            ps_dec = df['dec'].values
            counts = df['counts'].values
            expo = df['expo'].values
            
            for ia in range(0, 60):
                    ra = ps_ra[ia]
                    dec = ps_dec[ia]
                    
                    theta = 90.0 + dec
                    
                    imap = int(ra/deg)
                    if (imap == 60):
                        imap = 0
                    jmap = int(theta/deg)
                    if (jmap == 30):
                        jmap = 0
                    
                    h_cnts_map[jmap,imap] += counts[ia]
                    exposure[jmap,imap] += expo[ia]
                    
        for imap in range(0, nra):
            for jmap in range(0,ncolat):
                
                expo = exposure[jmap,imap]
                energy = esa_energy[esa]

                geo = gf[esa]
                
                # Only look up background rate if this bin has exposure,
                # so we don't depend on YD when there were no input files.
                if (expo > 0.0):
                    brate = get_brate(YD, esa)
                    back_rate_map[jmap,imap] = brate
                    back_rate_var[jmap,imap] = brate/expo
                    h_rate_map[jmap,imap] = h_cnts_map[jmap,imap] / expo
                    h_flux_map[jmap,imap] = h_rate_map[jmap,imap] / (geo * energy)
                    back_flux_map[jmap,imap] = brate / (geo * energy)
                    back_flux_var[jmap,imap] = back_rate_var[jmap,imap] / (geo * energy)**2
                    # represent uncertainty in terms of variance (Poisson counts)
                    h_rate_var[jmap,imap] = h_rate_map[jmap,imap] / expo
                    if (brate > 0.0):
                        stonoise_map[jmap,imap] = h_rate_map[jmap,imap] / ( brate )
                        # Guard against division by zero in stonoise_var components
                        if (back_rate_map[jmap,imap] > 0.0) and (h_rate_map[jmap,imap] > 0.0):
                            stonoise_var_map[jmap,imap] = (
                                h_rate_var[jmap,imap] / back_rate_map[jmap,imap]**2
                                + back_rate_var[jmap,imap] / h_rate_map[jmap,imap]**2
                            )
                        else:
                            stonoise_var_map[jmap,imap] = 0.0
                    # represent uncertainty in terms of variance (Poisson counts)
                    if (h_cnts_map[jmap,imap] > 0.0):
                        h_fvar_map[jmap,imap] = h_flux_map[jmap,imap]**2 / h_cnts_map[jmap,imap]
                    else:
                        h_fvar_map[jmap,imap] = 0.0
                        
        
        sbg_file = pd.DataFrame(stonoise_map)
        sbg_file.to_csv(map_dir+f"/map_stbg_esa{esa}.csv", index=False)
        
        svar_file = pd.DataFrame(stonoise_var_map)
        svar_file.to_csv(map_dir+f"/map_svar_esa{esa}.csv", index=False)
        
        expo_file = pd.DataFrame(exposure)
        expo_file.to_csv(map_dir+f"/map_expo_esa{esa}.csv", index=False)
        
        cnts_file = pd.DataFrame(h_cnts_map)
        cnts_file.to_csv(map_dir+f"/map_cnts_esa{esa}.csv", index=False)
        
        rate_file = pd.DataFrame(h_rate_map)
        rate_file.to_csv(map_dir+f"/map_rate_esa{esa}.csv", index=False)
        
        flux_file = pd.DataFrame(h_flux_map)
        flux_file.to_csv(map_dir+f"/map_flux_esa{esa}.csv", index=False)
        
        h_rate_var_file = pd.DataFrame(h_rate_var)
        h_rate_var_file.to_csv(map_dir+f"/map_rvar_esa{esa}.csv", index=False)
        
        h_fvar_map_file = pd.DataFrame(h_fvar_map)
        h_fvar_map_file.to_csv(map_dir+f"/map_fvar_esa{esa}.csv", index=False)
    
        # Background rate and flux products from the same brate
        backrate_file = pd.DataFrame(back_rate_map)
        backrate_file.to_csv(map_dir+f"/map_brate_esa{esa}.csv", index=False)

        backrate_var_file = pd.DataFrame(back_rate_var)
        backrate_var_file.to_csv(map_dir+f"/map_bvar_esa{esa}.csv", index=False)

        bflux_file = pd.DataFrame(back_flux_map)
        bflux_file.to_csv(map_dir+f"/map_bflux_esa{esa}.csv", index=False)

        bflux_var_file = pd.DataFrame(back_flux_var)
        bflux_var_file.to_csv(map_dir+f"/map_bfvar_esa{esa}.csv", index=False)
