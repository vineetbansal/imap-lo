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
    1:0.01633,2:0.03047,3:0.05576,4:0.10626,
    5:0.20004,6:0.40496,7:0.78729,8:1.6527
}

hy_gf = {
    1:7.0e-5,2:7.9e-5,3:9.7e-5,4:11.2e-5,
    5:14.0e-5,6:17.7e-5,7:22.5e-5
}

hy_dg = {
    1: 4.9e-5,2: 5.5e-5,3: 6.8e-5,4: 3.0e-5,
    5: 4.5e-5,6: 2.0e-5,7: 1.4e-5
}

sput_cor = {
    14:0.236,24:0.372,34:0.898,44:0.891,
    54:0.037,56:0.32,66:0.32,76:0.22
}

scale = 0.63529412

hy_gf = {k: v * scale for k, v in hy_gf.items()}

hy_dg = {k: v * scale for k, v in hy_dg.items()}

hy_gfu = hy_gf.copy()
hy_gfl = hy_gf.copy()

hy_dgu = hy_gf.copy()
hy_dgl = hy_gf.copy()

scale_u = 1.57407407

hy_gfu = {k: v * scale_u for k, v in hy_gfu.items()}
hy_dgu = {k: hy_gfu[k] - hy_gf[k] for k in hy_gf}
hy_dgu = {k: np.sqrt(hy_dgu[k]**2 + hy_dg[k]**2) for k in hy_dg}

scale_l = 0.36728395

hy_gfl = {k: v * scale_l for k, v in hy_gfl.items()}
hy_dgl = {k: hy_gf[k] - hy_gfl[k] for k in hy_gf}
hy_dgl = {k: np.sqrt(hy_dgl[k]**2 + hy_dg[k]**2) for k in hy_dg}

# modified scale on 6/4/26 
# this is because the amount of sputtering went down by 0.5
scale = 0.5

a = {
    (1,2):0.03*scale, (1,3):0.01*scale,
    (2,3):0.05*scale,(2,4):0.02*scale,(2,5):0.01*scale,
    (3,4):0.09*scale,(3,5):0.03*scale,(3,6):0.016*scale,(3,7):0.01*scale,
    (4,5):0.16*scale,(4,6):0.068*scale,(4,7):0.016*scale,(4,8):0.01*scale,
    (5,6):0.29*scale,(5,7):0.068*scale,(5,8):0.016*scale,
    (6,7):0.52*scale,(6,8):0.061*scale,
    (7,8):0.75*scale
}

scale = 0.25

a_up = {
    (1,2):0.03*scale, (1,3):0.01*scale,
    (2,3):0.05*scale,(2,4):0.02*scale,(2,5):0.01*scale,
    (3,4):0.09*scale,(3,5):0.03*scale,(3,6):0.016*scale,(3,7):0.01*scale,
    (4,5):0.16*scale,(4,6):0.068*scale,(4,7):0.016*scale,(4,8):0.01*scale,
    (5,6):0.29*scale,(5,7):0.068*scale,(5,8):0.016*scale,
    (6,7):0.52*scale,(6,8):0.061*scale,
    (7,8):0.75*scale
}

scale = 1.0

a_lo = {
    (1,2):0.03*scale, (1,3):0.01*scale,
    (2,3):0.05*scale,(2,4):0.02*scale,(2,5):0.01*scale,
    (3,4):0.09*scale,(3,5):0.03*scale,(3,6):0.016*scale,(3,7):0.01*scale,
    (4,5):0.16*scale,(4,6):0.068*scale,(4,7):0.016*scale,(4,8):0.01*scale,
    (5,6):0.29*scale,(5,7):0.068*scale,(5,8):0.016*scale,
    (6,7):0.52*scale,(6,8):0.061*scale,
    (7,8):0.75*scale
}

for pp in [75,90,105]:

    work_dir_hydrogen=f'../3S5_l1b_ram_maps/outdir/pivot_{pp}/maps/'
    work_dir_oxygen=f'../3S6_l1b_oxy_ram_maps/outdir/pivot_{pp}/maps/'
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
    hy_sput_flux_unc_list=[]
    hy_sput_flux_unl_list=[]
    hy_sput_flux_unu_list=[]

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

        # Subtracting the sputtered oxygen counts can take a low-count pixel
        # below zero, which is not a rate the instrument can have observed.
        # Clamp here, at the source, so the flux and both of its geometric
        # factor excursions below are non-negative: unu and unl each carry the
        # sign of the flux, and sqrt(unu*unl) would otherwise cancel two
        # negatives into a spurious error bar on a pixel reported as empty.
        cor_rate = np.maximum(cor_rate, 0.0)

        cor_rate_var=np.divide(
            cor_cnts_var,
            hy_expo[tar_esa-1]**2,
            out=np.zeros_like(cor_cnts_var),
            where=hy_expo[tar_esa-1]!=0
        )


        cor_flux=cor_rate/(hy_esa_energy[tar_esa]*hy_gf[tar_esa])

        cor_flux_var=cor_rate_var/(hy_esa_energy[tar_esa]*hy_gf[tar_esa])**2

        cor_flux_up=cor_flux * hy_gf[tar_esa] / (hy_gf[tar_esa] - hy_dgl[tar_esa])
        cor_flux_lo=cor_flux * hy_gf[tar_esa] / (hy_gf[tar_esa] + hy_dgu[tar_esa])
        cor_flux_unu = cor_flux_up - cor_flux
        cor_flux_unl =  cor_flux - cor_flux_lo
        cor_flux_unc=np.sqrt(cor_flux_unu*cor_flux_unl)

        hy_sput_flux_list.append(cor_flux)
        hy_sput_rate_list.append(cor_rate)

        hy_sput_flux_var_list.append(cor_flux_var)
        hy_sput_rate_var_list.append(cor_rate_var)

        hy_sput_flux_unc_list.append(cor_flux_unc)
        hy_sput_flux_unu_list.append(cor_flux_unu)
        hy_sput_flux_unl_list.append(cor_flux_unl)

    hy_sput_flux=np.array(hy_sput_flux_list)
    hy_sput_rate=np.array(hy_sput_rate_list)

    hy_sput_flux_var=np.array(hy_sput_flux_var_list)
    hy_sput_rate_var=np.array(hy_sput_rate_var_list)

    hy_sput_flux=np.where(hy_sput_flux<0,0,hy_sput_flux)
    hy_sput_rate=np.where(hy_sput_rate<0,0,hy_sput_rate)

    hy_sput_flux_unc=np.array(hy_sput_flux_unc_list)
    hy_sput_flux_unc=np.where(hy_sput_flux_unc<0,0,hy_sput_flux_unc)

    hy_sput_flux_unl=np.array(hy_sput_flux_unl_list)
    hy_sput_flux_unl=np.where(hy_sput_flux_unl<0,0,hy_sput_flux_unl)

    hy_sput_flux_unu=np.array(hy_sput_flux_unu_list)
    hy_sput_flux_unu=np.where(hy_sput_flux_unu<0,0,hy_sput_flux_unu)

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

        if np.any(hy_mask):
            gamma_global = np.nanmedian(hy_gamma[hy_mask])
        else:
            gamma_global = 1.6   # or whatever default spectral index you trust

        hy8[need_fallback]=hy7[need_fallback]*(E8/E7)**(-gamma_global)

    # ESA-8 variance propagation
    
    hy8_var = hy_sput_flux_var[6]
    # this is an approximation, and not the best

    hy_sput_flux = np.concatenate((hy_sput_flux, hy8[None, :, :]), axis=0)
    hy_sput_flux_var = np.concatenate((hy_sput_flux_var, hy8_var[None, :, :]), axis=0)

    # Bootstrap correction

    boot_flux=[]
    boot_var=[]
    
    boot_lo=[]
    boot_up=[]

    boot_unc=[]
    boot_unl=[] 
    boot_unu=[]

    for i in range(1,8):

        cor = hy_sput_flux[i-1].copy()
        clo = hy_sput_flux[i-1].copy()
        cup = hy_sput_flux[i-1].copy()
        var = hy_sput_flux_var[i-1].copy()
        
        for j in range(i+1,9):

            if (i,j) in a:

                cor -= a[(i,j)]*hy_sput_flux[j-1]
                clo -= a_lo[(i,j)]*hy_sput_flux[j-1]
                cup -= a_up[(i,j)]*hy_sput_flux[j-1]
                var += (a[(i,j)]**2)*hy_sput_flux_var[j-1]

        cor=np.where(cor<0,0,cor)
        clo=np.where(clo<0,0,clo)
        cup=np.where(cup<0,0,cup)   

        boot_flux.append(cor)
        boot_lo.append(clo)
        boot_up.append(cup)
        boot_var.append(var)

    boot_flux=np.array(boot_flux)
    boot_lo= np.array(boot_lo)
    boot_up= np.array(boot_up)
    boot_var=np.array(boot_var)
    boot_unc = np.zeros_like(boot_flux)
    boot_unl = np.zeros_like(boot_flux)
    boot_unu = np.zeros_like(boot_flux)

    for esa in range(1, 8):
        boot_lo[esa-1] = (boot_lo[esa-1]) * hy_gf[esa] / (hy_gf[esa] + hy_dgu[esa]  )
        boot_up[esa-1] = (boot_up[esa-1]) * hy_gf[esa] / (hy_gf[esa] - hy_dgl[esa]  )
        boot_unl[esa-1] = boot_flux[esa-1] - boot_lo[esa-1]
        boot_unu[esa-1] = boot_up[esa-1] - boot_flux[esa-1]
        boot_unc[esa-1] = np.sqrt(boot_unl[esa-1]* boot_unu[esa-1])
    
    for esa in range(1,8):

        pd.DataFrame(hy_sput_rate[esa-1]).to_csv(
            out_dir+f"map_rate_{esa}_Hy_sput_cor.csv",index=False)

        pd.DataFrame(hy_sput_rate_var[esa-1]).to_csv(
            out_dir+f"map_rate_{esa}_Hy_sput_var.csv",index=False)

        pd.DataFrame(hy_sput_flux[esa-1]).to_csv(
            out_dir+f"map_flux_{esa}_Hy_sput_cor.csv",index=False)

        pd.DataFrame(hy_sput_flux_var[esa-1]).to_csv(
            out_dir+f"map_flux_{esa}_Hy_sput_var.csv",index=False)
        
        pd.DataFrame(hy_sput_flux_unc[esa-1]).to_csv(
            out_dir+f"map_flux_{esa}_Hy_sput_unc.csv",index=False)

        pd.DataFrame(hy_sput_flux_unu[esa-1]).to_csv(
            out_dir+f"map_flux_{esa}_Hy_sput_unu.csv",index=False)

        pd.DataFrame(hy_sput_flux_unl[esa-1]).to_csv(
            out_dir+f"map_flux_{esa}_Hy_sput_unl.csv",index=False)

        pd.DataFrame(boot_flux[esa-1]).to_csv(
            out_dir+f"map_flux_{esa}_Hy_boot_cor.csv",index=False)

        pd.DataFrame(boot_var[esa-1]).to_csv(
            out_dir+f"map_flux_{esa}_Hy_boot_var.csv",index=False)
        
        pd.DataFrame(boot_unc[esa-1]).to_csv(
            out_dir+f"map_flux_{esa}_Hy_boot_unc.csv",index=False)
        
        pd.DataFrame(boot_unl[esa-1]).to_csv(
            out_dir+f"map_flux_{esa}_Hy_boot_unl.csv",index=False)
        
        pd.DataFrame(boot_unu[esa-1]).to_csv(
            out_dir+f"map_flux_{esa}_Hy_boot_unu.csv",index=False)
