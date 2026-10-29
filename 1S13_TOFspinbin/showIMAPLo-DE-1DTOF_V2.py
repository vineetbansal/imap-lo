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
                                             
    parser.add_argument('-t', '--tof',
                        help='tof 0,1, or 2',
                        dest='tof',
                        type=int,
                        required=True)
                            
    parser.add_argument('-s', '--delayLineCorr',
                        help='tofs delay-line correction for tof0 or tof1, 1: yes, 0:no (default to no correction)',
                        dest='s',
                        type=int)
                    
    parser.add_argument('-v', '--valid',
                        help='valid flags for TOF0, TOF1, TOF2, TOF3, checksum',
                        nargs="+",
                        dest='valid' )
                        # set valid flag of TOF0 to 2 to use all events
                        
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
                        
    parser.add_argument('-nf',
                        help='no filter',
                        type=int,
                        dest='nofilter')
                        
    parser.add_argument('-opt',
                        help='option ',
                        type=int,
                        dest='option')
    # -opt 0 for old file formats
    
    return parser.parse_args()

#


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
        print("1S13 1DTOF Failed total number of events = ", n, "esa = ", esa)
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

#    print("valid args:", args.valid)

    filter = 1
    filtername='+Dbl-Flt'
    if (args.nofilter ):
        filter = 0
        filtername=' '

    if (filter == 1):
        for i in range(0,n):
            if ((ValidTOF0[i] > 0) and ((ValidTOF1[i] == 0 ) and (ValidTOF2[i] == 0 ))):
                TOF0[i]=-5.0
                ValidTOF0[i]=0

            if ((ValidTOF1[i] > 0) and ((ValidTOF0[i] == 0 ) and (ValidTOF2[i] == 0 ))):
                TOF1[i]=-5.0
                ValidTOF1[i]=0
            
    # valid 4 is the checksum
    valid = [0,0,0,0,0]
    if (args.valid ):
        if (args.valid[0] =='1'):
            valid[0] = 1
        if (args.valid[0] =='2'):
            valid[0] = 2  
        if (args.valid[1] =='1'):
            valid[1] = 1
        if (args.valid[2] =='1'):
            valid[2] = 1
        if (args.valid[3] =='1'):
            valid[3] = 1
        if (args.valid[4] =='1'):
            valid[4] = 1

    delayCorr=0
    if (args.s):
        delayCorr = args.s

    useEvent = np.linspace(0, 0, n)
    useSum = valid[0]*10000+1000*valid[1]+100*valid[2]+10*valid[3]+1*valid[4]
 #   print("useSum = ", useSum)
    for i in range(0,n):
    # tof 3 plut tof0 minues( tof1 plus tof2)
        validSum = ValidTOF0[i]*10000 + 1000*ValidTOF1[i] + 100*ValidTOF2[i] + 10*ValidTOF3[i]
        if (validSum == 11110):
            checksum = np.abs(TOF3[i] + TOF0[i] - ( TOF1[i] + TOF2[i] ))
        else:
            checksum = 100.0
            
        validChecksum = 0
        if ((absent[i] == 0) & (mode_bit[i] == 1)):
    #    if ((checksum < checksum_lim[0]) and (TOF3[i] < 20)):
            validChecksum = 1

        useCheck = ValidTOF0[i]*10000 + \
                ValidTOF1[i]*1000 + \
                ValidTOF2[i]*100 + \
                ValidTOF3[i]*10 + \
                validChecksum*1

        if (useSum > 15000):
             useSum = useCheck
            # this effectively skips the valid check and uses all events

        if (useCheck == useSum):
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

#    print("number of valid TOF3 = ", nValid3)

    ind0 = np.where(useEvent==1)
    x0 = TOF0[ind0]
    x1 = TOF1[ind0]
    x2 = TOF2[ind0]
    x3 = TOF3[ind0]

    ncheck = len(x0) + len(x1) + len(x2) 
    if (ncheck < 3): 
        print("1S13 1DTOF Failed number of events after valid selection = ", ncheck, "esa = ", esa)
        continue

    if (args.tof ==0):
        xlabel = 'TOF0 (ns) '+filtername+'ESA='+str(esa)+', Valid:' +str(valid[0])+str(valid[1])+str(valid[2])+str(valid[3])+str(valid[4])
        x = x0
        if (delayCorr ==1):
            x = x + 0.5*x3
            xlabel = 'TOF0s (ns) '+filtername+'ESA='+str(esa)+', Valid:' +str(valid[0])+str(valid[1])+str(valid[2])+str(valid[3])+str(valid[4])
    if (args.tof ==1):
        xlabel = 'TOF1 (ns) '+filtername+'ESA='+str(esa)+', Valid:' +str(valid[0])+str(valid[1])+str(valid[2])+str(valid[3])+str(valid[4])
        x = x1
        if (delayCorr ==1):
            x = x - 0.5*x3
            xlabel = 'TOF1s (ns) '+filtername+'ESA='+str(esa)+', Valid:' +str(valid[0])+str(valid[1])+str(valid[2])+str(valid[3])+str(valid[4])
    if (args.tof ==2):
        xlabel = 'TOF2 (ns)'+'ESA='+str(esa)+', Valid:' +str(valid[0])+str(valid[1])+str(valid[2])+str(valid[3])+str(valid[4])
        x = x2

    dpi=75
    if (args.dpi):
            dpi = args.dpi

    xMin = 0.0
    xMax = 140.0
    yMin = 0.8

    if (args.xMin):
            xMin = args.xMin
    if (args.xMax):
            xMax = args.xMax

    hist0, bin_edges0 = np.histogram(x, bins=bins, range=(xMin,xMax))
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
    plt.hist(x, bins=bins, facecolor = 'b', edgecolor='k', linewidth=0.5, range=(xMin,xMax))

    plt.title(plottitle+' Valid: '+str(valid[0])+str(valid[1])+str(valid[2])+str(valid[3])+str(valid[4]), fontsize=fontSize-14)
    plt.xlabel(xlabel)
    plt.ylabel('Counts')
    # plt.legend()

    n = len(hist0)
    if (delayCorr==0):
    #    plt.savefig("test")
    #    plt.savefig('TOF'+str(args.tof)+'.png', dpi=args.dpi)
        plt.savefig(args.outFile+'TOF'+str(args.tof)+'ESA'+str(esa)+'.png', dpi=args.dpi, facecolor='w', edgecolor='w', orientation='portrait', format=None, transparent=False, bbox_inches=None, pad_inches=0.1)
        np.savetxt(args.outFile+'TOF'+str(args.tof)+'ESA'+str(esa)+'.csv',np.c_[bin_edges0[0:n],bin_edges0[1:n+1], hist0],  delimiter = ',',header="binEdge0,binEdge1,histogram")
    else:
    #    plt.savefig("test2")
        plt.savefig(args.outFile+'TOF'+str(args.tof)+'s'+'ESA'+str(esa)+'.png', dpi=args.dpi, facecolor='w', edgecolor='w', orientation='portrait', format=None, transparent=False, bbox_inches=None, pad_inches=0.1)
        np.savetxt(args.outFile+'TOF'+str(args.tof)+'s'+'ESA'+str(esa)+'.csv',np.c_[bin_edges0[0:n],bin_edges0[1:n+1], hist0],  delimiter = ',',header="binEdge0,binEdge1,histogram")


