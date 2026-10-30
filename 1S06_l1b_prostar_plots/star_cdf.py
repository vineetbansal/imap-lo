#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 29 18:58:08 2026

@author: hafijulislam
"""

from spacepy.pycdf import CDF
import numpy as np
import os
import argparse
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from spacepy import pycdf

def argParsing():
    
    parser = argparse.ArgumentParser(
        description=(
            "This tool plots the 2d l1b star sensor data along with the NEP angle average"
            "The figure is saved in the working directory"
        )
    )

    parser.add_argument(
        '-s', '--starfilepath',
        required=True,
        help='level 1b prostar'
    )

    parser.add_argument(
        '-k', '--housekeeping',
        required=True,
        dest='kfle',
        help='level 1b housekeeping file'
    )
    
    parser.add_argument('-o', '--outputFile',
                        help='the output  file',
                        dest='outFile',
                        required=True)
    
    return parser.parse_args()

args = argParsing()

cdf_hk = pycdf.CDF(args.kfle)

# need to fix this to make it a time thing
try:
    SPIN_SECONDS = np.average(cdf_hk['spin_period'][10000:60000])
except:
    SPIN_SECONDS = 15.011

file = args.starfilepath

# SPIN_SECONDS = 15
# file = '/Users/hafijulislam/UNH/imap-data-access/prostar/imap_lo_l1b_prostar_20260201-repoint00144_v002.cdf'

epoch = datetime(2010, 1, 1, 0, 0, 0)
cdf = CDF(file)
data = cdf['avg_amplitude'][...]
spinangle = cdf['spin_angle'][:]
time_bins1 = cdf['met'][...]

fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True, gridspec_kw={'width_ratios': [3, 1],'wspace': 0.1},figsize=(10,6))
im = ax1.imshow(data.T,aspect='auto',origin='lower',norm=LogNorm())

yticks = np.linspace(0, 720, num=6, endpoint=False)
ytick_labels = np.linspace(0, 360, num=6, endpoint=False)
ax1.set_yticks(yticks,ytick_labels)

ticks = np.linspace(time_bins1[0], time_bins1[-1], num=5)
spin_labels = (ticks - ticks[0]) / SPIN_SECONDS
labels_datetime = [epoch + timedelta(seconds=int(x)) for x in ticks]
labels_doy = [
    round(t.timetuple().tm_yday + (t.hour/24) + (t.minute/1440) + (t.second/86400), 3)
    for t in labels_datetime
]
try:
    dbl_labels = [f"{int(sp)}\n{lab}" for sp, lab in zip(spin_labels, labels_doy)]
except:
    dbl_labels = [f"{float(sp)}\n{lab}" for sp, lab in zip(spin_labels, labels_doy)]
#    dbl_labels = [f"{int(sp)}\n{lab}" for sp, lab in zip(spin_labels, labels_doy)]

data[data<0] = np.nan
val_720 = np.mean(data, axis=0)
mask = (val_720 != 0) & ~np.isnan(val_720)

angle_edges = np.arange(0, 720 +1,1)
angle_centers = (angle_edges[:-1] + angle_edges[1:]) / 2
ax2.plot(val_720[mask], angle_centers[mask], '-', color='b',lw=0.5)

# --- Save NEP vs Star Sensor Voltage to CSV ---
csv_out = os.path.splitext(args.outFile)[0] + "_nep_vs_voltage.csv"

# nep = angle_centers[mask]
nep = (spinangle[mask] - 2.0) % 360
voltage = val_720[mask]

out_arr = np.column_stack((nep, voltage))

# sort by first column (NEP)
out_arr = out_arr[np.argsort(out_arr[:, 0])]

np.savetxt(
    csv_out,
    out_arr,
    delimiter=",",
    header="NEP_deg,StarSensor_mV",
    comments=""
)

print(f"Saved NEP vs voltage data to: {csv_out}")

ax2.set_xlabel("Average Amplitude (mV)")
ax2.grid(linewidth=0.5,linestyle='--',color='lightgrey',alpha=0.6)

tick_positions = np.array([np.argmin(np.abs(time_bins1 - t)) for t in ticks])
ax1.set_xticks(tick_positions)
ax1.set_xticklabels(dbl_labels, rotation=0)
ax1.text(-0.2, -0.08, "Spin\nDOY", transform=ax1.transAxes, fontsize=10)

ax1.set_ylabel("\nNEP Angle (deg)")
t0 = time_bins1[0]
MET = epoch + timedelta(seconds=int(t0))
start_time = MET.strftime("%d-%b-%Y %H:%M:%S")
basename = os.path.splitext(os.path.basename(file))[0]
fig.suptitle(
    f"Start Time: {start_time}\n\nStar File: {basename}\n\n",
    y=0.98, fontsize=10
) 

cbar = fig.colorbar(im, ax=ax1, orientation="vertical",aspect=40,
                    location='left', pad=0.2)
cbar.set_label("Amplitude (mV)")

plt.savefig(args.outFile, dpi=250)


# assuming out_arr is already sorted
x = out_arr[:, 0]   # NEP
y = out_arr[:, 1]   # voltage

plt.figure()
plt.plot(x, y)

plt.xlim(0, 360)
plt.xlabel("NEP (deg)")
plt.ylabel("Star Sensor (mV)")
plt.title("NEP vs Star Sensor Voltage")

plt.tight_layout()
fig_out = os.path.splitext(args.outFile)[0] + "_nep_vs_voltage.png"
plt.savefig(fig_out, dpi=300)
plt.close()

#plt.tight_layout()
#plt.show()

