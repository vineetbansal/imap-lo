#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov  2 17:10:13 2025

@author: hafijulislam
"""

import pandas as pd
import numpy as np
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import argparse
from datetime import datetime, timedelta

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

    parser.add_argument('-b', '--bins',
                        help='the number of bins for histograms',
                        dest='bins',
                        type=int)
                        
    parser.add_argument('-tx', '--tofx',
                        help='tof on x 0,1, or 2',
                        dest='tofx',
                        type=int,
                        required=True)

    parser.add_argument('-ty', '--tofy',
                        help='tof on y 0,1, or 2',
                        dest='tofy',
                        type=int,
                        required=True)

    parser.add_argument('-v', '--valid',
                        help='1 for golden triples, 0 for silver triples',
                        dest='valid',
                        type=int,
                        required=True)

    parser.add_argument('-e', '--esa',
                        help='esa step, 1 - 7',
                        dest='esa',
                        type=int,
                        required=True)

    parser.add_argument('-time',
                        help='min and max times',
                        type=float,
                        nargs="+",
                        dest='times')

    parser.add_argument('-xmin',
                        help='minimum value for the x-axis',
                        type=float,
                        dest='xMin')
                        
    parser.add_argument('-xmax',
                        help='maximum value for the x-axis',
                        type=float,
                        dest='xMax')
                        
    parser.add_argument('-ymin',
                        help='minimum value for the y-axis',
                        type=float,
                        dest='yMin')
                        
    parser.add_argument('-ymax',
                        help='maximum value for the y-axis',
                        type=float,
                        dest='yMax')

    parser.add_argument('-dpi',
                        help='dpi of output image',
                        type=int,
                        dest='dpi')
                        
    parser.add_argument('-label',
                          help='labels',
                          nargs="+",
                          dest='label')
                          
    parser.add_argument('-xlabel',
                        help='x pos for labels',
                        nargs="+",
                        type=float,
                        dest='xlabel')

    parser.add_argument('-ylabel',
                        help='y pos for labels',
                        nargs="+",
                        type=float,
                        dest='ylabel')
                          
    parser.add_argument('-color',
                        help='color for labels',
                        nargs="+",
                        type=float,
                        dest='color')

    parser.add_argument('-plottitle',
                        help='plottitle',
                        dest='plottitle')



    return parser.parse_args()

# main

args = argParsing()

#file = "/Users/hafijulislam/Library/CloudStorage/Box-Box/First_light_maps/DN/Instrument_FM1_playback_301_ILO_SCI_DE_dec_20251102T170018_DN.csv"

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

df1 = pd.read_csv(args.file,names=cols,skiprows=1)

shis = df1['shcoarse'].to_numpy()
shist0 = shis[0]
shistn = shis[-1]
#print('shist0 = ',shist0)
#print('shistn = ',shistn)

if (args.times[0] == 0):
    args.times[0] = shist0
if (args.times[1] == 0):
    args.times[1] = shistn
    
if (shist0 > args.times[0]):
    args.times[0] = shist0
if (shistn < args.times[1]):
    args.times[1] = shistn

print('2D TOF time range =',args.times[0],args.times[1])
    
real_event = df1['shcoarse'].between(args.times[0],args.times[1])

df=df1[real_event]

if (args.valid ==0):
    df = df[(df['absent'] == 0) & ((df['mode'] == 0) | (df['mode'] == 1)) & (df['egy']== args.esa) ]
else:
    df = df[(df['absent'] == 0) & (df['mode'] == 1) & (df['egy']== args.esa) ] 
    
# df['tof0E'] = df['TOF0']*2*ADC_TOF0[1]+ADC_TOF0[0]
# df['tof2E'] = df['TOF2']*2*ADC_TOF2[1]+ADC_TOF2[0]
# df['tof3E']=  df['TOF3']*2*ADC_TOF3[1]+ADC_TOF3[0]

df['TOF1d'] = df['TOF0']+df['TOF3'] - df['TOF2'] + df['checksum']

df['TOF0'] = df['TOF0']*2*ADC_TOF0[1]+ADC_TOF0[0]
df['TOF2'] = df['TOF2']*2*ADC_TOF2[1]+ADC_TOF2[0]
df['TOF3'] =  df['TOF3']*2*ADC_TOF3[1]+ADC_TOF3[0]

# df['tof1E'] = np.where(df['mode']==1, tof1d*2*ADC_TOF1[1]+ADC_TOF1[0],df['TOF1']*2*ADC_TOF1[1]+ADC_TOF1[0])
df['TOF1'] = np.where(df['mode']==1, (df['TOF1d']*2*ADC_TOF1[1]+ADC_TOF1[0]),(df['TOF1']*2*ADC_TOF1[1]+ADC_TOF1[0]))

df['TOF0'] = df['TOF0'] + (df['TOF3']*0.5)
df['TOF1'] = df['TOF1'] - (df['TOF3']*0.5)

#use_event = np.linspace(1.,1.,n)

# Add a new column 'col3' with a list of values

df['quadrant'] = 1.0*df['TOF3']

tof3_array = df['TOF3'].to_numpy()

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

x0 = df['TOF0'].to_numpy()
x1 = df['TOF1'].to_numpy()
x2 = df['TOF2'].to_numpy()
x3 = df['TOF3'].to_numpy()

if (args.tofx ==0):
    if (args.valid ==0):
        xlabel = 'TOF0s (ns) (silver triples)'
    else:
        xlabel = 'TOF0s (ns) (golden triples)'
    x = x0
    
if (args.tofx ==1):
    if (args.valid ==0):
        xlabel = 'TOF1s (ns) (silver triples)'
    else:
        xlabel = 'TOF1s (ns) (golden triples)'
    x = x1
if (args.tofx ==2):
    if (args.valid ==0):
        xlabel = 'TOF2 (ns) (silver triples)'
    else:
        xlabel = 'TOF2 (ns) (golden triples)'
    x = x2


if (args.tofy ==0):
    if (args.valid ==0):
        ylabel = 'TOF0s (ns) (silver triples)'
    else:
        ylabel = 'TOF0s (ns) (golden triples)'
    y = x0
    
if (args.tofy ==1):
    if (args.valid ==0):
        ylabel = 'TOF1s (ns) (silver triples)'
    else:
        ylabel = 'TOF1s (ns) (golden triples)'
    y = x1
if (args.tofy ==2):
    if (args.valid ==0):
        ylabel = 'TOF2 (ns) (silver triples)'
    else:
        ylabel = 'TOF2 (ns) (golden triples)'
    y = x2


xlabel = xlabel+' iESA = '+str(args.esa)

dpi=75
if (args.dpi):
    dpi = args.dpi

xMin = 1.0
xMax = 200.0
yMin = 1.0
yMax = 200.0

if (args.xMin):
    xMin = args.xMin
if (args.xMax):
    xMax = args.xMax

if (args.yMin):
    yMin = args.yMin
if (args.yMax):
    yMax = args.yMax

bins=20
if (args.bins):
    bins = args.bins


fontSize = 22
#font = {'weight':'bold', 'size':fontSize}
font = {'size':fontSize}
mpl.rc('font', **font)

left=0.15
right= 0.95
top = 0.95
bottom=0.1

fig1 = plt.figure(figsize=(10.0,8.0))
ax = fig1.add_subplot(111)
# ax = plt.subplots()
plt.tick_params(axis='both', labelbottom='on')
fig1.subplots_adjust(left=left,right=right,bottom=bottom,top=top)

#ax.set_yscale('log')
#ax.set_yscale('log')
ax.set_xlabel(xlabel)
ax.set_ylabel(ylabel)


ax.axis([xMin,xMax,yMin,yMax])

if (args.label):
    nn = len(args.label)
    for ii in range(0,nn):
        ax.annotate(args.label[ii], xy=(args.xlabel[ii], args.ylabel[ii]),  xytext=(args.xlabel[ii], args.ylabel[ii]),color=plt.cm.cool(args.color[ii]))
        
plottitle=args.outFile[-100:]
if (args.plottitle):
        plottitle=ags.plottitle

        
plt.hist2d(x, y, bins=bins, norm=colors.LogNorm())
font = {'size':14}
mpl.rc('font', **font)
plt.colorbar()
#cbar.update_ticks()
#cbar.ax.tick_params(labelsize=fontSize-6)
#ax.set(xticks=[], yticks=[])

font = {'size':22}
mpl.rc('font', **font)
        
plt.title(plottitle, fontsize=fontSize-14)
plt.xlim(xMin,xMax)
plt.ylim(yMin,yMax)
plt.xlabel(xlabel)
plt.ylabel(ylabel)

plt.savefig(args.outFile+'TOF'+str(args.tofx)+'vs'+str(args.tofy)+'.png', dpi=args.dpi, facecolor='w', edgecolor='w', orientation='portrait',format=None, transparent=False, bbox_inches=None, pad_inches=0.1)





    

