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

cols = ['shcoarse', 'absent', 'timestamp', 'egy', 'mode', 'TOF0', 'TOF1', 'TOF2', 'TOF3', 'checksum', 'position']

def argParsing():

    parser = argparse.ArgumentParser(description='This tool accepts a GSEOS filename and makes cool plots for IMAP-Lo.')
    
    
    parser.add_argument('-f', '--file',
                            help='the GSEOS event file list',
                           dest='file',
                           required=True)
                           
    parser.add_argument('-o', '--outputFile',
                        help='the plot output file',
                        dest='outFile',
                        required=True)

    parser.add_argument('-c', '--outputFileCO',
                        help='the output file for CO',
                        dest='outFileCO',
                        required=True)

    parser.add_argument('-t', '--times',
                        help='the start and stop times',
                        dest='times',
                        nargs="+",
                        type=float,
                        required=True)
    
    parser.add_argument('-p', '--spinperiod',
                        help='the spin period in s',
                        dest='spinperiod',
                        type=float,
                        required=True)
    
    return parser.parse_args()

# main

args = argParsing()

#file = "/Users/hafijulislam/Library/CloudStorage/Box-Box/First_light_maps/DN/Instrument_FM1_playback_301_ILO_SCI_DE_dec_20251102T170018_DN.csv"

spin_duration = args.spinperiod

epoch = datetime(2010, 1, 1, 0, 0, 0)

columns = ["SHCOARSE", "ABSENT", "TIMESTAMP","EGY","MODE", "TOF0","TOF1","TOF2","TOF3","CHKSUM","POSITION","TOF1d"]
dtypes = {
    "SHCOARSE": int,
    "ABSENT": int,
    "TIMESTAMP":int,
    "EGY":int,
    "TOF0":float,
    "TOF1":float,
    "TOF2":float,
    "TOF3":float,
    "CHKSUM":int,
    "POSITION":str,
    "TOF1d":float
    }

cdf = pycdf.CDF(args.file)

data = {}

ct = cdf['coincidence_type'][:]
mode = cdf['mode'][:]
de_time = cdf['de_time'][:]
esa_step = cdf['esa_step'][:]
tof0 = cdf['tof0'][:]
tof1 = cdf['tof1'][:]
tof2 = cdf['tof2'][:]
tof3 = cdf['tof3'][:]
cksm = cdf['cksm'][:]
shcoarse = cdf['shcoarse']
de_count = cdf['de_count']
shcoarse_expanded = [shcoarse[j] for j in range(len(de_count)) for i in range(de_count[j]) ]
direct_events = cdf['direct_events'[:]]

# print(shcoarse)
# print(direct_events)

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

#print( df['coincidence_type']  )
# from spacepy import pycdf
# cdf = pycdf.CDF("./input/imap_lo_l1a_de_20260120-repoint00132_v001.cdf")
# cdf.keys()


# 'met', 'de_count', 'passes', 'coincidence_type', 'de_time', 'esa_step', 'mode', 
#  'tof0', 'tof1', 'tof2', 'tof3', 'cksm', 'pos', 'shcoarse', 'epoch', 'direct_events', 'direct_events_label'

# silver triples
# df = df[(df['absent'] == 0) & ((df['mode'] == 0) | (df['mode'] == 1))]

# only golden triples 
df = df[(df['coincidence_type'] == 0) & (df['mode'] == 1)]

# df['tof0E'] = df['TOF0']*2*ADC_TOF0[1]+ADC_TOF0[0]
# df['tof2E'] = df['TOF2']*2*ADC_TOF2[1]+ADC_TOF2[0]
# df['tof3E']=  df['TOF3']*2*ADC_TOF3[1]+ADC_TOF3[0]

df['tof1d'] = df['tof0']+df['tof3'] - df['tof2'] + df['cksm']

df['tof0'] = df['tof0']*ADC_TOF0[1]+ADC_TOF0[0]
df['tof2'] = df['tof2']*ADC_TOF2[1]+ADC_TOF2[0]
df['tof3'] =  df['tof3']*ADC_TOF3[1]+ADC_TOF3[0]

# df['tof1E'] = np.where(df['mode']==1, tof1d*2*ADC_TOF1[1]+ADC_TOF1[0],df['TOF1']*2*ADC_TOF1[1]+ADC_TOF1[0])
df['tof1'] = np.where(df['mode']==1, (df['tof1d']*ADC_TOF1[1]+ADC_TOF1[0]),(df['tof1']*ADC_TOF1[1]+ADC_TOF1[0]))

df['tof0'] = df['tof0'] + (df['tof3']*0.5)
df['tof1'] = df['tof1'] - (df['tof3']*0.5)

#use_event = np.linspace(1.,1.,n)

# Add a new column 'col3' with a list of values

df['quadrant'] = 1.0*df['tof3']

tof3_array = df['tof3'].to_numpy()

n = len(tof3_array)

quad = np.linspace(0., 0.,n)

for i in range(0, n):
    tof = tof3_array[i]
    
    if ((tof >= TOF3_L[0]) and (tof <= TOF3_H[0])):
        quad[i] = 0
    elif ((tof >= TOF3_L[1]) and (tof <= TOF3_H[1])):
        quad[i] = 1
    elif ((tof >= TOF3_L[2]) and (tof <= TOF3_H[2])):
        quad[i] = 2
    elif ((tof >= TOF3_L[3]) and (tof <= TOF3_H[3])):
        quad[i] = 3

df['quadrant'] = quad

df['pos'] = df['de_time']*((4.096e-3)*360.0/spin_duration) + 90.0 - 30.0
df['pos'] = df['pos'] % 360

real_event = df['tof0'].between(H_PEAK_L[0],H_PEAK_H[0]) & df['tof1'].between(H_PEAK_L[1],H_PEAK_H[1]) & df['tof2'].between(H_PEAK_L[2],H_PEAK_H[2]) & df['shcoarse'].between(args.times[0],args.times[1])

# real_event = df['tof0'].between(H_PEAK_L[0],H_PEAK_H[0]) & df['tof1'].between(H_PEAK_L[1],H_PEAK_H[1]) & df['tof2'].between(H_PEAK_L[2],H_PEAK_H[2])

#print(real_event)

# for i in range(0,n):
#    if (tarr0[i] < E_PEAK_H[0]):
#        use_event[i] = 0.0
#        df['absent'].values[i]=100
#    if (tarr1[i] < E_PEAK_H[1]):
#        use_event[i] = 0.0
#        df['absent'].values[i]=100
#    if (tarr2[i] < E_PEAK_H[2]):
#        use_event[i] = 0.0
#        df['absent'].values[i]=100
        
# ind = np.where(use_event==1.0)

# df.to_csv(args.outFile,index=False)

df[real_event].to_csv(args.outFile,index=False)

df1=df[real_event]

quadH = df1['quadrant'].to_numpy()

nH = len(quadH)

ind = np.where(quadH == 0)
n0 = len(ind[0])

ind = np.where(quadH == 1)
n1 = len(ind[0])

ind = np.where(quadH == 2)
n2 = len(ind[0])

ind = np.where(quadH == 3)
n3 = len(ind[0])

dt = args.times[1] - args.times[0]
print('Delta t', dt)
print('All ESA H:')
print(f"{'ESA':>10} {'N':>10} {'Q0':>10} {'Q1':>10} {'Q2':>10} {'Q3':>10}")
print(f"{'All':>10} {nH:>10} {n0:>10} {n1:>10} {n2:>10} {n3:>10}")


out = Path(args.outFile)

for iesa in range(1,8):
    
    esa = (df1['esa_step'] == iesa)
    
    df3=df1[esa]

    quadH = df3['quadrant'].to_numpy()

    nH = len(quadH)

    ind = np.where(quadH == 0)
    n0 = len(ind[0])

    ind = np.where(quadH == 1)
    n1 = len(ind[0])

    ind = np.where(quadH == 2)
    n2 = len(ind[0])

    ind = np.where(quadH == 3)
    n3 = len(ind[0])

    print(f"{iesa:>10} {nH:>10} {n0:>10} {n1:>10} {n2:>10} {n3:>10}")
    
    df3.to_csv(out.with_name(f"{out.stem}_{iesa}.csv"), index=False)

real_event_CO = df['tof0'].between(CO_PEAK_L[0],CO_PEAK_H[0]) & df['tof1'].between(CO_PEAK_L[1],CO_PEAK_H[1]) & df['tof2'].between(CO_PEAK_L[2],CO_PEAK_H[2])  & df['shcoarse'].between(args.times[0],args.times[1])

# real_event_CO = df['tof0'].between(CO_PEAK_L[0],CO_PEAK_H[0]) & df['tof1'].between(CO_PEAK_L[1],CO_PEAK_H[1]) & df['tof2'].between(CO_PEAK_L[2],CO_PEAK_H[2])  

df[real_event_CO].to_csv(args.outFileCO,index=False)

df2=df[real_event_CO]

quadCO = df2['quadrant'].to_numpy()

nCO = len(quadCO)

ind = np.where(quadCO == 0)
n0 = len(ind[0])

ind = np.where(quadCO == 1)
n1 = len(ind[0])

ind = np.where(quadCO == 2)
n2 = len(ind[0])

ind = np.where(quadCO == 3)
n3 = len(ind[0])

print('All ESA CO:')
print(f"{'ESA':>10} {'N':>10} {'Q0':>10} {'Q1':>10} {'Q2':>10} {'Q3':>10}")
print(f"{'All':>10} {nCO:>10} {n0:>10} {n1:>10} {n2:>10} {n3:>10}")

out = Path(args.outFileCO)

for iesa in range(1,8):
    
    esa = (df2['esa_step'] == iesa)
    
    df3=df2[esa]

    quadCO = df3['quadrant'].to_numpy()

    nCO = len(quadCO)

    ind = np.where(quadCO == 0)
    n0 = len(ind[0])

    ind = np.where(quadCO == 1)
    n1 = len(ind[0])

    ind = np.where(quadCO == 2)
    n2 = len(ind[0])

    ind = np.where(quadCO == 3)
    n3 = len(ind[0])

    print(f"{iesa:>10} {nCO:>10} {n0:>10} {n1:>10} {n2:>10} {n3:>10}") 

    df3.to_csv(out.with_name(f"{out.stem}_{iesa}.csv"), index=False)

    

