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
    
    parser.add_argument('-opt',
                        help='option ',
                        type=int,
                        dest='option')
    # -opt 1 for instrument files
    
    return parser.parse_args()



## main

args = argParsing()

option = 1
if (args.option > 1):
    option = args.option

if (option == 1):
    spin_sec,  \
        TOF3A, \
        TOF2A, \
        TOF1A, \
        TOF0A, \
        absentA,mode_bitA,spinbinA,esa_stepA = np.loadtxt(args.file, delimiter=',', unpack=True, skiprows=1)
        
# instrument option
if (option == 2):
    spin_sec, pac, mcp, spin_subsec,  \
        ValidStart3, ValidStop3, ValidTOF3, TOF3, \
        ValidStart2, ValidStop2, ValidTOF2, TOF2, \
        ValidStart1, ValidStop1, ValidTOF1, TOF1, \
        ValidStart0, ValidStop0, ValidTOF0, TOF0 = np.loadtxt(args.file, delimiter=',', unpack=True, skiprows=1)

for esa in range(1,8):
    ind = np.where(esa_stepA == esa)
    TOF3 = TOF3A[ind]
    TOF2 = TOF2A[ind]
    TOF1 = TOF1A[ind]
    TOF0 = TOF0A[ind]
    absent = absentA[ind]
    mode_bit = mode_bitA[ind]

    n = len(TOF1)
    if (n<2):
        print("1S13 checksum Failed total number of events = ", n, "esa = ", esa)
        continue

    ValidTOF0 = np.linspace(1,1,n)
    ValidTOF1 = np.linspace(1,1,n)
    ValidTOF2 = np.linspace(1,1,n)
    ValidTOF3 = np.linspace(1,1,n)

    ind0 = np.where(TOF0 < 0.0)
    ValidTOF0[ind0] = 0
    ind1 = np.where(TOF1 < 0.0)
    ValidTOF1[ind1] = 0
    ind2 = np.where(TOF2 < 0.0)
    ValidTOF2[ind2] = 0
    ind3 = np.where(TOF3 < 0.0)
    ValidTOF3[ind3] = 0

#print("valid args:", args.valid)

    tmin = args.tofmin
    tmax = args.tofmax
            
    # valid 4 is the checksum

    valid = [1,1,1,1,0]

    useEvent = np.linspace(0, 0, n)
    checksumEvent = np.linspace(1000., 1000., n)
    checksumEventDN = np.linspace(1000., 1000., n)
    useSum = valid[0]*10000+1000*valid[1]+100*valid[2]+10*valid[3]+1*valid[4]
 #   print("useSum = ", useSum)

    x0 = TOF0
    x1 = TOF1
    x2 = TOF2
    x3 = TOF3

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

    for i in range(0,n):
    # tof 3 plut tof0 minues( tof1 plus tof2)
        validSum = ValidTOF0[i]*10000 + 1000*ValidTOF1[i] + 100*ValidTOF2[i] + 10*ValidTOF3[i]
        if (validSum == 11110):
            checksum = np.abs(TOF3[i] + TOF0[i] - ( TOF1[i] + TOF2[i] ))
            checksumEvent[i] = TOF3[i] + TOF0[i] - ( TOF1[i] + TOF2[i] )
            if (args.useDN ):
                checksumEventDN[i] =   (TOF3[i] - 1.196257711)/0.167384315 \
                                    + (TOF0[i] - 0.422575526)/0.165422296 \
                                    - (TOF1[i] - 0.458300954)/0.165758627 \
                                    - (TOF2[i] - 0.314410275)/0.165961041

        else:
            checksum = 10.0
            
        validChecksum = 0
        if ((absent[i] == 0) & (mode_bit[i] == 1)):
    #    if ((checksum < checksum_lim[0]) and (TOF3[i] < 20)):
            validChecksum = 1

        if (args.allTriples):
            validChecksum = valid[4]


        useCheck = ValidTOF0[i]*10000 + \
                ValidTOF1[i]*1000 + \
                ValidTOF2[i]*100 + \
                ValidTOF3[i]*10 + \
                validChecksum*1

                
        if ((useCheck == useSum) and (x[i] < tmax) and (x[i] > tmin)):
            useEvent[i] = 1
        
    quad = np.linspace(10, 10, n)

    nValid3 = 0
    for i in range(0,n):
        if ((ValidTOF3[i] == 1) and (TOF3[i] < 20)):
                nValid3 += 1
        
        if (useEvent[i] == 1):
            tof = TOF3[i]
            if ((tof > TOF3_L[0]) and (tof < TOF3_H[0])):
                quad[i] = 0
            elif ((tof > TOF3_L[1]) and (tof < TOF3_H[1])):
                quad[i] = 1
            elif ((tof > TOF3_L[2]) and (tof < TOF3_H[2])):
                quad[i] = 2
            elif ((tof > TOF3_L[3]) and (tof < TOF3_H[3])):
                quad[i] = 3

    bins=20
    if (args.bins):
            bins = args.bins

   # print("number of valid TOF3 = ", nValid3)

    ind0 = np.where(useEvent==1)


    if (args.useDN ):
        xx = checksumEventDN[ind0]
    else:
        xx = checksumEvent[ind0]

    ncheck = len(xx)
    if (ncheck < 3): 
        print("1S13 Checksum Failed number of events after valid selection = ", ncheck, "esa = ", esa)
        continue

#    print("Checksum Min and Max: ",np.min(xx),np.max(xx))

    dpi=75
    if (args.dpi):
            dpi = args.dpi

    xMin = -10.
    xMax = 10.
    yMin = 0.8

    if (args.xMin):
            xMin = args.xMin
    if (args.xMax):
            xMax = args.xMax

    hist0, bin_edges0 = np.histogram(xx, bins=bins, range=(xMin,xMax))
    max0 = np.max(hist0)
    yMax = 1.1*max0

    if (args.yMin):
            yMin = args.yMin
    if (args.yMax):
            yMax = args.yMax

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

    if (args.label):
        nn = len(args.label)
        for ii in range(0,nn):
            ax.annotate(args.label[ii], xy=(args.xlabel[ii], args.ylabel[ii]),  xytext=(args.xlabel[ii], args.ylabel[ii]),color=plt.cm.cool(args.color[ii]))

    plottitle=args.outFile[-100:]
    if (args.plottitle):
            plottitle=ags.plottitle

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
   #  plt.legend()
    plt.savefig(args.outFile+'ESA'+str(esa)+'TOF'+str(args.tof)+'.png', dpi=args.dpi, facecolor='w', edgecolor='w',
                orientation='portrait', format=None, transparent=False, bbox_inches=None, pad_inches=0.1)

    n = len(hist0)

    np.savetxt(args.outFile+'ESA'+str(esa)+'TOF'+str(args.tof)+'.csv',np.c_[bin_edges0[0:n],bin_edges0[1:n+1], hist0],  delimiter = ',',header="binEdge0,binEdge1,histogram")

