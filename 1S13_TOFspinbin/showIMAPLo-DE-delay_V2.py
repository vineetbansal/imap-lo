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
                        nargs="+",
                        dest='valid' )
    # set TOF0 valid flag to 2 to use all events
                        
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
                        
    parser.add_argument('-nf',
                        help='no filter',
                        type=int,
                        dest='nofilter')
                        
    parser.add_argument('-opt',
                        help='option ',
                        type=int,
                        dest='option')
    # -opt 2 for other formats 

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
        print("1S13 delay Failed total number of events = ", n, "esa = ", esa)
        continue

#    print("valid args:", args.valid)

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

    filter = 1
    filtername='+DblFlt'
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
            
    useEvent = np.linspace(0, 0, n)
    useSum = valid[0]*10000+1000*valid[1]+100*valid[2]+10*valid[3]+1*valid[4]
 #   print("useSum = ", useSum)
    for i in range(0,n):
    # tof 3 plut tof0 minues( tof1 plus tof2)
        validSum = ValidTOF0[i]*10000 + 1000*ValidTOF1[i] + 100*ValidTOF2[i] + 10*ValidTOF3[i]
        if (validSum == 11110):
            checksum = np.abs(TOF3[i] + TOF0[i] - ( TOF1[i] + TOF2[i] ))
    #        print("golden triple:",i,ValidTOF0[i],ValidTOF1[i],ValidTOF2[i],ValidTOF3[i])
        else:
            checksum = 10.0
            
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
            
        if (args.tmin):
            tof = ( valid[0] * TOF0[i] +  valid[1] * TOF1[i] + valid[2] * TOF2[i] )/(( valid[0] + valid[1] + valid[2] ) * 1.0 )
            if ( tof < args.tmin ):
                useEvent[i] = 0
        
        if (args.tmax):
            tof = ( valid[0] * TOF0[i] +  valid[1] * TOF1[i] + valid[2] * TOF2[i] )/(( valid[0] + valid[1] + valid[2] ) * 1.0 )
            if ( tof > args.tmax ):
                useEvent[i] = 0
        
    quad = np.linspace(10, 10, n)

    nValid3 = 0
    for i in range(0,n):
        if (ValidTOF3[i] == 1):
                nValid3 += 1
        
        if (useEvent[i] == 1):
            tof = TOF3[i]
            if ((tof >= TOF3_L[0]) and (tof <= TOF3_H[0])):
                quad[i] = 0
            elif ((tof > TOF3_L[1]) and (tof <= TOF3_H[1])):
                quad[i] = 1
            elif ((tof > TOF3_L[2]) and (tof <= TOF3_H[2])):
                quad[i] = 2
            elif ((tof > TOF3_L[3]) and (tof <= TOF3_H[3])):
                quad[i] = 3

    bins=20
    if (args.bins):
            bins = args.bins

    if (nValid3 < 3):
        print("1S13 delay Failed after valid selection with number of valid TOF3 = ", nValid3)
        continue 
    
    ind0 = np.where(quad==0)
    x0 = TOF3[ind0]
    hist0, bin_edges0 = np.histogram(x0,bins=bins,range=(TOF3_L[0],TOF3_H[0]))
    max = np.max(hist0)

    nb=bins


#    print(" Quad 0 ")
#    print(hist0)
#    print(bin_edges0)

    ind1 = np.where(quad==1)
    x1 = TOF3[ind1]
    bins1 = int(bins  * (TOF3_H[1] - TOF3_L[1]) / (TOF3_H[0] - TOF3_L[0]) +0.49)
    nb = nb + bins1
    hist1, bin_edges1 = np.histogram(x1,bins=bins1, range=(TOF3_L[1],TOF3_H[1]))

    max1 = np.max(hist1)
    max = np.max([max, max1])

    # print(" ")
    # print(" Quad 1 ")
    # print(hist1)
    # print(bin_edges1)

    ind2 = np.where(quad==2)
    x2 = TOF3[ind2]
    bins2 = int(bins  * (TOF3_H[2] - TOF3_L[2]) / (TOF3_H[0] - TOF3_L[0]) +0.49)
    nb = nb + bins2

    hist2, bin_edges2 = np.histogram(x2,bins=bins2,  range=(TOF3_L[2],TOF3_H[2]))

    max2 = np.max(hist2)
    max = np.max([max, max2])

    # print(" ")
    # print(" Quad 2 ")
    # print(hist2)
    # print(bin_edges2)

    ind3 = np.where(quad==3)
    x3 = TOF3[ind3]
    bins3 = int(bins  * (TOF3_H[3] - TOF3_L[3]) / (TOF3_H[0] - TOF3_L[0]) + 0.49)
    nb = nb + bins3

    hist3, bin_edges3 = np.histogram(x3,bins=bins3, range=(TOF3_L[3],TOF3_H[3]))

    max3 = np.max(hist3)
    max = np.max([max, max3])

    histAll0 = np.linspace(0.,0., nb)
    histAll1 = np.linspace(0.,0., nb)
    histAll2 = np.linspace(0.,0., nb)
    histAll3 = np.linspace(0.,0., nb)
    bin_edgesAll = np.linspace(0.,0., nb+1)

    histAll0[0:bins] = hist0[:]
    histAll1[bins:bins+bins1] = hist1[:]
    histAll2[bins+bins1:bins+bins1+bins2] = hist2[:]
    histAll3[bins+bins1+bins2:bins+bins1+bins2+bins3] = hist3[:]

    bin_edgesAll[0:bins]=bin_edges0[0:bins]
    bin_edgesAll[bins:bins+bins1]=bin_edges1[0:bins1]
    bin_edgesAll[bins+bins1:bins+bins1+bins2]=bin_edges2[0:bins2]
    bin_edgesAll[bins+bins1+bins2:bins+bins1+bins2+bins3+1]=bin_edges3[:]

    # print(" ")
    # print(" Quad 3 ")
    # print(hist3)
    # print(bin_edges3)

    dpi=75
    if (args.dpi):
            dpi = args.dpi

    xMin = 0.0
    xMax = 14.0
    yMin = 0.0
    yMax = 1.1*max

    if (args.xMin):
            xMin = args.xMin
    if (args.xMax):
            xMax = args.xMax

    if (args.yMin):
            yMin = args.yMin
    if (args.yMax):
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
    plt.hist(x0, bins=bins, facecolor = 'b', edgecolor='k', linewidth=0.5, label='Quad0', range=(TOF3_L[0],TOF3_H[0]))
    plt.hist(x1, bins=bins1, facecolor = 'r', edgecolor='k', linewidth=0.5, label='Quad1', range=(TOF3_L[1],TOF3_H[1]))
    plt.hist(x2, bins=bins2, facecolor = 'g', edgecolor='k', linewidth=0.5, label='Quad2', range=(TOF3_L[2],TOF3_H[2]))
    plt.hist(x3, bins=bins3, facecolor = 'y', edgecolor='k', linewidth=0.5, label='Quad3', range=(TOF3_L[3],TOF3_H[3]))
    ttl_note=str(valid[0])+str(valid[1])+str(valid[2])+str(valid[3])+str(valid[4])
    if (args.tmin):
        ttl_note=ttl_note+' tof'+str(valid[0])+str(valid[1])+str(valid[2])+' > '+str(args.tmin)
    if (args.tmax):
        ttl_note=ttl_note+' tof'+str(valid[0])+str(valid[1])+str(valid[2])+' < '+str(args.tmax)
    plt.title(plottitle+' Valid: '+ttl_note, fontsize=fontSize-14)
    plt.xlabel('TOF3 (ns) '+filtername+', Valid:' +str(valid[0])+str(valid[1])+str(valid[2])+str(valid[3])+str(valid[4]))
    plt.ylabel('Counts')
    plt.legend()
    plt.savefig(args.outFile+'ESA'+str(esa)+'.png', dpi=args.dpi, facecolor='w', edgecolor='w',
                orientation='portrait', format=None,
                transparent=False, bbox_inches=None, pad_inches=0.1)
                
    np.savetxt(args.outFile+'TOF'+str(3)+'ESA'+str(esa)+'.csv',np.c_[bin_edgesAll[0:nb],bin_edgesAll[1:nb+1], histAll0, histAll1, histAll2, histAll3 ],  delimiter = ',', header="binEdge0,binEdge1,quad0,quad1,quad2,quad3")
                
                

#plt.show()


#ddat



#plt.show()

