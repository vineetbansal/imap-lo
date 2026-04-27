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

minEvents=3

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
                        
    parser.add_argument('-v', '--valid',
                    help='valid flags for TOF0, TOF1, TOF2, TOF3, checksum',
                    nargs=5,
                    type=int,
                    choices=[0,1],
                    dest='valid')
                        
    parser.add_argument('-tmax', '--time_max',
                        help='max for TOF0, TOF1, or TOF2',
                        type=float,
                        dest='tmax' )
                        
    parser.add_argument('-tmin', '--time_min',
                        help='min for TOF0, TOF1, or TOF2',
                        type=float,
                        dest='tmin' )
                        
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

    parser.add_argument('-plottitle',
                        help='plottitle',
                        dest='plottitle')

    parser.add_argument('-color',
                        help='color for labels',
                        nargs="+",
                        type=float,
                        dest='color')

    # -opt 2 for other formats 

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
if args.valid:
    if len(args.valid) != 5:
        raise ValueError(f"--valid requires exactly 5 values, got {len(args.valid)}: {args.valid}")
    valid = [int(x) for x in args.valid]

dpi=75
if args.dpi is not None:
    dpi = args.dpi

for esa in range(1,8):
    m = (esa_stepA == esa)

    TOF0 = TOF0A[m]
    TOF1 = TOF1A[m]
    TOF2 = TOF2A[m]
    TOF3 = TOF3A[m]
    absent = absentA[m]
    mode_bit = mode_bitA[m]

    n = len(TOF1)
    if (n < minEvents):
        print("1S08 delay Failed total number of events = ", n, "esa = ", esa)
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

    x0 = TOF0[use_event]
    x1 = TOF1[use_event]
    x2 = TOF2[use_event]
    x3 = TOF3[use_event]
    ncheck = len(x0)
    if (ncheck < minEvents): 
        print("1S08 Delay Failed number of events after valid selection = ", ncheck, "esa = ", esa)
        continue


    denom = valid[0] + valid[1] + valid[2]

    if denom > 0:
        tof = (valid[0]*TOF0 +
           valid[1]*TOF1 +
           valid[2]*TOF2) / float(denom)

        if args.tmin is not None:
            use_event &= (tof >= args.tmin)

        if args.tmax is not None:   
            use_event &= (tof <= args.tmax)
        
    quad = np.full(n, -1, dtype=int)   # default = no quadrant

    m0 = use_event & (TOF3 > TOF3_L[0]) & (TOF3 < TOF3_H[0])
    m1 = use_event & (TOF3 > TOF3_L[1]) & (TOF3 < TOF3_H[1])
    m2 = use_event & (TOF3 > TOF3_L[2]) & (TOF3 < TOF3_H[2])
    m3 = use_event & (TOF3 > TOF3_L[3]) & (TOF3 < TOF3_H[3])

    quad[m0] = 0
    quad[m1] = 1
    quad[m2] = 2
    quad[m3] = 3

    n_valid_tof3 = np.count_nonzero(m0 | m1 | m2 | m3)
    if n_valid_tof3 < minEvents:
        print("1S08 delay Failed after valid selection with number of valid TOF3 = ", n_valid_tof3)
        continue
    
    x0 = TOF3[m0]
    hist0, bin_edges0 = np.histogram(x0,bins=bins,range=(TOF3_L[0],TOF3_H[0]))
    max_count = np.max(hist0)

    nb=bins

    bins1 = max(1, int(bins * (TOF3_H[1] - TOF3_L[1]) / (TOF3_H[0] - TOF3_L[0]) + 0.49))
    bins2 = max(1, int(bins * (TOF3_H[2] - TOF3_L[2]) / (TOF3_H[0] - TOF3_L[0]) + 0.49))
    bins3 = max(1, int(bins * (TOF3_H[3] - TOF3_L[3]) / (TOF3_H[0] - TOF3_L[0]) + 0.49))

  #  print(" Quad 0 ")
  #  print(hist0)
  #  print(bin_edges0)

    x1 = TOF3[m1]
   
    nb = nb + bins1
    hist1, bin_edges1 = np.histogram(x1,bins=bins1, range=(TOF3_L[1],TOF3_H[1]))

    max1 = np.max(hist1)
    max_count = np.max([max_count, max1])

  #  print(" ")
  #  print(" Quad 1 ")
  #  print(hist1)
  #  print(bin_edges1)

    x2 = TOF3[m2]
    
    nb = nb + bins2

    hist2, bin_edges2 = np.histogram(x2,bins=bins2,  range=(TOF3_L[2],TOF3_H[2]))

    max2 = np.max(hist2)
    max_count = np.max([max_count, max2])

  #  print(" ")
  #  print(" Quad 2 ")
  #  print(hist2)
  #  print(bin_edges2)

    x3 = TOF3[m3]
   
    nb = nb + bins3

    hist3, bin_edges3 = np.histogram(x3,bins=bins3, range=(TOF3_L[3],TOF3_H[3]))

    max3 = np.max(hist3)
    max_count = np.max([max_count, max3])

    pieces = [
        (bin_edges3, hist3),   # 0.0 - 3.5
        (bin_edges2, hist2),   # 3.5 - 7.0
        (bin_edges1, hist1),   # 7.0 - 11.0
        (bin_edges0, hist0),   # 11.0 - 15.0
    ]

    bin_edge0_all = np.concatenate([edges[:-1] for edges, hist in pieces])
    bin_edge1_all = np.concatenate([edges[1:]  for edges, hist in pieces])
    hist_all      = np.concatenate([hist       for edges, hist in pieces])

  #  print(" ")
  #  print(" Quad 3 ")
  #  print(hist3)
  #  print(bin_edges3)

    xMin = 0.0
    xMax = TOF3_H[0]
    yMin = 0.0
    yMax = 1.1*max_count

    if args.xMin is not None:
            xMin = args.xMin
    if args.xMax is not None:
            xMax = args.xMax

    if args.yMin is not None:
            yMin = args.yMin
    if args.yMax is not None:
            yMax = args.yMax

    xlabel='TOF3 (ns)'+' ESA='+str(esa)

    ylabel='Counts'

    fontSize = 22
    font = {'weight':'bold', 'size':fontSize}
    mpl.rc('font', **font)

    left=0.15
    right= 0.98
    top = 0.9
    bottom=0.1

    fig1 = plt.figure(figsize=(10.0,10.0))
    ax = fig1.add_subplot(111)
    plt.tick_params(axis='both', labelbottom='on')
    fig1.subplots_adjust(left=left,right=right,bottom=bottom,top=top)

    #ax.set_yscale('log')
    #ax.set_xscale('log')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if (xMax <= xMin):
        xMax= xMin + 1.0
    if (yMax <= yMin):
        yMax= yMin + 1.0
    ax.axis([xMin,xMax,yMin,yMax])

    if args.label is not None:
        if args.xlabel is None or args.ylabel is None or args.color is None:
            raise ValueError("--label requires --xlabel, --ylabel, and --color")
        if not (len(args.label) == len(args.xlabel) == len(args.ylabel) == len(args.color)):
            raise ValueError("label/xlabel/ylabel/color must have the same number of entries")
        nn = len(args.label)
        for ii in range(0,nn):
            ax.annotate(args.label[ii], xy=(args.xlabel[ii], args.ylabel[ii]),  xytext=(args.xlabel[ii], args.ylabel[ii]),color=plt.cm.cool(args.color[ii]))
            
    plottitle=args.outFile[-100:]
    if args.plottitle is not None:
            plottitle=args.plottitle

    # plt.style.use('seaborn-whitegrid') # nice and clean grid
    # plt.bar(bin_edges0, hist0)
    plt.hist(x0, bins=bins, facecolor = 'b', edgecolor='k', linewidth=0.5, label='Quad0', range=(TOF3_L[0],TOF3_H[0]))
    plt.hist(x1, bins=bins1, facecolor = 'r', edgecolor='k', linewidth=0.5, label='Quad1', range=(TOF3_L[1],TOF3_H[1]))
    plt.hist(x2, bins=bins2, facecolor = 'g', edgecolor='k', linewidth=0.5, label='Quad2', range=(TOF3_L[2],TOF3_H[2]))
    plt.hist(x3, bins=bins3, facecolor = 'y', edgecolor='k', linewidth=0.5, label='Quad3', range=(TOF3_L[3],TOF3_H[3]))
    
    ttl_note = f"{valid[0]}{valid[1]}{valid[2]}{valid[3]}{valid[4]}"
    if args.tmin is not None:
        ttl_note += f" tof{valid[0]}{valid[1]}{valid[2]} > {args.tmin}"
    if args.tmax is not None:
        ttl_note += f" tof{valid[0]}{valid[1]}{valid[2]} < {args.tmax}"

    plt.title(plottitle+' Valid: '+ttl_note, fontsize=fontSize-14)
    plt.xlabel(f"TOF3 (ns) Valid:{valid[0]}{valid[1]}{valid[2]}{valid[3]}{valid[4]}")
    plt.ylabel('Counts')
    plt.legend()
    plt.savefig(args.outFile+'ESA'+str(esa)+'.png', dpi=dpi, facecolor='w', edgecolor='w',
                orientation='portrait', format=None,
                transparent=False, bbox_inches=None, pad_inches=0.1)
    plt.close(fig1)

    np.savetxt(
        args.outFile + 'ESA' + str(esa) + '.csv',
        np.c_[bin_edge0_all, bin_edge1_all, hist_all],
        delimiter=',',
        header='binEdge0,binEdge1,histogram'
    )
                

#plt.show()


#ddat



#plt.show()

