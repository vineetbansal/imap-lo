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

    parser.add_argument('-opt',
                        help='option ',
                        type=int,
                        dest='option')
    # -opt 1 for instrument files

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
        print("1S13 2DTOF Failed total number of events = ", n, "esa = ", esa)
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

 #   print("valid args:", args.valid)

# for i in range(0,n):
#    if ((ValidTOF0[i] > 0) and ((ValidTOF1[i] == 0 ) and (ValidTOF2[i] == 0 ))):
#        TOF0[i]=-5.0
#        ValidTOF0[i]=0

#    if ((ValidTOF1[i] > 0) and ((ValidTOF0[i] == 0 ) and (ValidTOF2[i] == 0 ))):
#        TOF1[i]=-5.0
#        ValidTOF1[i]=0
        
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
  #  print("useSum = ", useSum)
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

  #  print("number of valid TOF3 = ", nValid3)

    ind0 = np.where(useEvent==1)
    x0 = TOF0[ind0]
    x1 = TOF1[ind0]
    x2 = TOF2[ind0]
    x3 = TOF3[ind0]
    ncheck = len(x0) + len(x1) + len(x2) 
    if (ncheck < 3): 
        print("1S13 2DTOF Failed number of events after valid selection = ", ncheck, "esa = ", esa)
        continue
         


    if (args.tofx ==0):
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

    dpi=75
    if (args.dpi):
        dpi = args.dpi

    xMin = 1.0
    xMax = 200.0
    yMin = 1.0
    yMax = 200.0

    # hist0, bin_edges0 = np.histogram(x,bins=bins)
    # max0 = np.max(hist0)

    if (args.xMin):
            xMin = args.xMin
    if (args.xMax):
            xMax = args.xMax

    if (args.yMin):
            yMin = args.yMin
    if (args.yMax):
            yMax = args.yMax

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

    plt.title(plottitle+' Valid: '+str(valid[0])+str(valid[1])+str(valid[2])+str(valid[3])+str(valid[4]), fontsize=fontSize-14)
    plt.xlim(xMin,xMax)
    plt.ylim(yMin,yMax)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    # plt.legend()
    if (delayCorr==0):
        plt.savefig(args.outFile+'ESA'+str(esa)+'TOF'+str(args.tofx)+'vs'+str(args.tofy)+'.png', dpi=args.dpi, facecolor='w', edgecolor='w', orientation='portrait',format=None, transparent=False, bbox_inches=None, pad_inches=0.1)
    else:
        plt.savefig(args.outFile+'ESA'+str(esa)+'TOF'+str(args.tofx)+'s-vs-'+str(args.tofy)+'s.png', dpi=args.dpi, facecolor='w', edgecolor='w', orientation='portrait',format=None, transparent=False, bbox_inches=None, pad_inches=0.1)
    #plt.show()


#ddat



#plt.show()

