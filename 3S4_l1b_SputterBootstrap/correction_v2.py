#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 12:32:33 2026

@author: hafijulislam
"""
import numpy as np
import pandas as pd
import os
from scipy.ndimage import generic_filter


hy_esa_energy = {
    1:0.016,2:0.030,3:0.056,4:0.106,
    5:0.200,6:0.404,7:0.787,8:1.6527
}

hy_gf = {
    1:7.0e-5,2:7.9e-5,3:9.7e-5,4:11.2e-5,
    5:14.0e-5,6:17.7e-5,7:22.5e-5
}

sput_cor = {
    14:0.236,24:0.372,34:0.898,44:0.891,
    54:0.037,56:0.32,66:0.32,76:0.22
}

a = {
    (1,2):0.03,(1,3):0.01,
    (2,3):0.05,(2,4):0.02,(2,5):0.01,
    (3,4):0.09,(3,5):0.03,(3,6):0.016,(3,7):0.01,
    (4,5):0.16,(4,6):0.068,(4,7):0.016,(4,8):0.01,
    (5,6):0.29,(5,7):0.068,(5,8):0.016,
    (6,7):0.52,(6,8):0.061,
    (7,8):0.75
}


for pp in [75,90,105]:

    work_dir_hydrogen=f'../3S2_l1b_quickmaps/outdir/pivot_{pp}/maps/'
    work_dir_oxygen=f'../3S3_l1b_Oxy_quickmaps/outdir/pivot_{pp}/maps/'
    out_dir=f'./outdir/pivot_{pp}/maps/'

    os.makedirs(out_dir,exist_ok=True)

    ox_cnts_list=[]
    hy_cnts_list=[]
    hy_expo_list=[]

    for esa in range(1,8):

        ox_cnts=np.loadtxt(work_dir_oxygen+f"map_cnts_esa{esa}.csv",delimiter=',',skiprows=1)
        hy_cnts=np.loadtxt(work_dir_hydrogen+f"map_cnts_esa{esa}.csv",delimiter=',',skiprows=1)
        hy_expo = np.loadtxt(work_dir_hydrogen + f"map_expo_esa{esa}.csv", delimiter=',', skiprows=1)
        np.savetxt(out_dir + f"map_expo_esa{esa}.csv", hy_expo, delimiter=',')

        ox_cnts_list.append(ox_cnts)
        hy_cnts_list.append(hy_cnts)
        hy_expo_list.append(hy_expo)

    ox_cnts=np.array(ox_cnts_list)
    hy_cnts=np.array(hy_cnts_list)
    hy_expo=np.array(hy_expo_list)


    hy_cnts_var = hy_cnts
    ox_cnts_var = ox_cnts


    hy_sput_flux_list=[]
    hy_sput_rate_list=[]
    hy_sput_flux_var_list=[]
    hy_sput_rate_var_list=[]


    for tar_esa in range(1,8):

        if tar_esa == 5:

            cor_cnts = (
                hy_cnts[4]
                - ox_cnts[3]*sput_cor[54]
                - ox_cnts[5]*sput_cor[56]
            )

            cor_cnts_var = (
                hy_cnts_var[4]
                + (sput_cor[54]**2)*ox_cnts_var[3]
                + (sput_cor[56]**2)*ox_cnts_var[5]
            )

        elif tar_esa == 6:

            cor_cnts = hy_cnts[5] - ox_cnts[5]*sput_cor[66]

            cor_cnts_var = (
                hy_cnts_var[5]
                + (sput_cor[66]**2)*ox_cnts_var[5]
            )

        elif tar_esa == 7:

            cor_cnts = hy_cnts[6] - ox_cnts[5]*sput_cor[76]

            cor_cnts_var = (
                hy_cnts_var[6]
                + (sput_cor[76]**2)*ox_cnts_var[5]
            )

        else:

            coeff=sput_cor[tar_esa*10+4]

            cor_cnts = hy_cnts[tar_esa-1] - ox_cnts[3]*coeff

            cor_cnts_var = (
                hy_cnts_var[tar_esa-1]
                + (coeff**2)*ox_cnts_var[3]
            )


        cor_rate=np.divide(
            cor_cnts,
            hy_expo[tar_esa-1],
            out=np.zeros_like(cor_cnts),
            where=hy_expo[tar_esa-1]!=0
        )

        cor_rate_var=np.divide(
            cor_cnts_var,
            hy_expo[tar_esa-1]**2,
            out=np.zeros_like(cor_cnts_var),
            where=hy_expo[tar_esa-1]!=0
        )


        cor_flux=cor_rate/(hy_esa_energy[tar_esa]*hy_gf[tar_esa])

        cor_flux_var=cor_rate_var/(hy_esa_energy[tar_esa]*hy_gf[tar_esa])**2


        hy_sput_flux_list.append(cor_flux)
        hy_sput_rate_list.append(cor_rate)

        hy_sput_flux_var_list.append(cor_flux_var)
        hy_sput_rate_var_list.append(cor_rate_var)


    hy_sput_flux=np.array(hy_sput_flux_list)
    hy_sput_rate=np.array(hy_sput_rate_list)

    hy_sput_flux_var=np.array(hy_sput_flux_var_list)
    hy_sput_rate_var=np.array(hy_sput_rate_var_list)


    hy_sput_flux=np.where(hy_sput_flux<0,0,hy_sput_flux)
    hy_sput_rate=np.where(hy_sput_rate<0,0,hy_sput_rate)

    # ESA-8 flux extrapolation

    E6=hy_esa_energy[6]
    E7=hy_esa_energy[7]
    E8=hy_esa_energy[8]

    hy6=hy_sput_flux[5]
    hy7=hy_sput_flux[6]

    hy_mask=(hy6>0)&(hy7>0)

    hy_gamma=np.zeros_like(hy6)

    hy_gamma[hy_mask] = -np.log(hy7[hy_mask]/hy6[hy_mask])/np.log(E7/E6)

    hy8=np.zeros_like(hy7)

    hy8[hy_mask]=hy7[hy_mask]*(E8/E7)**(-hy_gamma[hy_mask])


    hy_gamma_nan=np.where(hy_mask,hy_gamma,np.nan)

    def local_median_valid(values):
        v=values[~np.isnan(values)]
        return np.nanmedian(v) if len(v)>0 else np.nan

    hy_gamma_filled=generic_filter(
        hy_gamma_nan,local_median_valid,size=3,mode='constant',cval=np.nan
    )

    hy7_only_mask=(hy7>0)&(hy6<=0)

    use_local=hy7_only_mask & np.isfinite(hy_gamma_filled)

    hy8[use_local]=hy7[use_local]*(E8/E7)**(-hy_gamma_filled[use_local])

    need_fallback=hy7_only_mask & ~np.isfinite(hy_gamma_filled)

    if np.any(need_fallback):

        gamma_global=np.nanmedian(hy_gamma[hy_mask])

        hy8[need_fallback]=hy7[need_fallback]*(E8/E7)**(-gamma_global)

    # ESA-8 variance propagation
    
    hy8_var = hy_sput_flux_var[6]

    hy_sput_flux = np.concatenate((hy_sput_flux, hy8[None, :, :]), axis=0)
    hy_sput_flux_var = np.concatenate((hy_sput_flux_var, hy8_var[None, :, :]), axis=0)

    
    # Bootstrap correction

    boot_flux=[]
    boot_var=[]

    for i in range(1,8):

        cor=hy_sput_flux[i-1]
        var=hy_sput_flux_var[i-1]

        for j in range(i+1,9):

            if (i,j) in a:

                cor -= a[(i,j)]*hy_sput_flux[j-1]
                var += (a[(i,j)]**2)*hy_sput_flux_var[j-1]

        cor=np.where(cor<0,0,cor)

        boot_flux.append(cor)
        boot_var.append(var)

    boot_flux=np.array(boot_flux)
    boot_var=np.array(boot_var)


    for esa in range(1,8):

        pd.DataFrame(hy_sput_rate[esa-1]).to_csv(
            out_dir+f"map_rate_{esa}_Hy_sput_cor.csv",index=False)

        pd.DataFrame(hy_sput_rate_var[esa-1]).to_csv(
            out_dir+f"map_rate_{esa}_Hy_sput_var.csv",index=False)

        pd.DataFrame(hy_sput_flux[esa-1]).to_csv(
            out_dir+f"map_flux_{esa}_Hy_sput_cor.csv",index=False)

        pd.DataFrame(hy_sput_flux_var[esa-1]).to_csv(
            out_dir+f"map_flux_{esa}_Hy_sput_var.csv",index=False)

        pd.DataFrame(boot_flux[esa-1]).to_csv(
            out_dir+f"map_flux_{esa}_Hy_boot_cor.csv",index=False)

        pd.DataFrame(boot_var[esa-1]).to_csv(
            out_dir+f"map_flux_{esa}_Hy_boot_var.csv",index=False)