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
                            help='the GSEOS event file list',
                           dest='file',
                           required=True)
    
    parser.add_argument('-e', '--esa',
                            help='the esa step',
                           dest='iesa',
                           type=int,
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

#epoch: CDF_TIME_TT2000 [179]
#esa_mode: CDF_INT8 [179]
#esa_step: CDF_UINT1 [7] NRV
#esa_step_label: CDF_CHAR*1 [7] NRV
#exposure_time_6deg: CDF_DOUBLE [179, 7, 60] NRV
#h_counts: CDF_UINT4 [179, 7, 60] NRV
#h_rates: CDF_DOUBLE [179, 7, 60] NRV
#o_counts: CDF_UINT4 [179, 7, 60] NRV
#o_rates: CDF_DOUBLE [179, 7, 60] NRV
#spin_bin_6: CDF_UINT1 [60] NRV
#spin_cycle: CDF_INT8 [179, 7] NRV

esa=args.iesa - 1
iesa = args.iesa

epoch = cdf['epoch'][:]
esa_mode = cdf['esa_mode'][:]
exposure = cdf['exposure_time_6deg'][:,esa,:]
h_counts = cdf['h_counts'][:,esa,:]
h_rates = cdf['h_rates'][:,esa,:]
o_counts = cdf['o_counts'][:,esa,:]
o_rates = cdf['o_rates'][:,esa,:]
spin_bin = cdf['spin_bin_6'][:]
spin_cycle = cdf['spin_cycle'][:,esa]

ofile = args.outFile

#fluxT = flux.T
#dflxT = dflx.T

epochF = pd.DataFrame(epoch)
epochF.to_csv(ofile+f"_epoch.csv", index=False)

esa_modeF = pd.DataFrame(esa_mode)
esa_modeF.to_csv(ofile+f"_esa_mode.csv", index=False)

exposureF = pd.DataFrame(exposure)
exposureF.to_csv(ofile+f"_exposure_{iesa}.csv", index=False)

spin_binF = pd.DataFrame(spin_bin)
spin_binF.to_csv(ofile+f"_spin_bin.csv", index=False)

spin_cycleF = pd.DataFrame(spin_cycle)
spin_cycleF.to_csv(ofile+f"_spin_cycle_{iesa}.csv", index=False)

h_countsF = pd.DataFrame(h_counts)
h_countsF.to_csv(ofile+f"_hcounts_{iesa}.csv", index=False)

h_ratesF = pd.DataFrame(h_rates)
h_ratesF.to_csv(ofile+f"_hrates_{iesa}.csv", index=False)

o_countsF = pd.DataFrame(o_counts)
o_countsF.to_csv(ofile+f"_ocounts_{iesa}.csv", index=False)

o_ratesF = pd.DataFrame(o_rates)
o_ratesF.to_csv(ofile+f"_orates_{iesa}.csv", index=False)

    

