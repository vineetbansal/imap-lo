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

TOF3_L = [ 11.0, 7.0, 3.5, 0.0 ]
TOF3_H = [15.0, 11.0, 7.0, 3.5 ]
# TOF_0, TOF_1, TOF_2
E_PEAK_H = [ 20.0, 10.0, 10.0 ]
H_PEAK_L = [ 20.0, 10.0, 12.0 ]
H_PEAK_H = [ 70.0, 50.0, 33.7 ] # new flight values
#CO_PEAK_L = [ 100.0, 60.0, 60.0   ] OLD values
#CO_PEAK_H = [ 270.0, 150.0, 150.0 ]
CO_PEAK_L = [ 100.0, 60.0, 61.9   ] # new flight values
CO_PEAK_H = [ 270.0, 150.0, 170.1 ]
#  for GOLD, TOF2 < 15, TOF2 < 35 and > 35

# EU = C0 + C1 * ADC
# ADC_TOF = [C0, C1]
ADC_TOF0 = [5.5252E-01 ,   1.6837E-01]
ADC_TOF1 = [-7.2018E-01,  1.6512E-01]
ADC_TOF2 = [3.7442E-01,    1.6641E-01]
ADC_TOF3 = [4.6726E-01,    1.7144E-01]

#CHKSM_LB = -21
LEFT_SCI_BOUNDARY = 20
# 
#CHKSM_RB = -6
# not really used
CHKSM_RB = LEFT_SCI_BOUNDARY - 15

PI = np.pi

TICK_TO_SEC = 4.096e-3

cols = ['shcoarse', 'absent', 'timestamp', 'egy', 'mode', 'TOF0', 'TOF1', 'TOF2', 'TOF3', 'checksum', 'position']

def argParsing():

    parser = argparse.ArgumentParser(description='This tool accepts a GSEOS filename and makes cool plots for IMAP-Lo.')
    
    parser.add_argument('-f', '--file',
                            help='the l1b file',
                           dest='file',
                           required=True)
    
    parser.add_argument('-k', '--hkfile',
                            help='the hk file',
                           dest='file_hk',
                           required=True)

    parser.add_argument('-o', '--outputFile',
                        help='the plot output file',
                        dest='outFile',
                        required=True)
    
    parser.add_argument('-s', '--species',
                        help='species 0 = H, 1 = O',
                        dest='species',
                        required=True, 
                        type=int) 

    return parser.parse_args()

def doy_fraction(t):
    start = datetime(t.year, 1, 1)
    return 1.0 + (t - start).total_seconds() / 86400.0 

def filter_and_write_cdf(args):
    """
    Filters a CDF dataset based on goodtime intervals, spin bins, ESA steps, and badtime,
    and writes the filtered results to a CSV file.
    
    Parameters
    ----------
    cdf_file : str
        Path to the input CDF file.
    goodtime_file : str
        CSV file containing goodtime intervals and ESA flags.
    out_file : str
        Output CSV file path.
    """
    # -------------------------------
    # Load CDF variables
    # -------------------------------

    out_file=args.outFile

    cdf = pycdf.CDF(args.file)

    ct       = cdf['coincidence_type'][:]
    mode     = cdf['mode'][:]
    de_time  = cdf['de_time'][:]
    esa_step = cdf['esa_step'][:]
    tof0     = cdf['tof0'][:]
    tof1     = cdf['tof1'][:]
    tof2     = cdf['tof2'][:]
    tof3     = cdf['tof3'][:]
    cksm     = cdf['cksm'][:]
    shcoarse = cdf['shcoarse'][:]
    de_count = cdf['de_count'][:]

    shcoarse = np.asarray(shcoarse)
    de_count = np.asarray(de_count)

    if shcoarse.ndim != 1 or de_count.ndim != 1:
        raise ValueError(f"Expected 1D arrays, got shcoarse {shcoarse.shape}, de_count {de_count.shape}")

    if len(shcoarse) != len(de_count):
        print(f"WARNING: length mismatch in {args.file}: shcoarse={len(shcoarse)}, de_count={len(de_count)}")
        n = min(len(shcoarse), len(de_count))
        print(f"Truncating both arrays to {n}")
        shcoarse = shcoarse[:n]
        de_count = de_count[:n]

    if np.any(de_count < 0):
        raise ValueError("de_count contains negative values")

    shcoarse_expanded = np.repeat(shcoarse, de_count)

    print("1S17 l1a sanity check for alignmen: ", len(shcoarse_expanded), len(tof0), len(tof1), len(de_time))

#    shcoarse_expanded = [shcoarse[j] for j in range(len(de_count)) for i in range(de_count[j]) ]
#    direct_events = cdf['direct_events'][:]

    cdf.close()

    df = pd.DataFrame({
        'coincidence_type': ct,
        'mode': mode,
        'esa_step': esa_step,
        'tof0': tof0,
        'tof1': tof1,
        'tof2': tof2,
        'tof3': tof3,
        'cksm': cksm,
        'de_time': de_time,
        'shcoarse': shcoarse_expanded
    })

    # only golden triples
    df = df[(df['coincidence_type'] == 0) & (df['mode'] == 1)].copy()

    df['tof1d'] = df['tof0'] + df['tof3'] - df['tof2'] - df['cksm'] + ( 2 * LEFT_SCI_BOUNDARY  )
    df['tof0'] = df['tof0'] *  ADC_TOF0[1] + ADC_TOF0[0]
    df['tof2'] = df['tof2'] *  ADC_TOF2[1] + ADC_TOF2[0]
    df['tof3'] = df['tof3'] *  ADC_TOF3[1] + ADC_TOF3[0]

    # since mode==1 after filtering, no need for np.where
    df['tof1'] = df['tof1d'] *  ADC_TOF1[1] + ADC_TOF1[0]
#    df['tof1'] = np.where(df['mode']==1, (df['tof1d']*ADC_TOF1[1]+ADC_TOF1[0]),(df['tof1']*ADC_TOF1[1]+ADC_TOF1[0]))

    df['tof0'] = df['tof0'] + 0.5 * df['tof3']
    df['tof1'] = df['tof1'] - 0.5 * df['tof3']

    df['quadrant'] = 1.0 * df['tof3']

    ct      = df['coincidence_type'][:]
    mode    = df['mode'][:]
    esa_step = df['esa_step'][:]
    tof0     = df['tof0'][:] # now tof0s
    tof1      = df['tof1'][:] # now tof1s
    tof2      = df['tof2'][:]
    tof3      = df['tof3'][:]
    de_time   = df['de_time'][:]
    shcoarse =  df['shcoarse'][:] # this is no longer a CDF variable 
    cksum     =  df['cksm'][:]
    
    # -------------------------------
    # Load housekeeping CSV
    # -------------------------------

    cdf_hk = pycdf.CDF(args.file_hk)
    spin_period = cdf_hk['spin_period'][:]
    cdf_hk.close()

    spin_period_ave = np.nanmean(spin_period)
    print("1S17 spin period ave  = ", spin_period_ave)

    deg_per_sec = 360.0 / spin_period_ave

    # -------------------------------
    # Get the spin phase
    # -------------------------------

    nep_spinphase = de_time * TICK_TO_SEC * deg_per_sec + 60.0
    nep_spinphase %= 360.0
    spinbin = np.round(10 * nep_spinphase).astype(int) % 3600

    # -------------------------------
    # Load goodtime CSV
    # -------------------------------
#    date, time_start, time_end, bin_start, bin_end, inst, \
#    esa1, esa2, esa3, esa4, esa5, esa6, esa7, comment = np.loadtxt(
#        goodtime_file, delimiter=',', unpack=True, comments='#'
#    )

    # -------------------------------
    # Write to CSV
    # -------------------------------


    for esa in range (1,8):
        with open(out_file+'_ESA'+str(esa)+'.csv', 'w') as fle:
            print("shcoarse,tof3,tof2,tof1s,tof0s,absent,mode,nep_spinbin,esa_step", file=fle)


            # m = len(time_start)
            # for esa_index in range (0,7):
            # # pull out any intervals not good for esa 
            #     for itime in range(0,m):
            #         if esa_flags[itime,esa_index] == 0:
            #             time_end[itime] = time_start[itime]
    
    # -------------------------------
    # Vectorized mask calculations
    # -------------------------------
            N = len(shcoarse)
#            M = len(time_start)
 # N = len(met) (number of events)
# M = len(time_start) (number of goodtime intervals)

# shape (N_events, N_goodtimes)
 #  print("met:", met.shape)
            
            esa_check = (esa_step == esa)
            
            tof3_check = (tof3 >= 0.0) & (tof3 <= 20.0) # kept handy but filter not used 

            if args.species == 1:  # O
                tof0_check = (tof0 >= CO_PEAK_L[0]) & (tof0 <= CO_PEAK_H[0])
                tof1_check = (tof1 >= CO_PEAK_L[1]) & (tof1 <= CO_PEAK_H[1])
                tof2_check = (tof2 >= CO_PEAK_L[2]) & (tof2 <= CO_PEAK_H[2])
            elif args.species == 0:  # H
                tof0_check = (tof0 >= H_PEAK_L[0]) & (tof0 <= H_PEAK_H[0])
                tof1_check = (tof1 >= H_PEAK_L[1]) & (tof1 <= H_PEAK_H[1])
                tof2_check = (tof2 >= H_PEAK_L[2]) & (tof2 <= H_PEAK_H[2])
            else:
                raise ValueError("species must be 0 (H) or 1 (O)")
            
            mask = esa_check & tof2_check & tof1_check & tof0_check 
#            mask = esa_check & tof2_check 

    #    esa_check = np.linspace(0,0,N)
    #    for i in range(0,N)
    #        esa_check = esa_flags[]

    #  print("met.shape:", met.shape)
    #  print("time_start.shape:", time_start.shape)
    #  print("spinbin2.shape:", spinbin2.shape)
    #   print("esa_step.shape:", esa_step.shape)
    #   print("esa_flags.shape:", esa_flags.shape)

    #  print("met_check.shape:", met_check.shape)
    #  print("spin_check.shape:", spin_check.shape)
    # print("esa_check.shape:", esa_check.shape)

    ## Event passes ANY goodtime interval
    #   mask = np.any(met_check & spin_check & esa_check, axis=0)  # shape (N_events,)
    #    mask &= (badtime == 0)              # only keep events not in badtime
    # Debug

    #    print(mask[0:20])


        # & (badtime == 0)
        
        # -------------------------------
        # Filter arrays
        # -------------------------------
            filtered = {
                'shcoarse': shcoarse[mask],
                'tof3': tof3[mask],
                'tof2': tof2[mask],
                'tof1': tof1[mask],
                'tof0': tof0[mask],
#                'de_time': de_time[mask],
                'spinbin': spinbin[mask],
                'esa_step': esa_step[mask]
            }
        
            n = len(filtered['shcoarse'])
            if (n > 0):
                for row in zip(
                        filtered['shcoarse'],
                        filtered['tof3'],
                        filtered['tof2'],
                        filtered['tof1'],
                        filtered['tof0'],
                        [0] * n,
                        [1] * n,
#                        filtered['de_time'],
                        filtered['spinbin'],
                        filtered['esa_step']
                    ):
                        print(','.join(map(str, row)), file=fle)
    
            print(f"1S17 CO: ESA = {esa}, Filtered {mask.sum()} / {N} rows written to {out_file}_ESA{esa}.csv")

# main

args = argParsing()

filter_and_write_cdf( args )