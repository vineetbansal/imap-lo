# May 18, 2023 - NAS
# in Version 2 we are adding the TOF3 < 20 ns criterion
#!/usr/bin/python
from spacepy.pycdf import CDF
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import argparse
import random
import os
from datetime import datetime, timedelta
from spacepy import pycdf
import pandas as pd

## constants
# bla = 10.0
PI = np.pi

double_to_triple = 10.0

# ESA Steps
nesa = 7

# profile for geometric factors
energies_hires = np.linspace(1.,1.,nesa)
energies_hires[:] = [16.35,30.56, 56.42, 105.21, 199.79, 407.49, 795.28]

energies_hithr = np.linspace(1.,1.,nesa)
energies_hithr[:] = [17.13, 32.02, 59.24, 113.03, 215.97, 439.82, 855.43]

energies_o_hires = np.linspace(1.,1.,nesa)
energies_o_hires[:] = [16.35,30.56, 56.42, 105.21, 199.79, 407.49, 795.28]
energies_o_hires = 1.01*energies_o_hires

survprob_hires = np.linspace(1.,1.,nesa)
survprob_hires[:] = [0.014674943,0.094340378,0.225305786,0.370788292,0.506098836,0.627079186,0.712499202]
survprob_hires_pole = np.linspace(1.,1.,nesa)
survprob_hires_pole[:] = [0.141009407,0.238042661, 0.34635036, 0.457261629, 0.561802854, 0.659298414, 0.731303948]

energies_hithr = np.linspace(1.,1.,nesa)
energies_hithr[:] = [17.13, 32.02, 59.24, 113.03, 215.97, 439.82, 855.43]

energies_o_hithr = np.linspace(1.,1.,nesa)
energies_o_hithr[:] = [16.35,30.56, 56.42, 105.21, 199.79, 407.49, 795.28]
energies_o_hithr = 1.01*energies_o_hires

survprob_hithr = np.linspace(1.,1.,nesa)
survprob_hithr[:] = [0.017992045,0.102998543,0.23670427, 0.386954276, 0.520900983,0.638133007, 0.720372178]
survprob_hithr_pole = np.linspace(1.,1.,nesa)
survprob_hithr_pole[:] = [0.14749437, 0.245987183, 0.35515275, 0.469585453, 0.573489784, 0.66845414, 0.738094243]

geo_hires =np.linspace(1.,1.,nesa)
geo_hires[:] = [9.09E-05, 1.01E-04, 1.13E-04, 1.29E-04, 1.59E-04, 2.05E-04, 2.55E-04]

# Fatemeh: need proxies for O geofactor here
geo_o_hires =np.linspace(1.,1.,nesa)
geo_o_hires[:] = [9.09E-05, 1.01E-04, 1.13E-04, 1.29E-04, 1.59E-04, 2.05E-04, 2.55E-04]
geo_o_hires = 3.0*geo_o_hires

geo_hithr =np.linspace(1.,1.,nesa)
geo_hithr[:] = [2.08E-04, 2.33E-04, 2.69E-04, 3.17E-04, 3.91E-04, 4.93E-04, 6.43E-04]
geo_hithr = 2.0* geo_hithr

# Fatemeh: need proxies for O geofactor here
geo_o_hithr =np.linspace(1.,1.,nesa)
geo_o_hithr[:] = [9.09E-05, 1.01E-04, 1.13E-04, 1.29E-04, 1.59E-04, 2.05E-04, 2.55E-04]
geo_o_hithr = 1.5* geo_o_hithr

hflux =np.linspace(1.,1.,nesa)
hflux[:] = [ 18000.,10000.,6000.0,5000.,2000., 400.,200.]

hrates_hires =np.linspace(1.,1.,nesa)
hrates_hires[:] = hflux * geo_hires * energies_hires

hrates_hithr =np.linspace(1.,1.,nesa)
hrates_hithr[:] = hflux * geo_hithr * energies_hithr

brates_hires =np.linspace(1.,1.,nesa)
brates_hires[:] = 0.1*brates_hires[:]

bunrat_hires =np.linspace(1.,1.,nesa)
bunrat_hires[:] = 0.01*bunrat_hires[:]

bflux_hires =np.linspace(1.,1.,nesa)
bflux_hires[:] =  brates_hires[:] / (geo_hires * energies_hires)

brates_hithr =np.linspace(1.,1.,nesa)
brates_hithr[:] = 0.2*brates_hithr[:]

bunrat_hithr =np.linspace(1.,1.,nesa)
bunrat_hithr[:] = 0.02*bunrat_hithr[:]

bflux_hithr =np.linspace(1.,1.,nesa)
bflux_hithr[:] =  brates_hithr[:] / (geo_hithr * energies_hithr)

oflux =np.linspace(1.,1.,nesa)
oflux[:] = [ 10.,10.,10.,10.,1000.0, 100.0,10.]

# note using proxy for o-geo factor here
orates_hires =np.linspace(1.,1.,nesa)
orates_hires[:] = oflux * geo_hires * energies_hires

orates_hithr =np.linspace(1.,1.,nesa)
orates_hithr[:] = oflux * geo_hithr * energies_hithr

brates_o_hires =np.linspace(1.,1.,nesa)
brates_o_hires[:] = 0.01*brates_o_hires[:]

bunrat_o_hires =np.linspace(1.,1.,nesa)
bunrat_o_hires[:] = 0.001*bunrat_o_hires[:]

brates_o_hithr =np.linspace(1.,1.,nesa)
brates_o_hithr[:] = 0.02*brates_o_hires[:]

bunrat_o_hithr =np.linspace(1.,1.,nesa)
bunrat_o_hithr[:] = 0.002*bunrat_o_hithr[:]

triple_rates_hires = np.linspace(1.,1.,nesa)
triple_rates_hires[:]= 1.5*(hrates_hires + orates_hires )

triple_rates_hithr = np.linspace(1.,1.,nesa)
triple_rates_hithr[:] = 1.5*(hrates_hithr + orates_hithr )

double_rates_hires = np.linspace(1.,1.,nesa)
double_rates_hires[:]= double_to_triple*triple_rates_hires

double_rates_hithr = np.linspace(1.,1.,nesa)
double_rates_hithr[:]= double_to_triple*triple_rates_hithr

# gauss sigma
sigma = np.linspace(1.,1.,nesa)
sigma[:] = 2.0*sigma[:]

# NEP North Ecliptic Pole in RA DEC coords here
#ibex_rotate -r 1. -d 90.0  -f J2000 -F ECLIPJ2000 -t 2025/03:20:17:26:57
#+270.000000 +66.560709
# NEP pole in RA and Dec J2000
ra_nep = 270.0*PI/180.
dec_nep = 66.560709*PI/180.0
theta_nep = 0.5*PI - dec_nep

znep = np.cos(theta_nep)
xnep = np.sin(theta_nep)*np.cos(ra_nep)
ynep = np.sin(theta_nep)*np.sin(ra_nep)

vec_nep =np.array([xnep, ynep, znep])

LN10 = 2.3026
AMP = 0.024
SLOPE = -0.4

M1 = -1.118
M0 = 4.0052
    
N1 = -0.75182
N0 = 8.1272
    
SLOPE2 = 0.75629375
    
zero = -0.06
    
nbin = 720

offset = - 12.0*2.0*PI/(15.0*1000)
# in principle the star sensor is shifted by 12 ms

# offset = -1.5*PI/180.0
# offset = -3.0*PI/180.0

def doy_fraction(t):
    start = datetime(t.year, 1, 1)
    return (t - start).total_seconds() / 86400.0 + 1 

def plot_results(args,  sts_best, outname):

    bin0 =args.bin[0]
    bin1 =args.bin[1]
    nbin1 = bin1-bin0
    x = np.linspace(0.,0.,nbin1)
    yd = np.linspace(0.,0.,nbin1)
    ym = np.linspace(0.,0.,nbin1)
    
    # print(nbin1)
    
  #  yd[:] = stsdata_ave[bin0:bin1]
    ym[:] = sts_best[bin0:bin1]
    
    for i in range(0,nbin1):
        j = i + bin0
        x[i]= (j+0.5)*360.0/(nbin*1.0)
    
    dpi=75
    if (args.dpi):
        dpi = args.dpi

    xMin = bin0*360.0/(1.0*nbin)
    xMax = bin1*360.0/(1.0*nbin)
    yMin = 0.0
    yMax = np.max(ym*1000)

    if (args.xMin):
        xMin = args.xMin
    if (args.xMax):
        xMax = args.xMax

    if (args.yMin):
        yMin = args.yMin
    if (args.yMax):
        yMax = args.yMax

    ylabel='Star Sensor (mV)'
    xlabel = 'Spinphase (deg)'

    fontSize = 22
    font = {'weight':'bold',   'size':fontSize}
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
#    ax.set_yscale('log')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    ax.axis([xMin,xMax,yMin,yMax])

    if (args.label):
        nn = len(args.label)
        for ii in range(0,nn):
            ax.annotate(args.label[ii], xy=(args.xlabel[ii], args.ylabel[ii]),  xytext=(args.xlabel[ii], args.ylabel[ii]),color=plt.cm.cool(args.color[ii]))

#    plottitle=args.filests
#    if (args.plottitle):
#        plottitle=ags.plottitle

# plt.style.use('seaborn-whitegrid') # nice and clean grid
# plt.bar(bin_edges0, hist0)
 #   plt.plot(x, yd, color = 'b', linewidth=1.)
    plt.plot(x, ym*1000, color = 'g',  linewidth=1.)

#    front = str(int(phase))
#    resid = np.abs(phase - int(phase))*10000
#    end = str(int(resid))

#    phaseString = front + '+' + end + '/10,000'
#    plt.title(plottitle+' phase ='+phaseString, fontsize=fontSize-14)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
# plt.legend()

    plt.savefig(outname+'.png', dpi=args.dpi, facecolor='w', edgecolor='w', orientation='portrait', format=None, transparent=False, bbox_inches=None, pad_inches=0.1)



def print_sts(sts_set,outname,s0,s1):

    nspin = s1 - s0 + 1
    outfile = outname+'.csv'
        
    f=open(outfile, 'w')
        
    for i in range(s0,s1):
        f.write(f"{i},")
    f.write(f"{s1} \n")

    for j in range(0,720):
        for i in range(0,nspin):
            kk = 720 * i + j
            if (i < nspin - 1 ):
                f.write(f"{sts_set[kk]},")
            else:
                f.write(f"{sts_set[kk]} \n")
    
    f.close()
        
def print_sts_ave(sts_set,outname,s0,s1):

    nspin = s1 - s0 + 1
    outfile = outname+'_ave.csv'
        
    f=open(outfile, 'w')
        
    for j in range(0,720):
        sum = 0.0
        nsum = 0
        for i in range(0,nspin):
#            ir = int(2*random.random()-1)*2
            ir = 0
            kk = 720 * i + j + ir
            if (kk > 720*nspin-1):
                kk = 720*nspin-1
            if (kk < 0):
                kk = 0
            sum = sum + sts_set[kk]
            nsum = nsum + 1
        ave = sum/ (1. * nsum)
        f.write(f"{ave} \n")
            
    f.close()

def sts_ave(sts_set,mspin):

    sts_ave_arr = np.linspace(0.,0.,nbin)
        
    for j in range(0,nbin):
        sum = 0.0
        nsum = 0
        for i in range(0,mspin):
            kk = 720 * i + j
            sum = sum + sts_set[kk]
            nsum = nsum + 1
        ave = sum/ (1. * nsum)
        sts_ave_arr[j] = ave
        
    return sts_ave_arr

def print_stsdata_ave(sts,outname,s0,s1, sin):

    nspin = s1 - s0 + 1
    outfile = outname+'_ave.csv'
    
    i0 = int(s0/sin)
    i1 = int(s1/sin)
        
    f=open(outfile, 'w')
    
    stsdata_ave = np.linspace(0.,0.,nbin)
    stsdata_ang = np.linspace(0.,0.,nbin)
    
    for j in range(0,nbin):
        sum = 0.0
        nsum = 0
        for i in range(i0,i1+1):
            sum = sum + sts[i,j]
            nsum = nsum + 1
        ave = sum/ (1. * nsum)
        ang = (j+0.5)*360.0/(nbin*1.0)
        stsdata_ave[j] = ave
        stsdata_ang[j] = ang
        
        f.write(f"{ang}, {ave} \n")
            
    f.close()
    return stsdata_ang, stsdata_ave


def print_results(stsdata_ave, sts_best, phase, outname):

    outfile = outname+'.csv'

    f=open(outfile, 'w')
    f.write(f"# ang,  sts_data_ave, sts_model, phase = {phase} \n" )
    for j in range(0,nbin):
        ave_data = stsdata_ave[j]
        best = sts_best[j]
        ang = (j+0.5)*360.0/(nbin*1.0)
        
        f.write(f"{ang}, {ave_data}, {best} \n")
            
    f.close()
    
    
def print_star_results(star_ave, outname):

    outfile = outname+'.csv'

    f=open(outfile, 'w')
    f.write(f"# ang, sts_model \n" )
    for j in range(0,nbin):
        ave_data = star_ave[j]
        ang = (j+0.5)*360.0/(nbin*1.0)
        
        f.write(f"{ang}, {ave_data} \n")
            
    f.close()


def count(cntfr):

    cnt = int(cntfr)
    fr = cntfr - 1.0*cnt
    rando = random.random()
    if (fr > rando):
       cnt += 1
       
    return cnt
    
def parse_stars(args):
# this function reads config files with ncol
# this reads the thing that Janzen sent

    dtype = [("name", "S"), ("ra", float), ("dec", float), ("mag", float)]
    lines = np.loadtxt(args.filestars, delimiter=',', unpack=True, skiprows=1, usecols=range(1, 4))
    
 #   name_st = lines[0,:]
    ra_st = lines[0,:]
    dec_st = lines[1,:]
    mag_st = lines[2,:]

    return ra_st, dec_st, mag_st
    
    
def parse_stars_tyc(args):
# this function reads config files with ncol
# this reads the thing that Janzen sent

#    dtype = [("name", "S"), ("ra", float), ("dec", float), ("mag", float)]
#    lines = np.loadtxt(args.filestars, delimiter=',', unpack=True, skiprows=1, usecols=(1,2,5,6))
    s_dtype={'names': ('star', 'ra', 'dec','ec_ra', 'ec_dec','bt','vt'), 'formats': ('S10','f8','f8','f8','f8','f8','f8')}
    
    lines = np.loadtxt(args.filestars, delimiter=',', usecols=(1,2,5,6), unpack=True, skiprows=1)
    
 #   name_st = lines[0,:]
    ra_st = lines[0,:]
    dec_st = lines[1,:]
    # mag_st = lines[2,:] # right now bt
    mag_st = lines[3,:] # right now vt
    print("stars = ",ra_st, dec_st, mag_st)


    return ra_st, dec_st, mag_st


def parse_sts(args):
# this function reads config files with ncol

    sts = np.loadtxt(args.filests,  unpack=True, dtype='float', comments='#')
    
   # sts[0,:] is the sts in the first spin

    return sts

def coords(args, phaseadjust):
    # phaseadjust (in rad) shifts the reference direction for the spin-pulse forward or back
    #   the star tracker fails to converge or gets blinded and loses sight of its phase. the spin-pulse gets issued at some adjust phase
    
    offang1 = args.randang*(random.random() - 0.5)
    offang2 = args.randang*(random.random() - 0.5)
    
    ra = args.spinvector[0]*PI/180.0 + offang1*PI/180.0
    dec = args.spinvector[1]*PI/180.0 + offang2*PI/180.0
    theta = 0.5*PI - dec
    
    zspin = np.cos(theta)
    xspin = np.sin(theta)*np.cos(ra)
    yspin = np.sin(theta)*np.sin(ra)

    vec_spin =np.array([xspin, yspin, zspin])
    
    vec_ec = np.cross(vec_spin, vec_nep)
    
    vec_nep1 = np.cross(vec_ec, vec_spin)
    
    # vec_nep1 and vec_ec contains the spin_pulse

    vec_pulse = np.add( (np.cos(offset+phaseadjust)*vec_nep1), (np.sin(offset+phaseadjust)*vec_ec ))
    vec_ec1 = np.cross(vec_spin, vec_pulse)
    
    return vec_spin, vec_pulse, vec_ec1
    
#    np.add(vector1, vector2)      # vector addition
#    np.cross(vector1, vector2)    # cross product
#    np.inner(vector1, vector2)
    
    
def star_angles(args, ra_st1, dec_st1, phaseadjust):
    # the spin, nep, and ec vectors make a right handed system
    # nep x ec = spin
    # ec = spin x nep
    # rotation in right-handed manner about spin direction

    ra  = ra_st1 * PI/180.0
    dec = dec_st1 *PI/180.0
    theta = 0.5*PI - dec

    zst = np.cos(theta)
    xst = np.sin(theta)*np.cos(ra)
    yst = np.sin(theta)*np.sin(ra)
    
    vec_st = np.array([xst, yst, zst])
    
    vec_spin, vec_pulse, vec_ec1 = coords(args,  phaseadjust)
    
    dot = np.inner(vec_st, vec_spin)
    
    angle_to_spin = np.arccos(dot) * 180.0/PI
    if (angle_to_spin < 0.0): angle_to_spin = angle_to_spin + 360.0
    
    # xst_nep is the projection of the star to pulse direction
    xst_nep = np.inner(vec_st, vec_pulse)
    # yst_nep is to projection of the star to the EC plane
    yst_ec = np.inner(vec_st, vec_ec1)
    
    phase_angle = np.arctan2(yst_ec, xst_nep) * 180.0/PI
    # Note the phase-angle is to the NEP, and doesn't add in that extra 3.0 offset
    
    return angle_to_spin, phase_angle
    
def star_spin(args, ra_st, dec_st, mag_st, phaseadjust, pivotAng):
    # this takes in the various vectors and produces a 720 array with the predicted star sensor values

    nst = len(ra_st)
    
    sts_spin = np.linspace(0.,0.,nbin)
    
    for i in range(0,nst):

            ra = ra_st[i]
            dec = dec_st[i]

            angle_to_spin, phase_angle = star_angles(args, ra, dec, phaseadjust)
            elevation =  angle_to_spin - pivotAng 
            
            if (np.abs(elevation) < 7.0):
            
                mag = mag_st[i]

                # sts_mag = np.exp(mag * M1)*M0 * args.norm
                # now using the cal results from IBEX
                sts_mag = args.norm * np.exp( LN10 * (AMP + SLOPE*mag))

                width = N0 +  N1 * elevation
                
                line0 = phase_angle - (0.5 * width)
                if (line0 < 0.0): line0 += 360.0
                line1 = phase_angle + (0.5 * width)
                if (line1 < 0.0): line1 += 360.0

                
                
                for j in range(0,nbin):

                    # offang3 = 2*args.randang*(random.random() - 0.5)
                    offang3 = 0.0

                    phase =  (j+0.5) * 360.0 / (nbin * 1.0) + offang3
                    if (phase < 0.0): phase += 360.0
                
                    term0 = 0.5-0.5*np.abs(phase - line0)*SLOPE2
                    tern0 = term0 + np.abs(term0)
                    term1 = 0.5-0.5*np.abs(phase - line1)*SLOPE2
                    tern1 = term1 + np.abs(term1)
                
                    signal = sts_mag * (tern0 + tern1)
                    
                    # signal = sts_mag
                    
                    if (signal < -1.0):
                        print("uho: ", signal, tern0, tern1, term0, term1)
                    
                    sts_spin[j] = sts_spin[j] + signal
                    # print(j, sts_spin[j], signal)
                
 #   for j in range(0,nbin):
 #       sts_spin[j] = sts_spin[j]
                
    return sts_spin


def argParsing():

    parser = argparse.ArgumentParser(description='This tool accepts a GSEOS filename and makes cool plots for IMAP-Lo.')
    
    parser.add_argument('-o', '--ostring',
                        help='output string for the pointing',
                        dest='outstring',
                        required=True)
                        
    parser.add_argument('-f', '--file',
                        help='file for the star catalog',
                        dest='filestars',
                        required=True)
    
    parser.add_argument('-s', '--starfilepath',
                        required=True,
                        dest='starfile',
                        help='level 1b prostar')
    
    parser.add_argument('-p', '--scposition',
                        required=True,
                        dest='position',
                        help='SC position file (includes spin angle)')
        
    parser.add_argument('-g', '--gtcontext',
                        required=True,
                        dest='context',
                        help='good time context file, includes ppm angle')
                        
    parser.add_argument('-m', '--mspin',
                        help='number of spins to model',
                        dest='msp',
                        type=int,
                        required=True)
                        
    parser.add_argument('-b', '--binrange',
                        help='bins for autocorrelation',
                        dest='bin',
                        nargs="+",
                        type=int,
                        default=[0,719])

    parser.add_argument('-n', '--norm',
                        help='norm for star sensor values',
                        dest='norm',
                        type=float,
                        required=True)
                        
    parser.add_argument('-r', '--randoang',
                        help='random angle in deg',
                        dest='randang',
                        type=float,
                        required=True)
    
    parser.add_argument('-vs', '--vector_spin',
                        help='RA, DEC [deg] for the spin direction',
                        dest='spinvector',
                        nargs="+",
                        type=float,
                        default=[0.0, 0.0])
                        
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

# Note that pivot angle is from the spin axis 0 - 180.0
                           
                        
    return parser.parse_args()

#
# define bin distribution


## main

args = argParsing()

file = args.starfile

cdf = CDF(file)
epoch = cdf['epoch'][:]
yr1  = epoch[0].year
doy1 = int(doy_fraction(epoch[0]) )
sdoy1 = f"{doy1:03d}"
date1 = f"{yr1}{sdoy1}"

# read the position / spin data

df = pd.read_csv(
    args.position,   # path to your file
    skipinitialspace=True  # removes spaces after commas
)

# --- ensure datetime column exists ---

df["date_dt"] = pd.to_datetime(df["date"].astype(str), format="%Y%j")

target_dt = datetime.strptime(date1, "%Y%j")
# ensure pandas Timestamp
target_dt = pd.Timestamp(target_dt)

# --- find closest row (as before) ---
idx = (df["date_dt"] - target_dt).abs().idxmin()
row = df.loc[idx]

# --- find nearest earlier neighbor ---
earlier = df[df["date_dt"] < row["date_dt"]]

if len(earlier) == 0:
    raise ValueError("No earlier neighbor available")

idx_prev = (earlier["date_dt"] - row["date_dt"]).abs().idxmin()
row_prev = earlier.loc[idx_prev]

# --- time difference in days ---
dt_days = (row["date_dt"] - row_prev["date_dt"]).total_seconds() / 86400.0

# --- gradients (deg/day) ---
grad_lon = (row["spin_lon_eq"] - row_prev["spin_lon_eq"]) / dt_days
grad_lat = (row["spin_lat_eq"] - row_prev["spin_lat_eq"]) / dt_days

# --- project to target ---
dt_target = (target_dt - row["date_dt"]).total_seconds() / 86400.0

spin_lon_proj = row["spin_lon_eq"] + grad_lon * dt_target
spin_lat_proj = row["spin_lat_eq"] + grad_lat * dt_target

args.spinvector[0] = spin_lon_proj
args.spinvector[1] = spin_lat_proj

print("Gradient lon (deg/day):", grad_lon)
print("Gradient lat (deg/day):", grad_lat)
print("Projected lon_eq:", spin_lon_proj)
print("Projected lat_eq:", spin_lat_proj)

# now read in the goodtime context file

df_gt = pd.read_csv(
    args.context,   # your file path to the context file
    header=None        # since your snippet has no header row
)

df_gt.columns = [
    "date",
    "met_start",
    "met_stop",
    "bin_start",
    "bin_stop",
    "inst",
    "H",
    "O",
    "exposure",
    "ppm_angle",
    "ppm_angle_sdc"
]

# df_gt["date_dt"] = pd.to_datetime(df_gt["date"].astype(str), format="%Y%j")

# convert DOY -> datetime
df_gt["date_dt"] = pd.to_datetime(
    df_gt["date"].astype(str),
    format="%Y%j",
    errors="coerce"   # avoids crashes if a bad value appears
)

# optional: drop invalid rows
df_gt_valid = df_gt.dropna(subset=["date_dt"])

# find closest row
idx = (df_gt_valid["date_dt"] - target_dt).abs().idxmin()
row = df_gt_valid.loc[idx]

# print(df_gt["date"].dtype)
# print(type(target_dt))

# --- find closest row (as before) ---
idx = (df_gt["date_dt"] - target_dt).abs().idxmin()
row = df_gt.loc[idx]

# ra_st, dec_st, mag_st = parse_stars(args)
ra_st, dec_st, mag_st = parse_stars_tyc(args)

# pivotAng = 90.0 * PI / 180.0
pivotAng = row["ppm_angle"]

# Check for exact match
if row["date_dt"] != target_dt:
    print("DANGER WILL ROBINSON: YOU DID NOT FIND THE TARGET PPM on date ", date1)
    print("target date and row date = ", target_dt, row["date_dt"])
    dt_days = (target_dt - row["date_dt"]).total_seconds() / 86400.0
    if (dt_days < 0.5):
        print("leaving things as they are")
    elif (pivotAng > 90.5):
        if (dt_days < 1.1):
            pivotAng = 90.0
        elif (dt_days < 2.2):
            pivotAng = 75.0
        else:
            pivotAng = 90.0
    elif (pivotAng < 89.5):
        if (dt_days < 1.1):
            pivotAng = 90.0
        elif (dt_days < 2.2):
            pivotAng = 105.0
        else:
            pivotAng = 90.0
    else:
        print("not sure how to change the pivot angle, since we are near 90")
    print("ppm angle = ", pivotAng)

mspin = args.msp

npset = mspin * nbin

sts_set = np.linspace(0.,0.,npset)

sts_best = np.linspace(0.,0.,nbin)

bin0 = args.bin[0]
bin1 = args.bin[1]

phaseadjust = 0.0

for i in range(0,mspin):
    
    sts_spin = star_spin(args, ra_st, dec_st, mag_st, phaseadjust, pivotAng)
    
    for j in range(0,nbin):
        kk = nbin * i + j
        sts_set[kk] = sts_spin[j]
           # if (sts_spin[j] < -1.0):
            #    print(j, sts_spin[j])
        
sts_ave_arr = sts_ave(sts_set,mspin)
   
phase_best = 0.0
print_star_results(sts_ave_arr, args.outstring+'_results')
plot_results(args, sts_ave_arr, args.outstring+'_results')
    
    
