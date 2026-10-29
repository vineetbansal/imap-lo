from datetime import datetime, timezone
import pandas as pd
import numpy as np
import argparse
from pathlib import Path
from spacepy import pycdf

TOF3_L = [ 11.0, 7.0, 3.5, 0.0 ]
TOF3_H = [15.0, 11.0, 7.0, 3.5 ]
# TOF_0, TOF_1, TOF_2
E_PEAK_H = [ 20.0, 10.0, 10.0 ]
H_PEAK_L = [ 20.0, 10.0, 12.0 ]
H_PEAK_H = [ 70.0, 50.0, 33.7 ]
CO_PEAK_L = [ 100.0, 60.0, 61.9   ]
CO_PEAK_H = [ 270.0, 150.0, 170.1 ]
#CO_PEAK_L = [ 100.0, 60.0, 60.0   ] what Hafeez used
#CO_PEAK_H = [ 270.0, 150.0, 150.0 ]
#  for GOLD, TOF2 < 15, TOF2 < 35 and > 35

# EU = C0 + C1 * ADC
# ADC_TOF = [C0, C1]
ADC_TOF0 = [5.5252E-01 ,   1.6837E-01]
ADC_TOF1 = [-7.2018E-01,  1.6512E-01]
ADC_TOF2 = [3.7442E-01,    1.6641E-01]
ADC_TOF3 = [4.6726E-01,    1.7144E-01]

CHKSM_LB = -21
CHKSM_RB = -6

PI = np.pi

TICK_TO_SEC = 4.096e-3

file = './Instrument_FM1_playback_full_feb_ILO_SCI_DE_dec_20260319T004334_DN.csv'

shcoarse, absent, timestamp, egy, mode, tof0, tof1, tof2, tof3, checksum, position = np.loadtxt(
        file, delimiter=',', unpack=True, skiprows=1
    )

df = pd.DataFrame({
        'shcoarse': shcoarse,
        'absent': absent,
        'mode': mode,
        'esa_step': egy,
        'tof0': tof0,
        'tof1': tof1,
        'tof2': tof2,
        'tof3': tof3,
        'cksm': checksum,
        'de_time': timestamp
    })


    # only golden triples
df = df[(df['absent'] == 0) & ((df['mode'] == 1) | (df['mode']==0))]

df['tof1d'] = df['tof0'] + df['tof3'] - df['tof2'] + df['cksm']

df['tof0'] = df['tof0'] * 2 * ADC_TOF0[1] + ADC_TOF0[0]
df['tof2'] = df['tof2'] * 2 * ADC_TOF2[1] + ADC_TOF2[0]
df['tof3'] = df['tof3'] * 2 * ADC_TOF3[1] + ADC_TOF3[0]

    # since mode==1 after filtering, no need for np.where
#df['tof1'] = df['tof1d'] * ADC_TOF1[1] + ADC_TOF1[0]
df['tof1'] = np.where(df['mode']==1, (df['tof1d']*2*ADC_TOF1[1]+ADC_TOF1[0]),(df['tof1']* 2 * ADC_TOF1[1]+ADC_TOF1[0]))

df['tof0'] = df['tof0'] + 0.5 * df['tof3']
df['tof1'] = df['tof1'] - 0.5 * df['tof3']

df['quadrant'] = 1.0 * df['tof3']

absent      = df['absent'][:]
mode    = df['mode'][:]
esa_step = df['esa_step'][:]
tof0     = df['tof0'][:]
tof1      = df['tof1'][:]
tof2      = df['tof2'][:]
tof3      = df['tof3'][:]
de_time   = df['de_time'][:]
shcoarse =  df['shcoarse'][:] 
cksum     =  df['cksm'][:]

# ================================
# Time window definition (Feb 2026)
# ================================
UTC = timezone.utc

windows = {
    1:  {"start": datetime(2026, 2, 1, 12, tzinfo=UTC), "end": datetime(2026, 2, 2, 10, tzinfo=UTC)},
    2:  {"start": datetime(2026, 2, 3, 12, tzinfo=UTC), "end": datetime(2026, 2, 4, 10, tzinfo=UTC)},
    3:  {"start": datetime(2026, 2, 5, 12, tzinfo=UTC), "end": datetime(2026, 2, 6, 10, tzinfo=UTC)},
    4:  {"start": datetime(2026, 2, 7, 12, tzinfo=UTC), "end": datetime(2026, 2, 8, 10, tzinfo=UTC)},
    5:  {"start": datetime(2026, 2, 9, 12, tzinfo=UTC), "end": datetime(2026, 2, 10, 10, tzinfo=UTC)},
    6:  {"start": datetime(2026, 2, 11, 12, tzinfo=UTC), "end": datetime(2026, 2, 12, 10, tzinfo=UTC)},
    7:  {"start": datetime(2026, 2, 13, 12, tzinfo=UTC), "end": datetime(2026, 2, 14, 10, tzinfo=UTC)},
    8:  {"start": datetime(2026, 2, 15, 12, tzinfo=UTC), "end": datetime(2026, 2, 16, 10, tzinfo=UTC)},
    9:  {"start": datetime(2026, 2, 17, 12, tzinfo=UTC), "end": datetime(2026, 2, 18, 10, tzinfo=UTC)},
    10: {"start": datetime(2026, 2, 19, 12, tzinfo=UTC), "end": datetime(2026, 2, 20, 10, tzinfo=UTC)},
    11: {"start": datetime(2026, 2, 23, 12, tzinfo=UTC), "end": datetime(2026, 2, 24, 10, tzinfo=UTC)},
    12: {"start": datetime(2026, 2, 25, 12, tzinfo=UTC), "end": datetime(2026, 2, 26, 10, tzinfo=UTC)},
    13: {"start": datetime(2026, 2, 27, 12, tzinfo=UTC), "end": datetime(2026, 2, 28, 10, tzinfo=UTC)},
}

epoch = datetime(2010, 1, 1, tzinfo=UTC)

def to_met(dt):
    return (dt - epoch).total_seconds()

windows_met = {
    k: {"t0": to_met(v["start"]), "t1": to_met(v["end"])}
    for k, v in windows.items()
}

out_file='./GSEOS_DE'
for k, w in windows_met.items():
    t0 = w["t0"]
    t1 = w["t1"]
    print(f"Window {k}: {t0} -> {t1}")

    for esa in range (1,8):
        with open(out_file+'_window'+str(k)+'_ESA'+str(esa)+'.csv', 'w') as fle:
            print("shcoarse,tof3,tof2,tof1,tof0,timestamp,esa_step", file=fle)

            esa_check = (esa_step == esa)
            met_check = ( shcoarse >= t0 ) & ( shcoarse <= t1 )
            tof0_check = (tof0 >= CO_PEAK_L[0]) & (tof0 <= CO_PEAK_H[0])
            tof1_check = (tof1 >= CO_PEAK_L[1]) & (tof1 <= CO_PEAK_H[1])
            tof2_check = (tof2 >= CO_PEAK_L[2]) & (tof2 <= CO_PEAK_H[2])
        #    tof3_check = (tof3 >= 0.0) & (tof3 <= 20.0)

            mask = esa_check & tof0_check & tof1_check & tof2_check & met_check

    # -------------------------------
    # Filter arrays
    # -------------------------------

            filtered = {
                'shcoarse': shcoarse[mask],
                'tof3': tof3[mask],
                'tof2': tof2[mask],
                'tof1': tof1[mask],
                'tof0': tof0[mask],
                'de_time': de_time[mask],
                'esa_step': esa_step[mask]
                }
                
            n = len(filtered['shcoarse'])
            if (n > 0):
                for row in zip(
                    filtered['shcoarse'],
                    filtered['tof3'],
                    filtered['tof2'],
                    filtered['tof1'],
                    filtered['tof0'],
                    filtered['de_time'],
                    filtered['esa_step']
                    ):
                    print(','.join(map(str, row)), file=fle)
    
        print(f"1G01 CO: ESA = {esa}, Filtered {mask.sum()} rows written to {out_file} + ESA")



