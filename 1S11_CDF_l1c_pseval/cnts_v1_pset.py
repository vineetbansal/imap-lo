
import numpy as np
from spacepy import pycdf
import argparse
from datetime import datetime
import os

PI = np.pi
small = 1.0e-10

# fname = './'
#  cdf = pycdf.CDF(fname)
#  cdf.keys()

def argParsing():

    parser = argparse.ArgumentParser(description='This tool accepts a GSEOS filename and makes cool plots for IMAP-Lo.')
    
    parser.add_argument('-f', '--file',
                            help='the l1c  file ',
                           dest='file',
                           required=True)

    return parser.parse_args()


def print_counts(fle, date, aram_counts,  aram_bg, aram_bgerr, expo):
        
    print(f"date, aram[H], aram_bg[H], aram_bgerr[H], aram[O], aram_bg[O], aram_bgerr[O], exposure(s)", file=fle)
    print( 
        f"{date}, {aram_counts[0]}, {aram_bg[0]}, {aram_bgerr[0]}, {aram_counts[1]}, {aram_bg[1]}, {aram_bgerr[1]}, {expo}", file=fle
        )

def doy_fraction(t):
    start = datetime(t.year, 1, 1)
    return (t - start).total_seconds() / 86400.0 + 1

def read_ps(args):

    cdf = pycdf.CDF(args.file)

    epoch = cdf['epoch'][:]
    yr1  = epoch[0].year
    doy1 = int(doy_fraction(epoch[0]) )
    sdoy1 = f"{doy1:03d}"
    date1 = f"{yr1}{sdoy1}"

  #  var='h_counts'
  #    var='o_counts'

    try:
        sc_velocity = cdf['sc_velocity'][:]
        sc_velocity = np.asarray(sc_velocity)
    except:
        sc_velocity = np.array([small,small,small])

    # Ensure we end up with a single 3-vector
    if sc_velocity.ndim == 1 and sc_velocity.size == 3:
        ram = sc_velocity

    elif sc_velocity.ndim == 2 and sc_velocity.shape[1] == 3:
        # time series — use mean direction (or choose index 0 if preferred)
        ram = np.mean(sc_velocity, axis=0)

    else:
        raise ValueError(f"Unexpected sc_velocity shape: {sc_velocity.shape}")

    # normalize
    ram = ram / np.linalg.norm(ram)

    aram_counts = np.zeros(2)
    aram_bg = np.zeros(2)
    aram_bgerr = np.zeros(2)
    
    ivar = 0

    for var, bgvar, bgsys in (
        ('h_counts','h_background_rates','h_background_rates_sys_err'),
        ('o_counts','o_background_rates','o_background_rates_sys_err'),
    ):
        counts = np.sum(cdf[var][0,:,:,:],axis=2) # ESA , spin
        exposure = np.sum(cdf['exposure_time'][0,:,:,:],axis=2) # ESA , spin
        bg = np.sum(cdf[bgvar][0,:,:,:],axis=2)/40.0
        bgerr = np.sum(cdf[bgsys][0,:,:,:],axis=2)/40.0
        
        lat7 = np.sum(cdf['hae_latitude'][0,:,:],axis=1)/40.0
        lon7 = np.sum(cdf['hae_longitude'][0,:,:],axis=1)/40.0
        lat_rad = np.radians(lat7)
        lon_rad = np.radians(lon7)

        expo = 0.0
        sumcnt = 0
        nspin = lat7.shape[0]

        for i in range(nspin): 

            lon = lon_rad[i]
            coslat = np.cos(lat_rad[i])
            x = coslat * np.cos(lon)
            y = coslat * np.sin(lon)
            z = np.sin(lat_rad[i])

            xyz = np.array([x,y,z])
            
            view = np.dot(xyz,ram)
            if (view <= 0.0):
                aram_counts[ivar] = aram_counts[ivar] + np.sum(counts[:,i])
                expo = expo + np.sum(exposure[:,i])
                aram_bg[ivar] = aram_bg[ivar] + (np.sum(bg[:,i])/7.0)
                aram_bgerr[ivar] = aram_bgerr[ivar] + (np.sum(bgerr[:,i])/7.0)
                sumcnt = sumcnt + 1.0

        if sumcnt > 0:
            aram_bg[ivar] /= sumcnt
            aram_bgerr[ivar] /= sumcnt


        ivar = ivar + 1
#        print(x,',',y,',',z)

 #   print(f"ram = {ram}, nspin = {nspin}, date = {date1}")

    basename = os.path.basename(args.file).split('.')[0]
    outfile = f"output/{basename}_aram_counts_{date1}.csv"

    with open(outfile, 'w') as fle:

        print_counts(fle, date1, aram_counts,  aram_bg, aram_bgerr, expo)

# MAIN 

os.makedirs("output", exist_ok=True)
if __name__ == "__main__":
    args = argParsing()
    read_ps(args)
