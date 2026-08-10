# May 18, 2023 - NAS
# in Version 2 we are adding the TOF3 < 20 ns criterion
#!/usr/bin/python
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import argparse
from scipy.optimize import curve_fit
import matplotlib.colors as colors
#import scipy.optimize.curve_fit as cf
#import scipy.curve_fit as cf
# from scipy.optimize import curve_fit

## constants
# bla = 10.0
# np.pi

TOF3_L = [ 10.0, 6.0, 2.0, 0.0 ]
TOF3_H = [14.0, 10.0, 6.0, 2.0 ]

checksum_lim  = [ 3.0, 3.0, 3.0, 3.0 ]
#  for GOLD, TOF2 < 15, TOF2 < 35 and > 35

minEvents = 3

def argParsing():

    parser = argparse.ArgumentParser(description='This tool accepts a GSEOS filename and makes cool plots for IMAP-Lo.')
    
    
    parser.add_argument('-f', '--file',
                            help='the GSEOS event file list',
                           dest='file',
                           required=True)
                           
    parser.add_argument('-o', '--output',
                        help='the plot output',
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
                        
    parser.add_argument('-s', '--delayLineCorr',
                    help='tofs delay-line correction for tof0 or tof1, 1: yes, 0:no (default to no correction)',
                    dest='s',
                    type=int,
                    choices=[0,1])

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

delayCorr=0
if args.s is not None:
    delayCorr=args.s

bins=20
if args.bins is not None:
    bins=args.bins

valid = [0, 0, 0, 0, 0]
if args.valid:
    if len(args.valid) != 5:
        raise ValueError(f"--valid requires exactly 5 values, got {len(args.valid)}: {args.valid}")
    valid = [int(x) for x in args.valid]

dpi=75
if args.dpi is not None:
    dpi = args.dpi

xMin = 1.0
xMax = 200.0
yMin = 1.0
yMax = 200.0

if args.xMin is not None:
    xMin = args.xMin
if args.xMax is not None:
    xMax = args.xMax
if args.yMin is not None:
    yMin = args.yMin
if args.yMax is not None:
    yMax = args.yMax

plottitle=args.outFile[-100:]
if (args.plottitle):
    plottitle=args.plottitle

if args.tofx not in (0, 1, 2):
    raise ValueError("--tofx must be 0, 1, or 2")

if args.tofy not in (0, 1, 2):
    raise ValueError("--tofy must be 0, 1, or 2")

for esa in range(1,8):

    m = (esa_stepA == esa)

    TOF0 = TOF0A[m]
    TOF1 = TOF1A[m]
    TOF2 = TOF2A[m]
    TOF3 = TOF3A[m]
    absent = absentA[m]
    mode_bit = mode_bitA[m]

    n = len(TOF0)
    if n < minEvents:
        print("1S08 2DTOF Failed total number of events = ", n, "esa = ", esa)
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
 
    quad = np.full(n, -1, dtype=int)   # default = no quadrant

    m0 = use_event & (TOF3 > TOF3_L[0]) & (TOF3 < TOF3_H[0])
    m1 = use_event & (TOF3 > TOF3_L[1]) & (TOF3 < TOF3_H[1])
    m2 = use_event & (TOF3 > TOF3_L[2]) & (TOF3 < TOF3_H[2])
    m3 = use_event & (TOF3 > TOF3_L[3]) & (TOF3 < TOF3_H[3])

    quad[m0] = 0
    quad[m1] = 1
    quad[m2] = 2
    quad[m3] = 3

    # print("number of valid TOF3 = ", nValid3)

    x0 = TOF0[use_event]
    x1 = TOF1[use_event]
    x2 = TOF2[use_event]
    x3 = TOF3[use_event]
    ncheck = len(x0)
    if (ncheck < minEvents): 
        print("1S08 2DTOF Failed number of events after valid selection = ", ncheck, "esa = ", esa)
        continue
         
    if (args.tofx == 0):
        xlabel = 'TOF0 (ns)'
        x = x0
        if (delayCorr ==1):
            x = x + 0.5*x3
            xlabel = 'TOF0s (ns)'
    if (args.tofx ==1):
        xlabel = 'TOF1 (ns)'
        x = x1
        if (delayCorr ==1):
            x = x - 0.5*x3
            xlabel = 'TOF1s (ns)'
    if (args.tofx ==2):
        xlabel = 'TOF2 (ns) '
        x = x2

    if (args.tofy ==0):
        ylabel = 'TOF0 (ns)'
        y = x0
        if (delayCorr ==1):
            y = y + 0.5*x3
            ylabel = 'TOF0s (ns)'
    if (args.tofy ==1):
        ylabel = 'TOF1 (ns)'
        y = x1
        if (delayCorr ==1):
            y = y - 0.5*x3
            ylabel = 'TOF1s (ns)'
    if (args.tofy ==2):
        ylabel = 'TOF2 (ns)'
        y = x2

    xlabel=xlabel+ 'ESA = '+str(esa) +' Valid:' +str(valid[0])+str(valid[1])+str(valid[2])+str(valid[3])+str(valid[4])

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

    if args.label is not None:
        if args.xlabel is None or args.ylabel is None or args.color is None:
            raise ValueError("--label requires --xlabel, --ylabel, and --color")
        if not (len(args.label) == len(args.xlabel) == len(args.ylabel) == len(args.color)):
            raise ValueError("label/xlabel/ylabel/color must have the same number of entries")
        nn = len(args.label)
        for ii in range(0,nn):
            ax.annotate(args.label[ii], xy=(args.xlabel[ii], args.ylabel[ii]),  xytext=(args.xlabel[ii], args.ylabel[ii]),color=plt.cm.cool(args.color[ii]))
            
    plt.hist2d(x, y, bins=bins, norm=colors.LogNorm(), cmin=1)
    font = {'size':14}
    mpl.rc('font', **font)
    plt.colorbar()
    #cbar.update_ticks()
    #cbar.ax.tick_params(labelsize=fontSize-6)
    #ax.set(xticks=[], yticks=[])

    font = {'size':22}
    mpl.rc('font', **font)

    plt.title(plottitle+' Valid: '+str(valid[0])+str(valid[1])+str(valid[2])+str(valid[3])+str(valid[4]), fontsize=fontSize-14)
    plt.xlim(xMin,xMax)
    plt.ylim(yMin,yMax)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    xname = f"TOF{args.tofx}"
    yname = f"TOF{args.tofy}"

    if delayCorr == 1 and args.tofx in (0, 1):
        xname += "s"
    if delayCorr == 1 and args.tofy in (0, 1):
        yname += "s"

    plt.savefig(f"{args.outFile}ESA{esa}{xname}vs{yname}.png", dpi=dpi, facecolor='w', edgecolor='w', orientation='portrait',format=None, transparent=False, bbox_inches=None, pad_inches=0.1)
    plt.close(fig1)

#ddat



#plt.show()

