
#!/usr/bin/python
"""
Created on Wed Mar 18 2026
@author: hafijulislam

"""

# June 6, 2026
# several major revisions here: 
# revising g-factors
# multiplicative factors
# the upper one is what we multiple the revised G
# same for lower 
# GeoCorr	Upper uncertainty	Lower uncertainty 
# 0.63529412	1.57407407	0.36728395



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
    1: 0.016,
    2: 0.030,
    3: 0.056,
    4: 0.106,
    5: 0.200,
    6: 0.405,
    7: 0.787,
    8: 1.821
}

gf = {
    1: 7.0e-5,
    2: 7.9e-5,
    3: 9.7e-5,
    4: 11.2e-5,
    5: 14.0e-5,
    6: 17.7e-5,
    7: 22.5e-5,
    8: 6.721e-5
}

dg = {
    1: 4.9e-5,
    2: 5.5e-5,
    3: 6.8e-5,
    4: 3.0e-5,
    5: 4.5e-5,
    6: 2.0e-5,
    7: 1.4e-5,
    8: 6.721e-5
}

scale = 0.63529412

gf = {k: v * scale for k, v in gf.items()}

dg = {k: v * scale for k, v in dg.items()}

gfu = gf.copy()
gfl = gf.copy()

dgu = gf.copy()
dgl = gf.copy()

scale_u = 1.57407407

gfu = {k: v * scale_u for k, v in gfu.items()}
dgu = {k: gfu[k] - gf[k] for k in gf}
dgu = {k: np.sqrt(dgu[k]**2 + dg[k]**2) for k in dg}

scale_l = 0.36728395

gfl = {k: v * scale_l for k, v in gfl.items()}
dgl = {k: gf[k] - gfl[k] for k in gf}
dgl = {k: np.sqrt(dgl[k]**2 + dg[k]**2) for k in dg}

ox_gf = {
    1: 3.54757e-05,
    2: 3.98436e-05,
    3: 6.36456e-05,
    4: 7.28599e-05,
    5: 7.23832e-05,
    6: 6.88855e-05,
    7: 8.00573e-05,
    8: 7.79902e-05,
}


do_gf = {
    1: 1.54757e-05,
    2: 1.98436e-05,
    3: 1.36456e-05,
    4: 1.28599e-05,
    5: 1.23832e-05,
    6: 1.88855e-05,
    7: 1.00573e-05,
    8: 1.79902e-05,
}

scale = 0.63529412

ox_gf = {k: v * scale for k, v in ox_gf.items()}

do_gf = {k: v * scale for k, v in do_gf.items()}

ox_gfu = ox_gf.copy()
ox_gfl = ox_gf.copy()

do_gu = ox_gf.copy()
do_gl = ox_gf.copy()

scale_u = 1.57407407

ox_gfu = {k: v * scale_u for k, v in ox_gfu.items()}
do_gu = {k: ox_gfu[k] - ox_gf[k] for k in ox_gf}
do_gu = {k: np.sqrt(do_gu[k]**2 + do_gf[k]**2) for k in do_gf}

scale_l = 0.36728395

ox_gfl = {k: v * scale_l for k, v in ox_gfl.items()}
do_gl = {k: ox_gf[k] - ox_gfl[k] for k in ox_gf}
do_gl = {k: np.sqrt(do_gl[k]**2 + do_gf[k]**2) for k in do_gf}

## Get background Rate

def get_brate(YD,esa):
    
    backfile = './config_files/imap_lo_H_background.csv'
    
    df = pd.read_csv(backfile,sep=',', names=['YD','start','end','bin_start','bin_end','Lo','esa1','esa2','esa3','esa4','esa5','esa6','esa7','type'])
    
    brate = df[(df['YD']==int(YD)) & (df['type']=='rate')][f'esa{esa}'].values[0]
    
    return brate

for pp in [75,90,105]:
    pivot_deg = pp + 4.0
    pivot = np.radians(pivot_deg)
    
    work_dir1 = f'./outdir/pivot_{pp}/daily'
    map_dir = f"./outdir/pivot_{pp}/maps/"
    
    os.makedirs(map_dir, exist_ok=True)
    
    data_dir = Path(work_dir1)
    
    print(f"Making Maps for Pivot {pp}")
    
    for esa in range(1,8):
        print(esa)

        map_manifest_rows = []
        
        h_cnts_map = np.zeros((30,60))        
        exposure = np.zeros((30,60))

        h_rate_map = np.zeros((30,60))
        h_rate_var = np.zeros((30,60))

        h_flux_map = np.zeros((30,60))
        h_fvar_map = np.zeros((30,60))
        h_fser_map = np.zeros((30,60))
        h_fseu_map = np.zeros((30,60))
        h_fsel_map = np.zeros((30,60))
        h_fvto_map = np.zeros((30,60))

        back_rate_map = np.zeros((30,60))
        back_rate_var = np.zeros((30,60))
        back_flux_map = np.zeros((30,60))
        back_flux_var = np.zeros((30,60))
        
        stonoise_map = np.zeros((30,60))
        stonoise_var_map = np.zeros((30,60))

        cosalpha_map = np.zeros((30,60))
        
        for filepath in data_dir.glob(f'*esa{esa}.csv'):
            
            file = str(filepath)            
            filename = file.split('/')[-1]
            YD = filename.split('_')[2]

            df = pd.read_csv(file)

            # Capture provenance for this daily file if present
            prov_cols = [
                "date_yyyymmdd",
                "yd",
                "repoint",
                "pivot",
                "l1b_product",
                "l1b_filename",
                "l1b_path",
            ]

            if all(c in df.columns for c in prov_cols):
                prov = df[prov_cols].iloc[0].to_dict()
            else:
                prov = {
                    "date_yyyymmdd": "",
                    "yd": YD,
                    "repoint": "",
                    "pivot": pp,
                    "l1b_product": "",
                    "l1b_filename": "",
                    "l1b_path": "",
                }

            prov["esa"] = esa
            prov["daily_csv"] = filename
            prov["daily_csv_path"] = str(Path(file).resolve())
            map_manifest_rows.append(prov)

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
                    
                    # Bin center angle in radians
                    alpha = np.radians((ia + 0.5) * 6.0)

                    # coord system with x = NEP, y = RAM, z = Sun
                    # look_x = np.sin(pivot)*np.cos(alpha)
                    look_y = np.sin(pivot)*np.sin(alpha)
                    # look_z = np.cos(pivot)
                    cosalpha = look_y

                    cosalpha_map[jmap, imap] = cosalpha

                    h_cnts_map[jmap,imap] += counts[ia]
                    exposure[jmap,imap] += expo[ia]
                    
        for imap in range(0, nra):
            for jmap in range(0,ncolat):
                
                expo = exposure[jmap,imap]
                energy = esa_energy[esa]

                geo = gf[esa]
                dge = dg[esa]
                dgeu = dgu[esa]
                dgel = dgl[esa]

                # Only look up background rate if this bin has exposure,
                # so we don't depend on YD when there were no input files.
                if (expo > 0.0):
                    brate = get_brate(YD, esa)
                    back_rate_map[jmap,imap] = brate
                    back_rate_var[jmap,imap] = brate/expo
                    h_rate_map[jmap,imap] = h_cnts_map[jmap,imap] / expo
                    h_flux_map[jmap,imap] = h_rate_map[jmap,imap] / (geo * energy)

                    h_mid = h_flux_map[jmap,imap]
                    if geo > dgel:
                        h_hi = h_mid * geo / (geo - dgel)
                        h_lo = h_mid * geo / (geo + dgeu)

                        dh_hi = h_hi - h_mid
                        dh_lo = h_mid - h_lo

                        h_fser_map[jmap, imap] = np.sqrt(dh_hi * dh_lo)
                        h_fseu_map[jmap, imap] = dh_hi
                        h_fsel_map[jmap, imap] = dh_lo
                    else:
                        h_fser_map[jmap, imap] = np.nan
                        h_fseu_map[jmap, imap] = np.nan
                        h_fsel_map[jmap, imap] = np.nan


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
                        h_fvto_map[jmap,imap] = (h_flux_map[jmap,imap]**2 / h_cnts_map[jmap,imap]) + h_fser_map[jmap,imap]**2
                    else:
                        h_fvar_map[jmap,imap] = 0.0
                        h_fvto_map[jmap,imap] = h_fser_map[jmap,imap]**2
                        
        
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

        sflx_file = pd.DataFrame(h_fser_map)
        sflx_file.to_csv(map_dir+f"/map_fser_esa{esa}.csv", index=False)
        
        sflu_file = pd.DataFrame(h_fseu_map)
        sflu_file.to_csv(map_dir+f"/map_fseu_esa{esa}.csv", index=False)

        sfll_file = pd.DataFrame(h_fsel_map)
        sfll_file.to_csv(map_dir+f"/map_fsel_esa{esa}.csv", index=False)
        
        h_rate_var_file = pd.DataFrame(h_rate_var)
        h_rate_var_file.to_csv(map_dir+f"/map_rvar_esa{esa}.csv", index=False)
        
        h_fvar_map_file = pd.DataFrame(h_fvar_map)
        h_fvar_map_file.to_csv(map_dir+f"/map_fvar_esa{esa}.csv", index=False)
    
        h_fvto_map_file = pd.DataFrame(h_fvto_map)
        h_fvto_map_file.to_csv(map_dir+f"/map_fvto_esa{esa}.csv", index=False)

        # Background rate and flux products from the same brate
        backrate_file = pd.DataFrame(back_rate_map)
        backrate_file.to_csv(map_dir+f"/map_brate_esa{esa}.csv", index=False)

        backrate_var_file = pd.DataFrame(back_rate_var)
        backrate_var_file.to_csv(map_dir+f"/map_bvar_esa{esa}.csv", index=False)

        bflux_file = pd.DataFrame(back_flux_map)
        bflux_file.to_csv(map_dir+f"/map_bflux_esa{esa}.csv", index=False)

        bflux_var_file = pd.DataFrame(back_flux_var)
        bflux_var_file.to_csv(map_dir+f"/map_bfvar_esa{esa}.csv", index=False)

        cosalpha_file = pd.DataFrame(cosalpha_map)
        cosalpha_file.to_csv(map_dir+f"/map_cosalpha_esa{esa}.csv", index=False)

        # Write map-level provenance manifest for this pivot/ESA
        if map_manifest_rows:

            manifest_df = pd.DataFrame(map_manifest_rows)

            manifest_df["date_yyyymmdd"] = manifest_df["date_yyyymmdd"].astype(str)
            manifest_df["repoint"] = manifest_df["repoint"].astype(str)

            manifest_df = (
                manifest_df
                .drop_duplicates()
                .sort_values(
                    by=["date_yyyymmdd", "repoint"],
                    ascending=[True, True]
                )
            )

            manifest_df.to_csv(
                map_dir + f"/map_l1b_manifest_esa{esa}.csv",
                index=False
            )
