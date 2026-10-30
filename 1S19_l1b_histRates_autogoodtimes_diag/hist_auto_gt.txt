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

epoch0 = datetime(2010, 1, 1, 0, 0, 0)

cols = ['shcoarse', 'absent', 'timestamp', 'egy', 'mode', 'TOF0', 'TOF1', 'TOF2', 'TOF3', 'checksum', 'position']

def print_lines(fgt, fcn, date, begin1, end1, sum_bg_cnts, sum_og_cnts, sum_bg_expo,  bg_rate_nom, pivot,pivotp):

    begin2 = begin1 - 20
    end2 = end1 + 20

    print( 
        f"{date},{int(begin2)},{int(end2)},0,59,Lo,1,1,1,1,1,1,1,# auto goodtimes bg_rate_nom = {bg_rate_nom:.6f}", file=fgt
        )
    print (
        f"{date},{int(begin2)},{int(end2)},30,59,Lo,{sum_bg_cnts},{sum_og_cnts},{sum_bg_expo},{pivot},{pivotp}", file=fcn
        )

def print_lines_tof_ideas(fideas, date, begin1, end1, header):

    begin2 = begin1 - 20
    end2 = end1 + 20

    if (header == 1):
        print( 
            f"date,begin,end,bin0,bin1,nbins,Lo,ESA1,ESA2,ESA3,ESA4,ESA5,ESA6,ESA7,Absent, Mode,TOF0lo,TOF0hi,nbins,TOF1lo,TOF1hi,nbins,TOF2lo,TOF2hi,nbins,TOF3lo,TOF3hi,nbins", file=fideas
        )   
    else:
        print( 
            f"{date},{int(begin2)},{int(end2)},0,59,60,Lo,1,1,1,1,1,1,1,0,1, {H_PEAK_L[0]},{CO_PEAK_H[0]},100,{H_PEAK_L[1]},{CO_PEAK_H[1]},100,{H_PEAK_L[2]},{CO_PEAK_H[2]},100,{TOF3_L[3]},{TOF3_H[0]},20", file=fideas
        )

def print_lines_background(fbg, fbo, date, begin1, end1, sum_bg_cnts, sum_og_cnts, sum_bg_expo,  bg_rate_nom):
    try:
        bg_rate = sum_bg_cnts / sum_bg_expo
        bg_rate_o = sum_og_cnts / sum_bg_expo
        sigma_bg_rate = np.sqrt(sum_bg_cnts) / sum_bg_expo
        sigma_og_rate = np.sqrt(sum_og_cnts) / sum_bg_expo
    except:
        bg_rate = bg_rate_nom
        bg_rate_o =  bg_rate_nom * 0.3
        sigma_bg_rate = bg_rate
        sigma_og_rate = bg_rate_o

    if (bg_rate == 0.0):
        bg_rate = bg_rate_nom / 50.0
        sigma_bg_rate = bg_rate
    if (bg_rate_o == 0.0):
        bg_rate_o = bg_rate_nom / 150.0
        sigma_og_rate = bg_rate_o
    if (sigma_bg_rate == 0.0):
        sigma_bg_rate = bg_rate
    if (sigma_og_rate == 0.0):
        sigma_og_rate = bg_rate_o

    begin2 = begin1 - 60*2
    end2 = end1 - 60*4.5

    print (
        f"{date},{int(begin2)},{int(end2)},0,59,Lo,{bg_rate:.7f},{bg_rate:.7f},{bg_rate:.7f},{bg_rate:.7f},{bg_rate:.7f},{bg_rate:.7f},{bg_rate:.7f},rate", file=fbg
        )
    print (
        f"{date},{int(begin2)},{int(end2)},0,59,Lo,{sigma_bg_rate:.7f},{sigma_bg_rate:.7f},{sigma_bg_rate:.7f},{sigma_bg_rate:.7f},{sigma_bg_rate:.7f},{sigma_bg_rate:.7f},{sigma_bg_rate:.7f},sigma", file=fbg
        )
    print (
        f"{date},{int(begin2)},{int(end2)},0,59,Lo,{bg_rate_o:.7f},{bg_rate_o:.7f},{bg_rate_o:.7f},{bg_rate_o:.7f},{bg_rate_o:.7f},{bg_rate_o:.7f},{bg_rate_o:.7f},rate", file=fbo
        )
    print (
        f"{date},{int(begin2)},{int(end2)},0,59,Lo,{sigma_og_rate:.7f},{sigma_og_rate:.7f},{sigma_og_rate:.7f},{sigma_og_rate:.7f},{sigma_og_rate:.7f},{sigma_og_rate:.7f},{sigma_og_rate:.7f},sigma", file=fbo
        )

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

    parser.add_argument('-o', '--outputFile',
                        help='the output autogt file',
                        dest='outFile',
                        required=True)
    
    parser.add_argument('-n', '--ncycle_sum',
                        help='the number of cycles to sum',
                        dest='ncycle_sum',
                        type=int,
                        required=True)
    
    parser.add_argument('-d', '--delay_max',
                        help='the max delay in s',
                        dest='delay_max',
                        type=int,
                        required=True)
    
    return parser.parse_args()

# main

args = argParsing()

#file = "/Users/hafijulislam/Library/CloudStorage/Box-Box/First_light_maps/DN/Instrument_FM1_playback_301_ILO_SCI_DE_dec_20251102T170018_DN.csv"

epoch = datetime(2010, 1, 1, 0, 0, 0)

cdf = pycdf.CDF(args.file)
cdf_de = pycdf.CDF(args.dfle)
cdf_hk = pycdf.CDF(args.kfle)

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
    bg_rate_nom = 0.0028
else:
    bg_rate_nom = 0.0035

ncycle_sum = args.ncycle_sum
interval_nom = 420 * ncycle_sum

exposure = 420 * ncycle_sum * 0.5

#print('expo =', exposure)

d = np.sum(cdf['h_counts'][:, 0:7, 20:50], axis=(1,2))
o = np.sum(cdf['o_counts'][:, 0:7, 20:50], axis=(1,2))
epoch = cdf['epoch'][:]
m0 = met_from_epoch(epoch[0])
# print("m0 = ", m0)

ncycle = np.shape(d)[0]

begin = 0.0
end = 0.0

#first_begin = 0.0
#last_end = 0.0

sum_bg_cnts = 0.0
sum_og_cnts = 0.0
sum_bg_expo = 0.0

# date = re.search(r"\d{8}", args.outFile).group()
yr1  = epoch[0].year
doy1 = int(doy_fraction(epoch[0]) )
sdoy1 = f"{doy1:03d}"
date1 = f"{yr1}{sdoy1}"
# print(date1)

with open(f'output/imap_lo_goodtimes_{date1}.csv', 'w') as fgt, \
     open(f'output/imap_lo_HO_cnts_expo_{date1}.csv', 'w') as fcn, \
     open(f'output/imap_lo_goodtimes_ideas_{date1}.csv', 'w') as fideas:

    ideas_header = 1
    print_lines_tof_ideas(fideas, date1, 0, 0, ideas_header)
    ideas_header = 0

    for i in range(0, ncycle, ncycle_sum):
        
        try:
            interval =  met_from_epoch(epoch[i+ncycle_sum-1]) - met_from_epoch(epoch[i])
          #  print("interval = ", interval)
        except:
            interval = interval_nom*ncycle_sum

        if (interval > (interval_nom + args.delay_max)):
             
            if (begin > 0.0):
                end = met_from_epoch(epoch[i-1])
#                last_end = end

                print_lines(fgt, fcn, date1, begin, end, sum_bg_cnts, sum_og_cnts, sum_bg_expo,  bg_rate_nom, pivot, pivotp)
                print_lines_tof_ideas(fideas, date1, begin, end, ideas_header)
                
                begin = 0.0
                end = 0.0

            continue
        
        delta_time = 0.0
        if (i > 0):
            delta_time =  met_from_epoch(epoch[i]) - (met_from_epoch(epoch[i-1])+420) 
            
        if (delta_time > args.delay_max) & (begin>0.0):
            end =   met_from_epoch(epoch[i-1]) 
            
            print_lines(fgt, fcn, date1, begin, end, sum_bg_cnts, sum_og_cnts, sum_bg_expo,  bg_rate_nom, pivot, pivotp)
            print_lines_tof_ideas(fideas, date1, begin, end, ideas_header)

            begin = 0.0
            end = 0.0

        antiram_cnts = np.sum(d[i:i+ncycle_sum])
        antiram_cnts_o = np.sum(o[i:i+ncycle_sum])
        antiram_rate = antiram_cnts / exposure
        antiram_rate_o = antiram_cnts_o / exposure  

#        print(antiram_rate, bg_rate)

        if (antiram_rate < bg_rate_nom):
            
            if (begin == 0.0):
                begin = met_from_epoch(epoch[i])
#                if (first_begin == 0.0):
#                    first_begin = begin
            sum_bg_cnts = sum_bg_cnts + antiram_cnts
            sum_og_cnts = sum_og_cnts + antiram_cnts_o
            sum_bg_expo = sum_bg_expo + exposure

        if (antiram_rate >= bg_rate_nom):
            if (begin > 0.0):
                end = met_from_epoch(epoch[i-1])
#                last_end = end

                print_lines(fgt, fcn, date1, begin, end, sum_bg_cnts, sum_og_cnts, sum_bg_expo,  bg_rate_nom, pivot, pivotp)
                print_lines_tof_ideas(fideas, date1, begin, end, ideas_header)
                
                begin = 0.0
                end = 0.0

    if (end == 0.) & (begin > 0.0 ):
        end = met_from_epoch(epoch[ncycle-1])
#        last_end = end
        if (end > begin):
             print_lines(fgt, fcn, date1, begin, end, sum_bg_cnts, sum_og_cnts, sum_bg_expo,  bg_rate_nom, pivot, pivotp)
             print_lines_tof_ideas(fideas, date1, begin, end, ideas_header)



with open(f'output/imap_lo_H_background_{date1}.csv', 'w') as fbg, \
     open(f'output/imap_lo_O_background_{date1}.csv', 'w') as fbo:
     if (last_end > first_begin):
         print_lines_background(fbg, fbo, date1, first_begin, last_end, sum_bg_cnts, sum_og_cnts, sum_bg_expo,  bg_rate_nom)
   
