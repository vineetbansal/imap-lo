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

#  The Proto2 conversions are:
# TOF0 ns = 0.422575526 + DN0 * 0.165422296
# TOF1 ns = 0.458300954 + DN1 * 0.165758627
# TOF2 ns = 0.314410275 + DN2 * 0.165961041
# TOF3 ns = 1.196257711 + DN3 * 0.167384315
 
# TOF0 DN = (TOF0 - 0.422575526) / 0.165422296
# TOF1 DN = (TOF1 - 0.458300954) / 0.165758627
# TOF2 DN = (TOF2 - 0.314410275) / 0.165961041
# TOF3 DN = (TOF3 - 1.196257711) / 0.167384315

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
                        
    parser.add_argument('-t', '--tof',
                        help='tof 0,1, or 2',
                        dest='tof',
                        type=int,
                        required=True)
                        
    parser.add_argument('-tmin', '--tofmin',
                        help='tof min',
                        dest='tofmin',
                        type=float,
                        required=True)
                        

    parser.add_argument('-tmax', '--tofmax',
                        help='tof max',
                        dest='tofmax',
                        type=float,
                        required=True)
                        

 #   parser.add_argument('-v', '--valid',
 #                       help='valid flags for TOF0, TOF1, TOF2, TOF3, checksum',
 #                       nargs="+",
 #                       dest='valid' )
                        
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

    parser.add_argument('-dn',
                        help='plot checksum in bits (DN)',
                        type=int,
                        dest='useDN')

    parser.add_argument('-at',
                        help='Plot all triples regardless of checksum validity',
                        type=int,
                        dest='allTriples')
    
    # -opt 1 for instrument files
    
    return parser.parse_args()



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

dpi=75
if args.dpi is not None:
    dpi = args.dpi

if args.tof not in (0, 1, 2):
    raise ValueError("--tof must be 0, 1, or 2")

useDN = (args.useDN == 1)

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
        print("checkdist Failed total number of events = ", n, "esa = ", esa)
        continue

    valid_tof0 = (TOF0 >= 0.0)
    valid_tof1 = (TOF1 >= 0.0)
    valid_tof2 = (TOF2 >= 0.0)
    valid_tof3 = (TOF3 >= 0.0)
    valid_checksum = (absent == 0) & (mode_bit == 1)

    # valid 4 is the checksum
    valid = [1,1,1,1,1]
    if args.allTriples:
        valid[4] = 0

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

#print("valid args:", args.valid)

    x0 = TOF0[use_event]
    x1 = TOF1[use_event]
    x2 = TOF2[use_event]
    x3 = TOF3[use_event]
    ncheck = len(x0)
    if (ncheck < minEvents): 
        print("checksumDist Failed number of events after valid selection = ", ncheck, "esa = ", esa)
        continue

    tmin = args.tofmin
    tmax = args.tofmax
    
    xlabel='chcksum'+' ESA='+str(esa)
    if (args.useDN ):
        xlabel = xlabel + ' (DN)'

    if (args.tof ==0):
        xlabel = xlabel + ' with TOF0 cstrnt '+str(tmin)+'->'+str(tmax)
        x = x0
    if (args.tof ==1):
        xlabel = xlabel + ' with TOF1 cstrnt '+str(tmin)+'->'+str(tmax)
        x = x1
    if (args.tof ==2):
        xlabel = xlabel + ' with TOF2 cstrnt '+str(tmin)+'->'+str(tmax)
        x = x2

    m_tof = (x > tmin) & (x < tmax)
    x  = x[m_tof]
    x0 = x0[m_tof]
    x1 = x1[m_tof]
    x2 = x2[m_tof]
    x3 = x3[m_tof]
    ncheck = len(x)
    if ncheck < minEvents:
        print("Checksum Failed number of events after TOF window = ", ncheck, "esa = ", esa)
        continue

    checksumEventDN = np.linspace(0,0,ncheck)
    checksumEvent = np.linspace(0,0,ncheck)
    for i in range(0,ncheck):
    # tof 3 plut tof0 minues( tof1 plus tof2)
        checksumEvent[i] = x3[i] + x0[i] - ( x1[i] + x2[i] )
        if useDN:
            checksumEventDN[i] =   (x3[i] - 1.196257711)/0.167384315 \
                                + (x0[i] - 0.422575526)/0.165422296 \
                                - (x1[i] - 0.458300954)/0.165758627 \
                                - (x2[i] - 0.314410275)/0.165961041
            
   # print("number of valid TOF3 = ", nValid3)

    if (args.useDN ):
        xx = checksumEventDN
    else:
        xx = checksumEvent

    ncheck = len(xx)
    if (ncheck < minEvents): 
        print("Checksum Failed number of events after valid selection = ", ncheck, "esa = ", esa)
        continue
    
    xMin = -10.
    xMax = 10.
    yMin = 0.8

    if args.xMin is not None:
            xMin = args.xMin
    if args.xMax is not None:
            xMax = args.xMax

    hist0, bin_edges0 = np.histogram(xx, bins=bins, range=(xMin,xMax))
    max0 = np.max(hist0)
    
    yMax = 1.1 * max0 if max0 > 0 else 1.0

    if args.yMin is not None:
        yMin = args.yMin
    if args.yMax is not None:
        yMax = args.yMax

    if yMax <= yMin:
        yMax = yMin + 1.0

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
    ax.set_yscale('log')
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
            
    plottitle=args.outFile[-100:]
    if args.plottitle is not None:
            plottitle=args.plottitle


    # plt.style.use('seaborn-whitegrid') # nice and clean grid
    # plt.bar(bin_edges0, hist0)
    plt.hist(xx, bins=bins, facecolor = 'b', edgecolor='k', linewidth=0.5, range=(xMin,xMax))

    plt.title(plottitle+' Valid: '+str(valid[0])+str(valid[1])+str(valid[2])+str(valid[3])+str(valid[4]), fontsize=fontSize-14)

    if (args.allTriples):
        xlabel=xlabel+', All Triples'
    else:
        xlabel=xlabel+', Valid:' +str(valid[0])+str(valid[1])+str(valid[2])+str(valid[3])+str(valid[4])
    plt.xlabel(xlabel)
    plt.ylabel('Counts')
   # plt.legend()
    plt.savefig(args.outFile+'ESA'+str(esa)+'TOF'+str(args.tof)+'.png', 
            dpi=dpi, facecolor='w', edgecolor='w',
            orientation='portrait', format=None,
            transparent=False, bbox_inches=None, pad_inches=0.1)
    plt.close(fig1)


    np.savetxt(args.outFile+'ESA'+str(esa)+'TOF'+str(args.tof)+'.csv',
           np.c_[bin_edges0[:-1], bin_edges0[1:], hist0],
           delimiter=',',
           header="binEdge0,binEdge1,histogram")
    

