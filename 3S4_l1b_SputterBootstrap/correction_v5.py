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


# Copied from imap_processing, branch vb/issue3349b (commit 304a8086). That
# revision adds Cntr_E_delta_minus / Cntr_E_delta_plus, which this step does not
# use, to the same v004 file on dev; every column read below is identical in
# both. Take the newer one again if the columns are ever recalibrated.
gf_file = './config_files/imap_lo_hydrogen-geometric-factor_v004.csv'

# ESA mode 0 is HiRes, 1 is HiThr. The maps this step consumes are HiRes.
esa_mode = 0

# Center energies and geometric factors per ESA step, from the shared hydrogen
# geometric factor ancillary file. Only rows where the incident and observed
# ESA step agree are used. The unc_minus / unc_plus columns bound the geometric
# factor and become the systematic error on the corrected flux.
def load_geometric_factors(filename, esa_mode):

    df = pd.read_csv(filename, comment='#', encoding='utf-8-sig')

    df = df[
        (df['esa_mode'] == esa_mode)
        & (df['incident_E-Step'] == df['Observed_E-Step'])
    ]

    return {
        column: {
            int(step): float(value)
            for step, value in zip(df['Observed_E-Step'], df[column])
        }
        for column in (
            'Cntr_E', 'GF_Trpl_H', 'GF_Trpl_H_unc_minus', 'GF_Trpl_H_unc_plus'
        )
    }

gf_data = load_geometric_factors(gf_file, esa_mode)

hy_esa_energy = gf_data['Cntr_E']

hy_gf = gf_data['GF_Trpl_H']

# NOTE: the columns are crossed with respect to their names on purpose. The
# ancillary names them for the direction the intensity moves, which is the
# opposite of the direction the geometric factor moves, since intensity goes as
# 1/G. So unc_plus is the downward excursion of the factor (hy_dgl, which
# raises the flux) and unc_minus the upward one (hy_dgu). This reproduces the
# values v4 derived by hand to ~0.1% at every ESA step, and matches
# imap_processing's _esa_calibration.
hy_dgl = gf_data['GF_Trpl_H_unc_plus']

hy_dgu = gf_data['GF_Trpl_H_unc_minus']

# ESA-8 is a virtual channel used only for the flux extrapolation below, so it
# has no row in the geometric factor file. Its center energy is E7 * 2.1.
hy_esa_energy[8] = hy_esa_energy[7] * 2.1

sputter_file = './config_files/sputter_factors.csv'

# Oxygen channels that sputter into each hydrogen channel, as
# {target_esa: {source_esa: sputter_factor}}. A hydrogen channel may be fed by
# more than one oxygen channel, so the inner dict can hold several entries.
def load_sputter_factors(filename):

    df = pd.read_csv(filename)

    factors = {}

    for target_esa, source_esa, factor in zip(
        df['target_esa'], df['source_esa'], df['sputter_factor']
    ):
        factors.setdefault(int(target_esa), {})[int(source_esa)] = float(factor)

    return factors

sput_cor = load_sputter_factors(sputter_file)

bootstrap_file = './config_files/bootstrap_factors.csv'

# Nominal bootstrap coefficients h_(i,k), keyed by (esa_step_i, esa_step_k).
def load_bootstrap_factors(filename):

    df = pd.read_csv(filename)

    return {
        (int(esa_i), int(esa_k)): float(factor)
        for esa_i, esa_k, factor in zip(
            df['esa_step_i'], df['esa_step_k'], df['bootstrap_factor']
        )
    }

bootstrap_factors = load_bootstrap_factors(bootstrap_file)

# modified scale on 6/4/26
# this is because the amount of sputtering went down by 0.25
# a is the correction actually applied; a_up / a_lo bound it to build the
# systematic error on the bootstrapped flux.
scale = 0.5
scale_up = 0.25
scale_lo = 1.0

a = {k: v * scale for k, v in bootstrap_factors.items()}

a_up = {k: v * scale_up for k, v in bootstrap_factors.items()}

a_lo = {k: v * scale_lo for k, v in bootstrap_factors.items()}





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
    hy_sput_flux_unc_list=[]
    hy_sput_flux_unl_list=[]
    hy_sput_flux_unu_list=[]

    for tar_esa in range(1,8):
        cor_cnts = hy_cnts[tar_esa-1]
        cor_cnts_var = hy_cnts_var[tar_esa-1]

        for src_esa, coeff in sput_cor.get(tar_esa, {}).items():

            cor_cnts = cor_cnts - ox_cnts[src_esa-1]*coeff

            cor_cnts_var = cor_cnts_var + (coeff**2)*ox_cnts_var[src_esa-1]


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
