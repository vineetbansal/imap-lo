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

cols = ['shcoarse', 'absent', 'timestamp', 'egy', 'mode', 'TOF0', 'TOF1', 'TOF2', 'TOF3', 'checksum', 'position']

def doy_fraction(t):
    start = datetime(t.year, 1, 1)
    return (t - start).total_seconds() / 86400.0 + 1

def argParsing():

    parser = argparse.ArgumentParser(description='This tool accepts a GSEOS filename and makes cool plots for IMAP-Lo.')
    
    parser.add_argument('-f', '--file',
                            help='the l1b file',
                           dest='file',
                           required=True)
    
    parser.add_argument('-o', '--outputFile',
                        help='the plot output file',
                        dest='outFile',
                        required=True)

    return parser.parse_args()

# main

args = argParsing()

#file = "/Users/hafijulislam/Library/CloudStorage/Box-Box/First_light_maps/DN/Instrument_FM1_playback_301_ILO_SCI_DE_dec_20251102T170018_DN.csv"

epoch = datetime(2010, 1, 1, 0, 0, 0)

cdf = pycdf.CDF(args.file)

data = {}

#absent: CDF_INT8 [21764]
#avg_spin_durations: CDF_DOUBLE [21764]
#badtimes: CDF_INT8 [21764]
#coincidence_type: CDF_CHAR*6 [21764]
#epoch: CDF_TIME_TT2000 [21764]
#esa_mode: CDF_INT8 [21764]
#esa_step: CDF_INT8 [21764]
#event_met: CDF_DOUBLE [21764]
#hae_x: CDF_DOUBLE [21764]
#hae_y: CDF_DOUBLE [21764]
#hae_z: CDF_DOUBLE [21764]
#mode_bit: CDF_INT8 [21764]
#off_angle_bin: CDF_INT8 [21764]
#pivot_angle: CDF_DOUBLE [1] NRV
#pos: CDF_INT8 [21764]
#shcoarse: CDF_UINT4 [21764]
#species: CDF_CHAR*1 [21764]
#spin_bin: CDF_INT8 [21764]
#spin_cycle: CDF_INT8 [21764]
#tof0: CDF_DOUBLE [21764]
#tof1: CDF_DOUBLE [21764]
#tof2: CDF_DOUBLE [21764]
#tof3: CDF_DOUBLE [21764]

# 'absent', 'avg_spin_durations', 'badtimes', 'coincidence_type'
# 'epoch', 'esa_mode', 'esa_step', 'event_met', 'hae_x', 'hae_y', 'hae_z'
# 'mode_bit', 'off_angle_bin', 'pivot_angle', 'pos', 'shcoarse', 'species'
# 'spin_bin', 'spin_cycle', 'tof0', 'tof1', 'tof2','tof3'

data = {}

var = 'esa_step'
esa_step = cdf[var][:]
    
var = 'absent'
absent = cdf[var][:]

var = 'mode_bit'
mode_bit = cdf[var][:]

var = 'tof0'
tof0 = cdf[var][:]

var = 'tof1'
tof1 = cdf[var][:]
    
var = 'tof2'
tof2 = cdf[var][:]
    
var = 'tof3'
tof3 = cdf[var][:]

var = 'badtimes'
badtime = cdf[var][:]

var = 'event_met'
met = cdf[var][:]

var = 'spin_bin'
spinbin = cdf[var][:]

ofile = args.outFile

n = len(met)

with open(ofile, 'w') as fle:

    print( f"met,tof3,tof2,tof1,tof0,absent,mode_bit,spinbin,esa_step", file=fle  )
    for i in range(0,n):
        if (badtime[i]==0):
            print( 
                f"{met[i]},{tof3[i]},{tof2[i]},{tof1[i]},{tof0[i]},{absent[i]},{mode_bit[i]},{spinbin[i]},{esa_step[i]}", file=fle
                )

#fluxT = flux.T
#dflxT = dflx.T

    

