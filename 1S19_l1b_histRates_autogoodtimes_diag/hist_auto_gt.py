#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov  2 17:10:13 2025

@author: hafijulislam
"""

# >>> import cdflib
# >>> cdf = cdflib.CDF("./input/imap_lo_l1a_de_20260120-repoint00132_v001.cdf")
# >>> cdf.cdf_info()
# CDFInfo(CDF=PosixPath('/Users/nschwadron/data/imap_pipeline2/1R3-CDF-spinphaseDEWTime/input/imap_lo_l1a_de_20260120-repoint00132_v001.cdf'), Version='3.9.0', Encoding=6, Majority='Row_major', rVariables=[], zVariables=['met', 'de_count', 'passes', 'coincidence_type', 'de_time', 'esa_step', 'mode', 'tof0', 'tof1', 'tof2', 'tof3', 'cksm', 'pos', 'shcoarse', 'epoch', 'direct_events', 'direct_events_label'], Attributes=[{'Acknowledgement': 'Global'}, {'Data_type': 'Global'}, {'Data_version': 'Global'}, {'Descriptor': 'Global'}, {'Discipline': 'Global'}, {'File_naming_convention': 'Global'}, {'HTTP_LINK': 'Global'}, {'Instrument_type': 'Global'}, {'LINK_TITLE': 'Global'}, {'Logical_file_id': 'Global'}, {'Logical_source': 'Global'}, {'Logical_source_description': 'Global'}, {'Mission_group': 'Global'}, {'PI_affiliation': 'Global'}, {'PI_name': 'Global'}, {'Project': 'Global'}, {'Rules_of_use': 'Global'}, {'Source_name': 'Global'}, {'TEXT': 'Global'}, {'Repointing': 'Global'}, {'Start_date': 'Global'}, {'Parents': 'Global'}, {'ground_software_version': 'Global'}, {'Generation_date': 'Global'}, {'Generated_by': 'Global'}, {'DEPEND_0': 'Variable'}, {'CATDESC': 'Variable'}, {'DISPLAY_TYPE': 'Variable'}, {'FIELDNAM': 'Variable'}, {'FILLVAL': 'Variable'}, {'FORMAT': 'Variable'}, {'LABLAXIS': 'Variable'}, {'UNITS': 'Variable'}, {'VALIDMIN': 'Variable'}, {'VALIDMAX': 'Variable'}, {'VAR_TYPE': 'Variable'}, {'DEPEND_1': 'Variable'}, {'LABL_PTR_1': 'Variable'}, {'TIME_BASE': 'Variable'}, {'RESOLUTION': 'Variable'}, {'TIME_SCALE': 'Variable'}, {'REFERENCE_POSITION': 'Variable'}, {'DICT_KEY': 'Variable'}, {'MONOTON': 'Variable'}, {'SCALETYP': 'Variable'}], Copyright='\nCommon Data Format (CDF)\nhttps://cdf.gsfc.nasa.gov\nSpace Physics Data Facility\nNASA/Goddard Space Flight Center\nGreenbelt, Maryland 20771 USA\n(User support: gsfc-cdf-support@lists.nasa.gov)\n', Checksum=False, Num_rdim=0, rDim_sizes=[], Compressed=False, LeapSecondUpdate=None)
# 'met', 'de_count', 'passes', 'coincidence_type', 'de_time', 'esa_step', 'mode', 'tof0', 'tof1', 'tof2', 'tof3', 'cksm', 'pos', 'shcoarse', 'epoch', 'direct_events', 'direct_events_label'

import pandas as pd
import numpy as np
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from spacepy import pycdf
from spacepy.time import Ticktock
import re

TOF3_L = [ 11.0, 7.0, 3.5, 0.0 ]
TOF3_H = [15.0, 11.0, 7.0, 3.5 ]
# TOF_0, TOF_1, TOF_2
E_PEAK_H = [ 20.0, 10.0, 10.0 ]
H_PEAK_L = [ 20.0, 10.0, 10.0 ]
H_PEAK_H = [ 70.0, 50.0, 40.0 ]
CO_PEAK_L = [ 100.0, 60.0, 60.0   ]
CO_PEAK_H = [ 270.0, 150.0, 150.0 ]
#  for GOLD, TOF2 < 15, TOF2 < 35 and > 35

# EU = C0 + C1 * ADC
# ADC_TOF = [C0, C1]
ADC_TOF0 = [5.5252E-01 ,   1.6837E-01]
ADC_TOF1 = [-7.2018E-01,  1.6512E-01]
ADC_TOF2 = [3.7442E-01,    1.6641E-01]
ADC_TOF3 = [4.6726E-01,    1.7144E-01]

CHKSM_LB = -21
CHKSM_RB = -6

PI = np.pi

VERY_SMALL = 1.0e-10

epoch0 = datetime(2010, 1, 1, 0, 0, 0)

cols = ['shcoarse', 'absent', 'timestamp', 'egy', 'mode', 'TOF0', 'TOF1', 'TOF2', 'TOF3', 'checksum', 'position']



def print_lines_selector(args, fcut, header, date, file_date, repoint_int, ngood, ntotal, counts_array, exposure18, pivot):
    # 0,1,2     N ram 5,6,7 ESA
    # 3,4,5     N arm 5,6,7 ESA
    # 6,7,8     S ram 5,6,7 ESA
    # 9,10,11   S arm 5,6,7 ESA

    # --- Fix initializations ---
    rates = np.zeros(12)
    runc  = np.zeros(12)

    rates[:] = counts_array[:] / (exposure18 + VERY_SMALL)
    runc[:]  = rates[:] / np.sqrt(counts_array[:] + VERY_SMALL)

    accum = np.zeros(4)
    aunc  = np.zeros(4)

    accum[0] = np.sum(counts_array[0:3]) / (3 * exposure18 + VERY_SMALL)
    aunc[0]  = accum[0] / np.sqrt(np.sum(counts_array[0:3]) + VERY_SMALL)

    accum[1] = np.sum(counts_array[3:6]) / (3 * exposure18 + VERY_SMALL)
    aunc[1]  = accum[1] / np.sqrt(np.sum(counts_array[3:6]) + VERY_SMALL)

    accum[2] = np.sum(counts_array[6:9]) / (3 * exposure18 + VERY_SMALL)
    aunc[2]  = accum[2] / np.sqrt(np.sum(counts_array[6:9]) + VERY_SMALL)

    accum[3] = np.sum(counts_array[9:12]) / (3 * exposure18 + VERY_SMALL)
    aunc[3]  = accum[3] / np.sqrt(np.sum(counts_array[9:12]) + VERY_SMALL)

    if header == 1:
        print(
            "date,yyyymmdd,repoint,ngood,ntotal,expo_1stp,expo_3stp,pivot,"
            "Nram,Unc,Narm,Unc,Sram,Unc,Sarm,Unc,"
            "Nram5,Unc,Nram6,Unc,Nram7,Unc,"
            "Narm5,Unc,Narm6,Unc,Narm7,Unc,"
            "Sram5,Unc,Sram6,Unc,Sram7,Unc,"
            f"Sarm5,Unc,Sarm6,Unc,Sarm7,Unc,cut90,{args.tcut90:.6e},cutoff,{args.tcutOff:.6e}",
            file=fcut
        )
    else:
        print(
                f"{date},{file_date},{repoint_int},{ngood},{ntotal},{exposure18},{3*exposure18},{pivot},"
                f"{accum[0]:.6e},{aunc[0]:.6e},"
                f"{accum[1]:.6e},{aunc[1]:.6e},"
                f"{accum[2]:.6e},{aunc[2]:.6e},"
                f"{accum[3]:.6e},{aunc[3]:.6e},"
                f"{rates[0]:.6e},{runc[0]:.6e},{rates[1]:.6e},{runc[1]:.6e},{rates[2]:.6e},{runc[2]:.6e},"
                f"{rates[3]:.6e},{runc[3]:.6e},{rates[4]:.6e},{runc[4]:.6e},{rates[5]:.6e},{runc[5]:.6e},"
                f"{rates[6]:.6e},{runc[6]:.6e},{rates[7]:.6e},{runc[7]:.6e},{rates[8]:.6e},{runc[8]:.6e},"
                f"{rates[9]:.6e},{runc[9]:.6e},{rates[10]:.6e},{runc[10]:.6e},{rates[11]:.6e},{runc[11]:.6e}",
                file=fcut
            )

def get_repoint(fname):
    m = re.search(r"repoint(\d+)", fname)
    if not m:
        raise ValueError(f"No repoint found in {fname}")
    return int(m.group(1))

def doy_fraction(t):
    start = datetime(t.year, 1, 1)
    return 1.0 + (t - start).total_seconds() / 86400.0 

def met_from_epoch(t):

#    met = (t - epoch0) / 1000.0  # seconds

    e0 = epoch0
    e1 =  t
    dt = e1 - e0
    met =  dt.total_seconds() + 9
    # this is because we are using an older time kernel (pre 2012)
#    print("met = ",met)
    return met

def argParsing():

    parser = argparse.ArgumentParser(description='This tool accepts a GSEOS filename and makes cool plots for IMAP-Lo.')
    
    parser.add_argument('-f', '--file',
                            help='the hist file (l1b)',
                           dest='file',
                           required=True)
    
    parser.add_argument('-e', '--de_file',
                            help='the level 1b de file',
                           dest='dfle',
                           required=True)
    
    parser.add_argument('-k', '--hk_file',
                            help='the level 1b NHK file',
                           dest='kfle',
                           required=True)

    parser.add_argument('-o', '--outputRoot',
                        help='the output root for autogt file',
                        dest='outRoot',
                        required=True)
    
    parser.add_argument('-n', '--ncycle_sum',
                        help='the number of hist to sum',
                        dest='ncycle_sum',
                        type=int,
                        required=True)
        
    parser.add_argument('-t90', '--tcut90',
                        help='the cut rate in s-1 (e.g., 0.0028) for 90 deg PPM',
                        dest='tcut90',
                        type=float,
                        required=True)

    parser.add_argument('-toff', '--tcutOff',
                        help='the cut rate in s-1 (e.g., 0.0028) for PPM angles other than 90 deg',
                        dest='tcutOff',
                        type=float,
                        required=True)

    return parser.parse_args()

# main

args = argParsing()

#file = "/Users/hafijulislam/Library/CloudStorage/Box-Box/First_light_maps/DN/Instrument_FM1_playback_301_ILO_SCI_DE_dec_20251102T170018_DN.csv"

epoch = datetime(2010, 1, 1, 0, 0, 0)

cdf = pycdf.CDF(args.file)
cdf_de = pycdf.CDF(args.dfle)
cdf_hk = pycdf.CDF(args.kfle)

repoint_int = get_repoint(args.file)

data = {}

#azimuth_6: CDF_UINT1 [60] NRV
#azimuth_60: CDF_UINT1 [6] NRV
#azimuth_60_label: CDF_CHAR*3 [6] NRV
#azimuth_6_label: CDF_CHAR*3 [60] NRV
#disc_tof0: CDF_UINT4 [181, 7, 6]
#disc_tof1: CDF_UINT4 [181, 7, 6]
#disc_tof2: CDF_UINT4 [181, 7, 6]
#disc_tof3: CDF_UINT4 [181, 7, 6]
#epoch: CDF_TIME_TT2000 [181]
#esa_step: CDF_UINT1 [7] NRV
#esa_step_label: CDF_CHAR*3 [7] NRV
#hydrogen: CDF_UINT4 [181, 7, 60]
#oxygen: CDF_UINT4 [181, 7, 60]
#pos0: CDF_UINT4 [181, 7, 6]
#pos1: CDF_UINT4 [181, 7, 6]
#pos2: CDF_UINT4 [181, 7, 6]
#pos3: CDF_UINT4 [181, 7, 6]
#shcoarse: CDF_UINT4 [181]
#silver: CDF_UINT4 [181, 7, 60]
#start_a: CDF_UINT4 [181, 7, 6]
#start_c: CDF_UINT4 [181, 7, 6]
#stop_b0: CDF_UINT4 [181, 7, 6]
#stop_b3: CDF_UINT4 [181, 7, 6]
#tof0_count: CDF_UINT4 [181, 7, 6]
#tof0_tof1: CDF_UINT4 [181, 7, 60]
#tof0_tof2: CDF_UINT4 [181, 7, 60]
#tof1_count: CDF_UINT4 [181, 7, 6]
#tof1_tof2: CDF_UINT4 [181, 7, 60]
#tof2_count: CDF_UINT4 [181, 7, 6]
#tof3_count: CDF_UINT4 [181, 7, 6]

# 'azimuth_6','azimuth_60','azimuth_60_label','azimuth_6_label','disc_tof0','disc_tof1','disc_tof2','disc_tof3','epoch','esa_step','esa_step_label','hydrogen','oxygen','pos0','pos1','pos2','pos3','shcoarse','silver','start_a','start_c','stop_b0','stop_b3','tof0_count','tof0_tof1','tof0_tof2','tof1_count','tof1_tof2','tof2_count','tof3_count'

try:
    pivotp = cdf_de['pivot_angle'][0]
except:
    pivotp = 0.0

try:

    epoch_hk=cdf_hk['epoch']
    tt = Ticktock(epoch_hk, 'CDF')
    times = np.array(tt.UTC)
    t0_hk = times[0]
#    print(t0_hk)
# print(times[-1])
    start_time_hk = t0_hk + timedelta(hours=3)
    end_time_hk = t0_hk + timedelta(hours=15)
# print(start_time_hk)
# print(end_time_hk)
    mask_hk = (times >= start_time_hk) & (times <= end_time_hk)
    pri = cdf_hk['pcc_coarse_pot_pri'][...]
    sec = cdf_hk['pcc_coarse_pot_sec'][...]

    pivot1 = np.nanmedian(pri[mask_hk])
#    pivot2 = np.nanmedian(sec[mask_hk])
#pivot1 = np.nanmedian(cdf_hk['pcc_coarse_pot_pri'][mask_hk])
#pivot2 = np.nanmedian(cdf_hk['pcc_coarse_pot_sec'][mask_hk])
    pivot = pivot1 
#    print(pivotp)
#    pivot = pivot1
    if np.isnan(pivot):
        pivot = 90.0
except:
    pivot = 90.0

# print("pivot = ",pivot, "pivottp = ",pivotp)

#    pcc_coarse_pot_pri: CDF_DOUBLE [86443]
#.   pcc_coarse_pot_sec: CDF_DOUBLE [86443]

try:
    first_begin = met_from_epoch(cdf_hk['epoch'][0])
    last_end = met_from_epoch(cdf_hk['epoch'][-1])
except:
    first_begin = met_from_epoch(cdf['epoch'][0])
    last_end = met_from_epoch(cdf['epoch'][-1])

if (pivot < 92.0 ) & (pivot > 88.0):
    bg_rate_nom = args.tcut90
else:
    bg_rate_nom = args.tcutOff

ncycle_sum = args.ncycle_sum
interval_nom = 420 * ncycle_sum

exposure = 420 * ncycle_sum * 0.5
exposure_hist = 420 

#print('expo =', exposure)

d = np.sum(cdf['h_counts'][:, 0:7, 20:50], axis=(1,2))
o = np.sum(cdf['o_counts'][:, 0:7, 20:50], axis=(1,2))

darm_S = np.sum(cdf['h_counts'][:,:, 20:23], axis=(2))
dram_S = np.sum(cdf['h_counts'][:,:, 17:20], axis=(2))
darm_N = np.sum(cdf['h_counts'][:,:, 47:50], axis=(2))
dram_N = np.sum(cdf['h_counts'][:,:, 50:53], axis=(2))

epoch = cdf['epoch'][:]
m0 = met_from_epoch(epoch[0])
# print("m0 = ", m0)

ncycle = np.shape(d)[0]

begin = 0.0
end = 0.0

#first_begin = 0.0
#last_end = 0.0

# 0,1,2     N ram 5,6,7 ESA
# 3,4,5     N arm 5,6,7 ESA
# 6,7,8     S ram 5,6,7 ESA
# 9,10,11   S arm 5,6,7 ESA
sum_cnts_poles = np.zeros(12)
# per 18 deg bin exposure
sum_exposure_18 = 0.0

sum_bg_cnts = 0.0
sum_og_cnts = 0.0
sum_bg_expo = 0.0

# date = re.search(r"\d{8}", args.outFile).group()
yr1  = epoch[0].year
doy1 = int(doy_fraction(epoch[0]) )
sdoy1 = f"{doy1:03d}"
date1 = f"{yr1}{sdoy1}"
# print(date1)
mon1  = epoch[0].month
day1  = epoch[0].day

date_yyyymmdd = f"{yr1}{mon1:02d}{day1:02d}"

ngood = 0
ntotal = ncycle
# number of good histograms
output_file = args.outRoot+date1+'.csv'

with open(output_file, 'w') as fcut :

    cut_header = 1

    print_lines_selector(args,fcut, cut_header, date1, date_yyyymmdd, repoint_int, ngood, ntotal, sum_cnts_poles, sum_exposure_18, pivot)

    cut_header = 0

    for i in range(0, ncycle):

        i0 = max(int(i - ncycle_sum//2), 0)
        i1 = min(ncycle, i0 + ncycle_sum)
        if (i1 - i0) < ncycle_sum: 
            i0 = max(i1 - ncycle_sum, 0)

        antiram_cnts = np.sum(d[i0:i1])
        antiram_cnts_o = np.sum(o[i0:i1])
        antiram_rate = antiram_cnts / exposure
        antiram_rate_o = antiram_cnts_o / exposure  
        
        if (antiram_rate < bg_rate_nom):
            sum_exposure_18 += ((exposure_hist/7.0) * (18.0/360.0))
            # 0,1,2     N ram 5,6,7 ESA
            # 3,4,5     N arm 5,6,7 ESA
            # 6,7,8     S ram 5,6,7 ESA
            # 9,10,11   S arm 5,6,7 ESA
            sum_cnts_poles[0:3] += dram_N[i,4:7] 
            sum_cnts_poles[3:6] += darm_N[i,4:7] 
            sum_cnts_poles[6:9] += dram_S[i,4:7] 
            sum_cnts_poles[9:12] += darm_S[i,4:7] 
            ngood += 1

    print_lines_selector(args,fcut, cut_header, date1, date_yyyymmdd, repoint_int, ngood, ntotal, sum_cnts_poles, sum_exposure_18, pivot)
