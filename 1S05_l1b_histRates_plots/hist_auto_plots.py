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
import re
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.colors import PowerNorm


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

def doy_fraction(t):
    start = datetime(t.year, 1, 1)
    return (t - start).total_seconds() / 86400.0 + 1

def remap_spin_bins(h):
    return np.concatenate(
        (h[:, :, 50:60], h[:,:, 0:20], h[:, :, 20:50]),
        axis=2
    )

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
    
    parser.add_argument('-n', '--ncycle_sum',
                        help='the number of cycles to sum',
                        dest='ncycle_sum',
                        type=int,
                        required=True)


    return parser.parse_args()

# main

args = argParsing()

#file = "/Users/hafijulislam/Library/CloudStorage/Box-Box/First_light_maps/DN/Instrument_FM1_playback_301_ILO_SCI_DE_dec_20251102T170018_DN.csv"

epoch = datetime(2010, 1, 1, 0, 0, 0)

cdf = pycdf.CDF(args.file)
# cdf_l1c = pycdf.CDF(args.cfle)

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

# # pivot = cdf_l1c['pivot_angle'][0]

ncycle_sum = args.ncycle_sum
interval_nom = 420 * ncycle_sum

exposure = 420 * ncycle_sum * 0.5

# print('expo =', exposure)

for var in ('h_counts','o_counts'):

    d = np.sum(cdf[var][:, 0:6, 20:49], axis=(1,2))
    epoch = cdf['epoch'][:]
    m0 = met_from_epoch(epoch[0])
# print("m0 = ", m0)

    date = re.search(r"\d{8}", args.file).group()

# ------------------------------------------------------------
# INPUT DATA (from your pipeline)
# ------------------------------------------------------------
    epoch = cdf['epoch'][:]                     # shape (ntime,)
#h_counts = cdf['h_counts'][:]               # (ntime, nesa, nspin)

    h_counts = cdf[var][:,:,:]

    # Assume data_list is a list of 2D arrays, one per ESA step
    vmin1 = min([np.min(d) for d in h_counts])
    vmax1 = max([np.max(d) for d in h_counts])

# Summed diagnostic (your exact line)
    d = np.sum(h_counts[:, 0:6, 20:49], axis=(1, 2))

    total = np.sum(d)

# ------------------------------------------------------------
# Convert epoch -> MET seconds (relative to first sample)
# ------------------------------------------------------------
    met = np.array([(t - epoch[0]).total_seconds() for t in epoch])

    t0 = epoch[0]  # your starting datetime

    start_doy = t0.timetuple().tm_yday \
                + t0.hour/24 \
                + t0.minute/(24*60) \
             + t0.second/(24*3600) \
             + t0.microsecond/(24*3600*1e6)

    doy = start_doy + met / (24*3600)  # 24*3600 = seconds per day

# ------------------------------------------------------------
# Build ESA heatmaps: (spin_bin, time)
# ------------------------------------------------------------
    n_esa = 7

    h_cnt_nep = remap_spin_bins(h_counts)

    esa_maps = [h_cnt_nep[:, i, :].T for i in range(n_esa)]
    spin_bins = np.arange(h_cnt_nep.shape[2])

# ------------------------------------------------------------
# FIGURE + GRIDSPEC LAYOUT
# ------------------------------------------------------------
    fig = plt.figure(figsize=(15, 10))

    gs = GridSpec(
        n_esa + 1, 2,
        width_ratios=[30, 1],        # plots | colorbar
        height_ratios=[1] + [1]*n_esa,
        hspace=0.08,
        wspace=0.05 
    )

# Left column axes
    axes = [fig.add_subplot(gs[i, 0]) for i in range(n_esa + 1)]

# Right column colorbar axis (ESA panels only)
    cax = fig.add_subplot(gs[1:, 1])

# ------------------------------------------------------------
# TOP PANEL: summed diagnostic
# ------------------------------------------------------------
    axes[0].plot(doy, d, linewidth=1)
    axes[0].set_ylabel("Summed \nARam \nCounts", fontsize=12)
    axes[0].grid(True, alpha=0.3)

# ------------------------------------------------------------
# ESA HEATMAP PANELS
# ------------------------------------------------------------
    im = None
    for i in range(n_esa):
        ax = axes[i + 1]

        norm = PowerNorm(gamma=0.15, vmin=0.0, vmax=vmax1)

        im = ax.imshow(
            esa_maps[i],
            aspect='auto',
            origin='lower',
            extent=[
                doy.min(), doy.max(),
                spin_bins.min(), spin_bins.max()
            ],
#        vmin=0,
#       vmax=vmax, 
            norm=norm
        )  

        ax.set_ylabel(f"ESA {i+1}\nNEP", fontsize=14)
        ax.set_yticks([0, spin_bins.max()])
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.tick_params(axis='x', labelsize=12)  # increase x-axis tick label size
        ax.tick_params(axis='y', labelsize=12)

# ------------------------------------------------------------
# COLORBAR (off to the side)
# ------------------------------------------------------------
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label("Counts", fontsize=14)
    cbar.ax.tick_params(labelsize=14) 
    cbar.ax.yaxis.labelpad = 10

# ------------------------------------------------------------
# OPTIONAL: vertical dashed red lines (good-time boundaries)
# ------------------------------------------------------------
# Example:
# goodtime_met = [1200, 2400, 3600]
# for ax in axes:
#     for tmark in goodtime_met:
#         ax.axvline(tmark, color='red', linestyle='--', linewidth=1)

# ------------------------------------------------------------
# LABELS + TITLE (with breathing room)
# ------------------------------------------------------------
    axes[-1].set_xlabel("DOY ", fontsize=14)

    fig.suptitle(
        f"IMAP-Lo {date} {var} total ARam = {total}",
        fontsize=16,
        y=0.97  
    )

    fig.subplots_adjust(
        left=0.08,
        right=0.92,
        top=0.90,
        bottom=0.06
    )


    file1 = args.file.replace('.cdf', '_'+var+'.png')     # replace extension
    png_file = file1.replace('../input_l1b_histrates', './output')   # move to output folder

    plt.savefig(png_file, dpi=200)
    plt.close()




