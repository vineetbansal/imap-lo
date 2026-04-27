#!/usr/bin/python
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
# from matplotlib import pyplot as plt
import argparse
from scipy import optimize
import matplotlib.colors as colors
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
                            help='the GSEOS event file list',
                           dest='file',
                           required=True)

    parser.add_argument('-o', '--output',
                        help='the plot output',
                        dest='outFile',
                        required=True)
                        
                        
    parser.add_argument('-t', '--tof',
                        help='tof 0,1, or 2',
                        dest='tof',
                        type=int,
                        required=True)
                                
    parser.add_argument('-vTrp', '--validTriple',
                        help='valid flags for TOF0, TOF1, TOF2, TOF3, checksum',
                        nargs="+",
                        dest='validTrp' )
                        
    parser.add_argument('-vDbl', '--validDouble',
                        help='valid flags for TOF0, TOF1, TOF2, TOF3, checksum',
                        nargs="+",
                        dest='validDbl' )

    parser.add_argument('-b', '--bins',
                        help='the number of bins for histograms',
                        dest='bins',
                        type=int)
                        
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
                        
    parser.add_argument('-plottitle',
                        help='plottitle',
                        dest='plottitle')
                        
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
                        
    parser.add_argument('-opt',
                        help='option ',
                        type=int,
                        dest='option')
    # -opt 1 for instrument files
                        
#    parser.add_argument('-m', '--mcp',
#                        help='range for MCP',
#                        nargs="+",
#                        dest='mcp',
#                        required=True )
#
#    parser.add_argument('-p', '--pac',
#                        help='range for PAC',
#                        nargs="+",
#                        dest='pac',
#                        required=True )

    return parser.parse_args()

#



def bin_TOF(T0, T1, T2, T3, ValTOF0, ValTOF1, ValTOF2, ValTOF3, bins, minTOF, maxTOF, selectTOF, filter, valid ):
#  valid = [1,0,0,0,0]
#  TOF0, TOF1, TOF2, TOF3, checksum
#
# if filter = 1, then we apply added filter to remove electrons
#      this essentially makes doubles from singles
#
# selectTOF is 0, 1, 2, or 3 depending on the TOF to select

    n1 = len(T0)
    
    TOF0_filter = np.linspace(0, 0, n1)
    TOF1_filter = np.linspace(0, 0, n1)
    TOF2_filter = np.linspace(0, 0, n1)
    
    VTOF0_filter = np.linspace(0, 0, n1)
    VTOF1_filter = np.linspace(0, 0, n1)
    VTOF2_filter = np.linspace(0, 0, n1)
    
    TOF0_filter = T0
    TOF1_filter = T1
    TOF2_filter = T2
    VTOF0_filter = ValTOF0
    VTOF1_filter = ValTOF1
    VTOF2_filter = ValTOF2
    
    useEve = np.linspace(0, 0, n1)

    for i in range(0,n1):
    
#        print(i, T0[i],ValTOF1[i],ValTOF2[i])
        if (filter == 1):
            if ((ValTOF0[i] > 0) and ((ValTOF1[i] == 0 ) and (ValTOF2[i] == 0 ))):
                VTOF0_filter[i]=0
    
            if ((ValTOF1[i] > 0) and ((ValTOF0[i] == 0 ) and (ValTOF2[i] == 0 ))):
                VTOF1_filter[i]=0
                
            if ((ValTOF2[i] > 0) and ((ValTOF0[i] == 0 ) and (ValTOF1[i] == 0 ))):
                VTOF2_filter[i]=0
        
    useSum = valid[0]*10000+1000*valid[1]+100*valid[2]+10*valid[3]+1*valid[4]

    
    for i in range(0,n1):
# tof 3 plut tof0 minues( tof1 plus tof2)

        validSum = ValTOF0[i]*10000 + ValTOF1[i]*1000 + ValTOF2[i]*100 + ValTOF3[i]*10
        if (validSum == 11110):
            checksum = np.abs(T3[i] + T0[i] - ( T1[i] + T2[i] ))
        else:
            checksum = 10.0
        
        validChecksum = 0
        if ((checksum < checksum_lim[0]) and (T3[i] <= 20.0)):
            validChecksum = 1
        
        useCheck = VTOF0_filter[i]*10000 + \
                VTOF1_filter[i]*1000 + \
                VTOF2_filter[i]*100 + \
                ValTOF3[i]*10 + \
                validChecksum*1
            
        if (useCheck == useSum):
            useEve[i] = 1
            
    ind = np.where(useEve==1)
    
    x0 = TOF0_filter[ind]
    x1 = TOF1_filter[ind]
    
    x2 = T2[ind]
    x3 = T3[ind]
    
    if (selectTOF == 0):
        x = x0
    if (selectTOF == 1):
        x = x1
    if (selectTOF == 2):
        x = x2
    
    hist, bin_edges = np.histogram(x, bins=bins, range=(minTOF,maxTOF))
    
    return hist, bin_edges
    
def valid_TOF(T0, T1, T2, T3, ValTOF0, ValTOF1, ValTOF2, ValTOF3, valid, n ):

    useEvent = np.linspace(0, 0, n)
    useSum = valid[0]*10000+1000*valid[1]+100*valid[2]+10*valid[3]+1*valid[4]
    print("useSum = ", useSum)
    for i in range(0,n):
# tof 3 plut tof0 minues( tof1 plus tof2)
        validSum = ValTOF0[i]*10000 + 1000*ValTOF1[i] + 100*ValTOF2[i] + 10*ValTOF3[i]
        if (validSum == 11110):
            checksum = np.abs(T3[i] + T0[i] - ( T1[i] + T2[i] ))
        else:
            checksum = 10.0
        
        validChecksum = 0
        if ((checksum < checksum_lim[0]) and (T3[i] < 20)):
            validChecksum = 1

        useCheck = ValTOF0[i]*10000 + \
            ValTOF1[i]*1000 + \
            ValTOF2[i]*100 + \
            ValTOF3[i]*10 + \
            validChecksum*1
            
        if (useCheck == useSum):
            useEvent[i] = 1

    return useEvent

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
    print("number of events = ", n)

    print("valid args Dbl:", args.validDbl)
    print("valid args Trp:", args.validTrp)

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

    # valid 4 is the checksum
    validDbl = [0,0,0,0,0]
    if (args.validDbl ):
        if (args.validDbl[0] =='1'):
            validDbl[0] = 1
        if (args.validDbl[1] =='1'):
            validDbl[1] = 1
        if (args.validDbl[2] =='1'):
            validDbl[2] = 1
        if (args.validDbl[3] =='1'):
            validDbl[3] = 1
        if (args.validDbl[4] =='1'):
            validDbl[4] = 1

    # valid 4 is the checksum
    validTrp = [0,0,0,0,0]
    if (args.validTrp ):
        if (args.validTrp[0] =='1'):
            validTrp[0] = 1
        if (args.validTrp[1] =='1'):
            validTrp[1] = 1
        if (args.validTrp[2] =='1'):
            validTrp[2] = 1
        if (args.validTrp[3] =='1'):
            validTrp[3] = 1
        if (args.validTrp[4] =='1'):
            validTrp[4] = 1
    
    useEventDbl = valid_TOF(TOF0, TOF1, TOF2, TOF3, ValidTOF0, ValidTOF1, ValidTOF2, ValidTOF3, validDbl, n )
    useEventTrp = valid_TOF(TOF0, TOF1, TOF2, TOF3, ValidTOF0, ValidTOF1, ValidTOF2, ValidTOF3, validTrp, n )

    bins=20
    if (args.bins):
            bins = args.bins

    indDbl0 = np.where(useEventDbl==1)
    xDbl0 = TOF0[indDbl0]
    xDbl1 = TOF1[indDbl0]
    xDbl2 = TOF2[indDbl0]
    xDbl3 = TOF3[indDbl0]

    indTrp0 = np.where(useEventTrp==1)
    xTrp0 = TOF0[indTrp0]
    xTrp1 = TOF1[indTrp0]
    xTrp2 = TOF2[indTrp0]
    xTrp3 = TOF3[indTrp0]

    if (args.tof ==0):
        xlabel = 'TOF0 (ns) '
        xDbl = xDbl0
        xTrp = xTrp0
    if (args.tof ==1):
        xlabel = 'TOF1 (ns) '
        xDbl = xDbl1
        xTrp = xTrp1
    if (args.tof ==2):
        xlabel = 'TOF2 (ns) '
        xDbl = xDbl2
        xTrp = xTrp2
    xlabel=xlabel+ ' ESA = '+str(esa) + ' VDbl:'+str(validDbl[0])+str(validDbl[1])+str(validDbl[2])+str(validDbl[3])+str(validDbl[4])+ ' VTrp:'+str(validTrp[0])+str(validTrp[1])+str(validTrp[2])+str(validTrp[3])+str(validTrp[4])

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
            
            
    histDbl0, bin_edgesDbl0 = np.histogram(xDbl, bins=bins, range=(xMin,xMax))
    histTrp0, bin_edgesTrp0 = np.histogram(xTrp, bins=bins, range=(xMin,xMax))

    max0 = np.max(histDbl0)
    yMax = 1.1*max0

    if (args.yMin):
            yMin = args.yMin
    if (args.yMax):
            yMax = args.yMax

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

    ylabel = 'Counts'

    #ax.set_yscale('log')
    ax.set_yscale('log')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True)
    ax.set_axisbelow(True)  # This line added.

    ax.axis([xMin,xMax,yMin,yMax])

    if (args.label):
        nn = len(args.label)
        for ii in range(0,nn):
            ax.annotate(args.label[ii], xy=(args.xlabel[ii], args.ylabel[ii]),  xytext=(args.xlabel[ii], args.ylabel[ii]),color=plt.cm.cool(args.color[ii]))
            
            
    plottitle=args.outFile[-100:]
    if (args.plottitle):
            plottitle=ags.plottitle

    # histDbl0, bin_edgesDbl0
    n2 = len(bin_edgesDbl0)
    x2 = np.linspace(0.0,0.0,n2)
    x2[:] = bin_edgesDbl0[:]
        
    yhist2 = np.linspace(0.0,0.0,n2)
    yhist2[0]=histDbl0[0]
    yhist2[1:n2]=histDbl0[:]

    n3 = len(bin_edgesTrp0)
    x3 = np.linspace(0.0,0.0,n3)
    x3[:] = bin_edgesTrp0[:]
        
    yhist3 = np.linspace(0.0,0.0,n3)
    yhist3[0]=histTrp0[0]
    yhist3[1:n2]=histTrp0[:]

    plt.step(x2,yhist2,label='Double Counts',color='k',alpha=0.8, linewidth=2)
    plt.fill_between(x3,yhist3,label='Triple Counts',color='b', step="pre",alpha=0.6)

    if (args.tof ==0):
        plt.axvline(x=20, color='y',linestyle='--',linewidth=3)
    if (args.tof ==1):
        plt.axvline(x=10, color='y',linestyle='--',linewidth=3)
    if (args.tof ==2):
        plt.axvline(x=10, color='y',linestyle='--',linewidth=3)

    plt.title(plottitle+' ValidDbl: '+str(validDbl[0])+str(validDbl[1])+str(validDbl[2])+str(validDbl[3])+str(validDbl[4])+' ValidTrp: '+str(validTrp[0])+str(validTrp[1])+str(validTrp[2])+str(validTrp[3])+str(validTrp[4]), fontsize=fontSize-14)
    plt.xlabel(xlabel)
    plt.ylabel('Counts')
    plt.legend()

    plt.savefig(args.outFile+'ESA'+str(esa)+'TOF'+str(args.tof)+'.png', dpi=args.dpi, facecolor='w', edgecolor='w',
                orientation='portrait', format=None, transparent=False, bbox_inches=None, pad_inches=0.1)



