# May 18, 2023 - NAS
# in Version 2 we are adding the TOF3 < 20 ns criterion
#!/usr/bin/python
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import argparse
from scipy.optimize import curve_fit
#import scipy.optimize.curve_fit as cf
#import scipy.curve_fit as cf
# from scipy.optimize import curve_fit

## constants
# bla = 10.0
# np.pi

TOF3_L = [ 11.0, 7.0, 3.5, 0.0 ]
TOF3_H = [15.0, 11.0, 7.0, 3.5 ]

checksum_lim  = [ 3.0, 3.0, 3.0, 3.0 ]
#  for GOLD, TOF2 < 15, TOF2 < 35 and > 35

minEvents = 3

def argParsing():

    parser = argparse.ArgumentParser(description='This tool accepts a GSEOS filename and makes cool plots for IMAP-Lo.')
    
    
    parser.add_argument('-f', '--file',
                            help='the event file list',
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
                                                 
    parser.add_argument('-v', '--valid',
                    help='valid flags for TOF0, TOF1, TOF2, TOF3, checksum',
                    nargs=5,
                    type=int,
                    choices=[0,1],
                    dest='valid')
                        
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
                        
    parser.add_argument('-noplot',
                        help='noplot',
                        dest='noplot', 
                        type=int)
    
    # -opt 0 for old file formats
    
    return parser.parse_args()

#

## main

args = argParsing()

spin_sec,  \
    TOF3A, \
    TOF2A, \
    TOF1A, \
    TOF0A, \
    absentA,mode_bitA,spinbinA,esa_stepA = np.loadtxt(args.file, delimiter=',', unpack=True, skiprows=1)

bins=20
if args.bins is not None:
    bins=args.bins

valid = [0, 0, 0, 0, 0]
if args.valid is not None:
    if len(args.valid) != 5:
        raise ValueError(f"--valid requires exactly 5 values, got {len(args.valid)}: {args.valid}")
    valid = [int(x) for x in args.valid]

dpi=75
if args.dpi is not None:
    dpi = args.dpi

plottitle=args.outFile[-100:]
if (args.plottitle):
    plottitle=args.plottitle

xMin = 0.0
xMax = 360.0
yMin = 0.8

if args.xMin is not None:
    xMin = args.xMin
if args.xMax is not None:
    xMax = args.xMax
if args.yMin is not None:
    yMin = args.yMin

for esa in range(1,8):
    m = (esa_stepA == esa)

    TOF0 = TOF0A[m]
    TOF1 = TOF1A[m]
    TOF2 = TOF2A[m]
    TOF3 = TOF3A[m]
    absent = absentA[m]
    mode_bit = mode_bitA[m]
    spinbin = spinbinA[m]

    n = len(TOF0)
    if n < minEvents:
        print("IDEAS Spinbin plot Failed total number of events = ", n, "esa = ", esa)
        continue

    valid_tof0 = (TOF0 >= 0.0)
    valid_tof1 = (TOF1 >= 0.0)
    valid_tof2 = (TOF2 >= 0.0)
    valid_tof3 = (TOF3 >= 0.0)
    valid_checksum = (absent == 0) & (mode_bit == 1)

    use_event = np.ones(n, dtype=bool)
    if valid[0]:
        use_event &= valid_tof0
    if valid[1]:
        use_event &= valid_tof1
    if valid[2]:
        use_event &= valid_tof2
    if valid[3]:
        use_event &= valid_tof3
    if valid[4]:
        use_event &= valid_checksum

#    print("valid args:", args.valid)

    x0 = TOF0[use_event]
    x1 = TOF1[use_event]
    x2 = TOF2[use_event]
    x3 = TOF3[use_event]
    ncheck = len(x0)
    if (ncheck < minEvents): 
        print("1S12 spinbin Ideas Failed number of events after valid selection = ", ncheck, "esa = ", esa)
        continue

#    print("number of valid TOF3 = ", nValid3)

    x = spinbin[use_event]*360.0/3600.0

    xlabel='Spin angle from NEP (deg)'+' ESAstep = '+str(esa)

    hist0, bin_edges0 = np.histogram(x, bins=bins, range=(xMin,xMax))
    max0 = np.max(hist0)

    if args.yMax is None:
        yMax_local = 1.1 * max0 if max0 > 0 else 1.0
    else:
        yMax_local = args.yMax

    yMin_local = yMin
    if yMax_local <= yMin_local:
        yMax_local = yMin_local + 1.0

    xMax_local = xMax
    if xMax_local <= xMin:
        xMax_local = xMin + 1.0

    ylabel='Counts'

    fontSize = 22
    font = {'weight':'bold', 'size':fontSize}
    mpl.rc('font', **font)

    left=0.15
    right= 0.98
    top = 0.9
    bottom=0.1

    if args.noplot is None: 

        fig1 = plt.figure(figsize=(10.0,10.0))
        ax = fig1.add_subplot(111)
        plt.tick_params(axis='both', labelbottom='on')
        fig1.subplots_adjust(left=left,right=right,bottom=bottom,top=top)

        #ax.set_yscale('log')
        ax.set_yscale('log')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        ax.axis([xMin, xMax_local, yMin_local, yMax_local])

        if args.label is not None:
            if args.xlabel is None or args.ylabel is None or args.color is None:
                raise ValueError("--label requires --xlabel, --ylabel, and --color")
            if not (len(args.label) == len(args.xlabel) == len(args.ylabel) == len(args.color)):
                raise ValueError("label/xlabel/ylabel/color must have the same number of entries")
            nn = len(args.label)
            for ii in range(0,nn):
                ax.annotate(args.label[ii], xy=(args.xlabel[ii], args.ylabel[ii]),  xytext=(args.xlabel[ii], args.ylabel[ii]),color=plt.cm.cool(args.color[ii]))

        # plt.style.use('seaborn-whitegrid') # nice and clean grid
        # plt.bar(bin_edges0, hist0)
        plt.hist(x, bins=bins, facecolor = 'b', edgecolor='k', linewidth=0.5, range=(xMin,xMax))

        plt.title(plottitle+' Valid: '+str(valid[0])+str(valid[1])+str(valid[2])+str(valid[3])+str(valid[4]), fontsize=fontSize-14)
        plt.xlabel(xlabel)
        plt.ylabel('Counts')
        # plt.legend()

        plt.savefig(args.outFile+'ESA'+str(esa)+'.png', dpi=dpi, facecolor='w', edgecolor='w', orientation='portrait', format=None, transparent=False, bbox_inches=None, pad_inches=0.1)
        plt.close(fig1)
    np.savetxt(args.outFile+'ESA'+str(esa)+'.csv',np.c_[bin_edges0[:-1], bin_edges0[1:], hist0],  delimiter = ',',header="binEdge0,binEdge1,histogram")
    
