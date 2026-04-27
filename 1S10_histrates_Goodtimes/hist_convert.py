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

def met_from_epoch(t):

#    met = (t - epoch0) / 1000.0  # seconds

    e0 = epoch0
    e1 =  t
    dt = e1 - e0
    # numpy / pandas vector case
  # Case 1 — numpy timedelta64
    if isinstance(dt, np.ndarray) and np.issubdtype(dt.dtype, np.timedelta64):
        met = dt / np.timedelta64(1, 's')

    # Case 2 — object array of datetime.timedelta
    elif isinstance(dt, np.ndarray):
        met = np.array([d.total_seconds() for d in dt])

    # Case 3 — pandas Series
    elif hasattr(dt, "dt"):
        met = dt.dt.total_seconds()

    # Case 4 — scalar
    else:
        met = dt.total_seconds()

    return met + 9


    if hasattr(dt, "dtype"):
        met = dt / np.timedelta64(1, 's') + 9
    else:  # scalar datetime.timedelta
        met = dt.total_seconds() + 9

    # this is because we are using an older time kernel (pre 2012)
#    print("met = ",met)
    return met


def filter_and_write_cdf(cdf_file, goodtime_file, out_file):
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
    cdf = pycdf.CDF(cdf_file)
    

    #epoch = cdf['epoch'][:]
#esa_mode = cdf['esa_mode'][:]
#exposure = cdf['exposure_time_6deg'][:,esa,:]
#h_counts = cdf['h_counts'][:,esa,:]
#h_rates = cdf['h_rates'][:,esa,:]
#o_counts = cdf['o_counts'][:,esa,:]
#o_rates = cdf['o_rates'][:,esa,:]
#spin_bin = cdf['spin_bin_6'][:]
#spin_cycle = cdf['spin_cycle'][:,esa]

    epoch       = cdf['epoch'][:]
    met = met_from_epoch(epoch)
    exposure  = cdf['exposure_time_6deg'][:,:,:]
    h_counts  = cdf['h_counts'][:,:,:]
    h_rates = cdf['h_rates'][:,:,:]
    o_counts  = cdf['o_counts'][:,:,:]
    o_rates = cdf['o_rates'][:,:,:]

    unfiltered = {
        'epoch': epoch,
        'met': met,
        'exposure': exposure,
        'h_counts': h_counts,
        'o_counts': o_counts,
        'h_rates': h_rates,
        'o_rates': o_rates
    }

    # -------------------------------
    # Load goodtime CSV
    # -------------------------------
#    date, time_start, time_end, bin_start, bin_end, inst, \
#    esa1, esa2, esa3, esa4, esa5, esa6, esa7, comment = np.loadtxt(
#        goodtime_file, delimiter=',', unpack=True, comments='#'
#    )

# Read CSV, everything after 13th column is ignored
    df = pd.read_csv(
        goodtime_file,
        header=None,      # no header row
        usecols=range(14),# read only first 14 columns (up to esa7)
        dtype=str         # read everything as string initially
    )

    # Assign column names
    df.columns = [
        "date","time_start","time_end","bin_start","bin_end",
        "inst","esa1","esa2","esa3","esa4","esa5","esa6","esa7","bla"
    ]

    # Convert numeric columns to int
    numeric_cols = ["date","time_start","time_end","bin_start","bin_end",
                    "esa1","esa2","esa3","esa4","esa5","esa6","esa7"]
    df[numeric_cols] = df[numeric_cols].astype(int)

    # 'inst' stays as string
    inst = df['inst'].to_numpy()
    time_start = df['time_start'].to_numpy()
    time_end   = df['time_end'].to_numpy()
    bin_start  = df['bin_start'].to_numpy()
    bin_end    = df['bin_end'].to_numpy()
    esa_flags  = df[['esa1','esa2','esa3','esa4','esa5','esa6','esa7']].to_numpy()

    # -------------------------------
    # Write to CSV
    # -------------------------------
   # with open(out_file, 'w') as fle:
   #     print("epoch,met,esa,exposure,h_counts,h_rates,o_counts,o_rates", file=fle)

    # -------------------------------
    # Vectorized mask calculations
    # -------------------------------
    N = len(met)
    M = len(time_start)
 # N = len(met) (number of events)
# M = len(time_start) (number of goodtime intervals)

    for iesa in range(0,7):

        for bin in range(0,60):

            # reset start time and stop time
            time_start = df['time_start'].to_numpy()
            time_end   = df['time_end'].to_numpy()

            # remove places not in the goodtime list
            for itime in range(0,M):
                if esa_flags[itime,iesa] == 0:
                    time_end[itime] = time_start[itime]

                if (bin > bin_end[itime]) or (bin < bin_start[itime] ):
                    time_end[itime] = time_start[itime]

            met_check  = (met[:, None] >= time_start) & (met[:, None] <= time_end)
            event_pass = met_check  
            mask = np.any(event_pass, axis=1) 

            for k in ('exposure','h_counts','o_counts','h_rates','o_rates'):
                unfiltered[k][~mask,iesa,bin] = 0

    # reset time_start and time_end again
    time_start = df['time_start'].to_numpy()
    time_end   = df['time_end'].to_numpy()
# shape (N_events, N_goodtimes)
 #  print("met:", met.shape)
    met_check  = (met[:, None] >= time_start) & (met[:, None] <= time_end)
    #   print("met_check:", met_check.shape)
    #   print("Number of mets passing filter:", np.sum(met_check))
    #   print("spinbin2 shape:", spinbin2.shape)
    #        spin_check = (spinbin2[:, None] >= bin_start) & (spinbin2[:, None] <= bin_end)
    #  print("spen check shape:", spin_check.shape)
    #  print("spin check passing:", np.sum(spin_check[:,0]))
    #  esa_idx    = esa_step - 1
    #  esa_check  = np.take(esa_flags, esa_idx[:, None], axis=1)  # shape (N_events, N_goodtimes)

    # NOT DOING ESA STEP FILTERING

    #    esa_check = np.linspace(0,0,N)
    #    for i in range(0,N)
    #        esa_check = esa_flags[]

        # Combine checks per event per interval
    event_pass = met_check    # shape (N_events, N_goodtimes)

    #  print("met.shape:", met.shape)
    #  print("time_start.shape:", time_start.shape)
    #  print("spinbin2.shape:", spinbin2.shape)
    #   print("esa_step.shape:", esa_step.shape)
    #   print("esa_flags.shape:", esa_flags.shape)

    #  print("met_check.shape:", met_check.shape)
    #  print("spin_check.shape:", spin_check.shape)
    # print("esa_check.shape:", esa_check.shape)

        # Reduce across goodtime intervals: True if event passes any interval
    mask = np.any(event_pass, axis=1)  # shape -> (N_events,)

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
        'epoch': unfiltered['epoch'][mask],
        'met': unfiltered['met'][mask],
        'exposure': unfiltered['exposure'][mask,:,:],
        'h_counts': unfiltered['h_counts'][mask,:,:],
        'o_counts': unfiltered['o_counts'][mask,:,:],
        'h_rates': unfiltered['h_rates'][mask,:,:],
        'o_rates': unfiltered['o_rates'][mask,:,:]
    }
    
    for k in ('epoch','met'):
        d = pd.DataFrame(filtered[k])
        d.to_csv(f"{out_file}_{k}.csv", index=False)

    for iesa in range(0,7):
        esa = iesa + 1
        for k in ('exposure','h_counts','o_counts','h_rates','o_rates'):
            d = pd.DataFrame(filtered[k][:,iesa,:])
            d.to_csv(f"{out_file}_{k}_{esa}.csv", index=False)

def doy_fraction(t):
    start = datetime(t.year, 1, 1)
    return (t - start).total_seconds() / 86400.0 + 1

def argParsing():

    parser = argparse.ArgumentParser(description='This tool accepts a GSEOS filename and makes cool plots for IMAP-Lo.')
    
    parser.add_argument('-f', '--file',
                            help='the GSEOS event file list',
                           dest='file',
                           required=True)
    
    parser.add_argument('-g', '--goodtime_file',
                        help='the goodtime file',
                        dest='goodtime_file',
                        required=True)
    
    parser.add_argument('-o', '--outputFile',
                        help='the plot output file',
                        dest='outFile',
                        required=True)

    return parser.parse_args()

# main

args = argParsing()

#file = "/Users/hafijulislam/Library/CloudStorage/Box-Box/First_light_maps/DN/Instrument_FM1_playback_301_ILO_SCI_DE_dec_20251102T170018_DN.csv"


cdf = pycdf.CDF(args.file)

filter_and_write_cdf(
    cdf_file=args.file,
    goodtime_file=args.goodtime_file,
    out_file=args.outFile
)

    

