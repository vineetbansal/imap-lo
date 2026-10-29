#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 17:33:23 2025

@author: hafijulislam

Sputtering and Bootstrap Correction for IBEX-Lo instrument
"""

import numpy as np
import pandas as pd
import os
from scipy.ndimage import generic_filter

esa_energy = {
    1: 0.016,
    2: 0.030,
    3: 0.056,
    4: 0.106,
    5: 0.200,
    6: 0.404,
    7: 0.787,
    8: 1.6527 #Calculated,  E7 * 2.1
}

## Coefficient for bootstrap correction

a12 = 0.03
a13 = 0.01

a23 = 0.05
a24 = 0.02
a25 = 0.01

a34 = 0.09
a35 = 0.03
a36 = 0.016
a37 = 0.01

a45 = 0.16
a46 = 0.068
a47 = 0.016
a48 = 0.01

a56 = 0.29
a57 = 0.068
a58 = 0.016

a67 = 0.52
a68 = 0.061

a78 = 0.75

E6 = esa_energy[6]
E7 = esa_energy[7]
E8 = esa_energy[8]

for pp in [75,90,105]:

    work_dir_hydrogen = f'../3S2_l1b_quickmaps/outdir/pivot_{pp}/maps/'
    work_dir_oxygen = f'../3S3_l1b_Oxy_quickmaps/outdir/pivot_{pp}/maps/'
    
    out_dir = f'./outdir/pivot_{pp}/maps/'
    
    os.makedirs(out_dir, exist_ok=True)
    
    ox_flux_list = []
    hy_flux_list = []
    
    hy_cnts_list = []
    
    
    for esa in range(1,8):
        str_esa = str(esa)
        ox_flux_file = work_dir_oxygen+f"map_flux_esa{str_esa}.csv"
        hy_flux_file = work_dir_hydrogen+f"map_flux_esa{str_esa}.csv"
        hy_cnts_file = work_dir_hydrogen+f"map_cnts_esa{str_esa}.csv"
        
        ox_flux = np.loadtxt(ox_flux_file, delimiter=',',skiprows=1)
        hy_flux = np.loadtxt(hy_flux_file, delimiter=',',skiprows=1)
        hy_cnts = np.loadtxt(hy_cnts_file, delimiter=',',skiprows=1)
        
        ox_flux_list.append(ox_flux)
        hy_flux_list.append(hy_flux)
        hy_cnts_list.append(hy_cnts)
    
    ## Calculate Uncertainties
    hy_flux = np.array(hy_flux_list)
    hy_cnts = np.array(hy_cnts_list)
    
    hy_unc = np.zeros_like(hy_flux)
    unc_mask = hy_cnts>0
    hy_unc[unc_mask] = hy_flux[unc_mask]/np.sqrt(hy_cnts[unc_mask])
        
    # Calculate Flux for ESA-8

    hy6 = hy_flux_list[5]
    hy7 = hy_flux_list[6]
    
    # masks to avoid log/division issues
    hy_mask = (hy6 > 0) & (hy7 > 0)
    
    # gamma maps
    hy_gamma = np.zeros_like(hy6)
    
    hy_gamma[hy_mask] = -np.log(hy7[hy_mask] / hy6[hy_mask]) / np.log(E7 / E6)
    
    # ESA 8 flux maps from ESA 7
    hy8 = np.zeros_like(hy7)
    
    hy8[hy_mask] = hy7[hy_mask] * (E8 / E7) ** (-hy_gamma[hy_mask])

    # For pixels with hy7>0 but hy6=0: fill gamma from valid surrounding pixels
    hy_gamma_nan = np.where(hy_mask, hy_gamma, np.nan)

    def local_median_valid(values):
        """Return median of finite values; NaN if none."""
        v = values[~np.isnan(values)]
        return np.nanmedian(v) if len(v) > 0 else np.nan

    size = 3
    hy_gamma_filled = generic_filter(hy_gamma_nan, local_median_valid, size=size, mode='constant', cval=np.nan)
    hy7_only_mask = (hy7 > 0) & (hy6 <= 0)
    use_local = hy7_only_mask & np.isfinite(hy_gamma_filled)
    hy8[use_local] = hy7[use_local] * (E8 / E7) ** (-hy_gamma_filled[use_local])
    
    # Pixels with no valid neighbors use global median
    
    need_fallback = hy7_only_mask & ~np.isfinite(hy_gamma_filled)
    if np.any(need_fallback):
        gamma_global = np.nanmedian(hy_gamma[hy_mask])
        hy8[need_fallback] = hy7[need_fallback] * (E8 / E7) ** (-gamma_global)

    hy_flux_list.append(hy8)
    
    ## Calculate the Corrected Flux and Uncertainties for each esa
    
    tar_esa =1
    cor_boot_1 = hy_flux_list[tar_esa-1] - a12*hy_flux_list[tar_esa] - a13*hy_flux_list[tar_esa+1] 
    cor_boot_1 = np.where(cor_boot_1<0,0,cor_boot_1) # Assigning every negetive value to be zero
    
    cor_boot_unc_1 = hy_unc[tar_esa-1]**2 + (a12**2) * hy_unc[tar_esa]**2 + (a13**2) * hy_unc[tar_esa+1]**2
    
    
    tar_esa =2
    cor_boot_2 = hy_flux_list[tar_esa-1] - a23*hy_flux_list[tar_esa] - a24*hy_flux_list[tar_esa+1] - a25*hy_flux_list[tar_esa+2]  
    cor_boot_2 = np.where(cor_boot_2<0,0,cor_boot_2)
    
    cor_boot_unc_2 = hy_unc[tar_esa-1]**2 + (a23**2) * hy_unc[tar_esa]**2 + (a24**2) * hy_unc[tar_esa+1]**2+ (a25**2) * hy_unc[tar_esa+2]**2
    
    tar_esa =3
    cor_boot_3 = hy_flux_list[tar_esa-1] - a34*hy_flux_list[tar_esa] - a35*hy_flux_list[tar_esa+1] - a36*hy_flux_list[tar_esa+2] - a37*hy_flux_list[tar_esa+3] 
    cor_boot_3 = np.where(cor_boot_3<0,0,cor_boot_3)
    
    cor_boot_unc_3 = hy_unc[tar_esa-1]**2 + (a34**2) * hy_unc[tar_esa]**2 + (a35**2) * hy_unc[tar_esa+1]**2 + (a36**2) * hy_unc[tar_esa+2]**2 + (a37**2) * hy_unc[tar_esa+3]**2
    
    tar_esa =4
    cor_boot_4 = hy_flux_list[tar_esa-1] - a45*hy_flux_list[tar_esa] - a46*hy_flux_list[tar_esa+1] - a47*hy_flux_list[tar_esa+2] - a48*hy_flux_list[tar_esa+3]
    cor_boot_4 = np.where(cor_boot_4<0,0,cor_boot_4)
    
    cor_boot_unc_4 = hy_unc[tar_esa-1]**2 + (a45**2) * hy_unc[tar_esa]**2 + (a46**2) * hy_unc[tar_esa+1]**2 + (a47**2) * hy_unc[tar_esa+2]**2 #+ (a48**2) * hy_unc[tar_esa+3]**2
    
    tar_esa = 5    
    cor_sput_5 = hy_flux_list[tar_esa-1] - ox_flux_list[tar_esa-1] * 0.15 
    cor_boot_5 = cor_sput_5 - a56*hy_flux_list[tar_esa] - a57*hy_flux_list[tar_esa+1] - a58*hy_flux_list[tar_esa+2] 
    cor_boot_5 = np.where(cor_boot_5<0,0,cor_boot_5)
    
    cor_boot_unc_5 = hy_unc[tar_esa-1]**2 + (a56**2) * hy_unc[tar_esa]**2 + (a57**2) * hy_unc[tar_esa+1]**2 #+ (a58**2) * hy_unc[tar_esa+2]**2
    
    tar_esa = 6
    cor_sput_6 = hy_flux_list[tar_esa-1] - ox_flux_list[tar_esa-1] * 0.01 
    cor_boot_6 = cor_sput_6 - a67*hy_flux_list[tar_esa] - a68*hy_flux_list[tar_esa+1]
    cor_boot_6 = np.where(cor_boot_6<0,0,cor_boot_6)
    
    cor_boot_unc_6 = hy_unc[tar_esa-1]**2 + (a67**2) * hy_unc[tar_esa]**2 #+ (a68**2) * hy_unc[tar_esa+1]**2 
    
    tar_esa = 7
    cor_boot_7 = hy_flux_list[tar_esa-1] - a78*hy_flux_list[tar_esa]
    cor_boot_7 = np.where(cor_boot_7<0,0,cor_boot_7)
    
    cor_boot_unc_7 = hy_unc[tar_esa-1]**2
    
    ## Produce Sputtering Corrected Maps
    
    flux_file1 = pd.DataFrame(cor_sput_5)
    flux_file1.to_csv(out_dir+"map_flux_5_Hy_sput_cor.csv", index=False)
    
    flux_file3 = pd.DataFrame(cor_sput_6)
    flux_file3.to_csv(out_dir+"map_flux_6_Hy_sput_cor.csv", index=False)
    
    cor_boot = {
        1: cor_boot_1,
        2: cor_boot_2,
        3: cor_boot_3,
        4: cor_boot_4,
        5: cor_boot_5,
        6: cor_boot_6,
        7: cor_boot_7
    }
    
    cor_boot_unc = {
        1: cor_boot_unc_1,
        2: cor_boot_unc_2,
        3: cor_boot_unc_3,
        4: cor_boot_unc_4,
        5: cor_boot_unc_5,
        6: cor_boot_unc_6,
        7: cor_boot_unc_7
    }
    
    ## Produce Bootstrapped Corrected Maps
    
    for esa in range(1, 8):
        flux_file = pd.DataFrame(cor_boot[esa])
        flux_file.to_csv(out_dir+f"map_flux_{esa}_Hy_boot_cor.csv", index=False)
        
        func_file = pd.DataFrame(cor_boot_unc[esa])
        func_file.to_csv(out_dir+f"map_func_{esa}_Hy_boot_cor.csv", index=False)


