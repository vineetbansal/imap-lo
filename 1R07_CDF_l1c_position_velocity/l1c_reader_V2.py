#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov  2 17:10:13 2025

@author: hafijulislam
"""

# >>> import cdflib
# >>> cdf = cdflib.CDF("./input/imap_lo_l1a_de_20260120-repoint00132_v001.cdf")
# >>> cdf.cdf_info()
# CDFInfo(CDF=PosixPath('/Users/nschwadron/data/imap_pipeline2/1R3-CDF-spinphaseDEWTime/input/imap_lo_l1a_de_20260120-repoint00132_v001.cdf'), Version='3.9.0', Encoding=6, Majority='Row_major', rVariables=[], zVariables=['met', 'de_count', 'passes', 'coincidence_type', 'de_time', 'esa_step', 'mode', 'tof0', 'tof1', 'tof2', 'tof3', 'cksm', 'pos', 'shcoarse', 'epoch', 'direct_events', 'direct_events_label'], Attributes=[{'Acknowledgement': 'Global'}, {'Data_type': 'Global'}, {'Data_version': 'Global'}, {'Descriptor': 'Global'}, {'Discipline': 'Global'}, {'File_naming_convention': 'Global'}, {'HTTP_LINK': 'Global'}, {'Instrument_type': 'Global'}, {'LINK_TITLE': 'Global'}, {'Logical_file_id': 'Global'}, {'Logical_source': 'Global'}, {'Logical_source_description': 'Global'}, {'Mission_group': 'Global'}, {'PI_affiliation': 'Global'}, {'PI_name': 'Global'}, {'Project': 'Global'}, {'Rules_of_use': 'Global'}, {'Source_name': 'Global'}, {'TEXT': 'Global'}, {'Repointing': 'Global'}, {'Start_date': 'Global'}, {'Parents': 'Global'}, {'ground_software_version': 'Global'}, {'Generation_date': 'Global'}, {'Generated_by': 'Global'}, {'DEPEND_0': 'Variable'}, {'CATDESC': 'Variable'}, {'DISPLAY_TYPE': 'Variable'}, {'FIELDNAM': 'Variable'}, {'FILLVAL': 'Variable'}, {'FORMAT': 'Variable'}, {'LABLAXIS': 'Variable'}, {'UNITS': 'Variable'}, {'VALIDMIN': 'Variable'}, {'VALIDMAX': 'Variable'}, {'VAR_TYPE': 'Variable'}, {'DEPEND_1': 'Variable'}, {'LABL_PTR_1': 'Variable'}, {'TIME_BASE': 'Variable'}, {'RESOLUTION': 'Variable'}, {'TIME_SCALE': 'Variable'}, {'REFERENCE_POSITION': 'Variable'}, {'DICT_KEY': 'Variable'}, {'MONOTON': 'Variable'}, {'SCALETYP': 'Variable'}], Copyright='\nCommon Data Format (CDF)\nhttps://cdf.gsfc.nasa.gov\nSpace Physics Data Facility\nNASA/Goddard Space Flight Center\nGreenbelt, Maryland 20771 USA\n(User support: gsfc-cdf-support@lists.nasa.gov)\n', Checksum=False, Num_rdim=0, rDim_sizes=[], Compressed=False, LeapSecondUpdate=None)
# 'met', 'de_count', 'passes', 'coincidence_type', 'de_time', 'esa_step', 'mode', 'tof0', 'tof1', 'tof2', 'tof3', 'cksm', 'pos', 'shcoarse', 'epoch', 'direct_events', 'direct_events_label'

import math
import pandas as pd
import numpy as np
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from spacepy import pycdf
import spiceypy as spice

TOF3_L = [ 11.0, 7.0, 3.5, 0.0 ]
TOF3_H = [15.0, 11.0, 7.0, 3.5 ]
# TOF_0, TOF_1, TOF_2
E_PEAK_H = [ 20.0, 10.0, 10.0 ]
H_PEAK_L = [ 20.0, 10.0, 10.0 ]
H_PEAK_H = [ 70.0, 50.0, 40.0 ]
CO_PEAK_L = [ 100.0, 60.0, 60.0   ]
CO_PEAK_H = [ 270.0, 150.0, 150.0 ]
#  for GOLD, TOF2 < 15, TOF2 < 35 and > 35

# EU = C0 + C1 * ADC
# ADC_TOF = [C0, C1]
ADC_TOF0 = [5.5252E-01 ,   1.6837E-01]
ADC_TOF1 = [-7.2018E-01,  1.6512E-01]
ADC_TOF2 = [3.7442E-01,    1.6641E-01]
ADC_TOF3 = [4.6726E-01,    1.7144E-01]

CHKSM_LB = -21
CHKSM_RB = -6

# Constant offset between TT2000 epoch and Unix epoch
# 2000-01-01 12:00:00 TT  = 2000-01-01 11:58:55.816 UTC
# Difference to 1970-01-01 00:00:00 UTC
TT2000_TO_UNIX_SECONDS = 946728000.0 - 64.184  # = 946727935.816

PI = np.pi

eps = np.deg2rad(23.4392911)
small = 1.0e-10

rot_ecl_to_eq = np.array([
    [1, 0, 0],
    [0,  np.cos(eps), -np.sin(eps)],
    [0,  np.sin(eps),  np.cos(eps)]
])

cols = ['shcoarse', 'absent', 'timestamp', 'egy', 'mode', 'TOF0', 'TOF1', 'TOF2', 'TOF3', 'checksum', 'position']

def print_coord(fle, date, spin_axis, sc_lon, sc_lat, sc_lon2, sc_lat2, sc_lon_ephem, sc_lat_ephem, spin_lon, spin_lat, spin_lon_eq, spin_lat_eq, sc_position, sc_velocity, spin_axis_angle):
        
    print(f"date, spin_axis_angle, sc_lon[V], sc_lat[V], sc_lon[E], sc_lat[E], sc_lon[EPH], sc_lat[EPH], spin_lon, spin_lat, spin_lon_eq, spin_lat_eq, spin_axis, sc_position, sc_velocity", file=fle)
    print( 
        f"{date}, {spin_axis_angle}, {sc_lon}, {sc_lat}, {sc_lon2}, {sc_lat2}, {sc_lon_ephem}, {sc_lat_ephem}, {spin_lon}, {spin_lat}, {spin_lon_eq}, {spin_lat_eq}, {spin_axis}, {sc_position}, {sc_velocity}", file=fle
        )

def sph_to_cart(lat, lon):
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    x = np.cos(lat_rad) * np.cos(lon_rad)
    y = np.cos(lat_rad) * np.sin(lon_rad)
    z = np.sin(lat_rad)
    return np.array([x, y, z])


def convert_spin_to_J2000(lon_spin, lat_spin):
    
    xyz = sph_to_cart(lat_spin, lon_spin)
    spin_eq = rot_ecl_to_eq @ xyz

    lat_spin_eq = np.degrees(np.arcsin(spin_eq[2]))
    lon_spin_eq = np.degrees(np.arctan2(spin_eq[1], spin_eq[0])) # negative sign since we are looking from the inside
    lon_spin_eq = (lon_spin_eq + 360) % 360  # wrap

    return lon_spin_eq, lat_spin_eq

def to_unix_seconds(epoch):
    """
    Accepts either:
      • TT2000 nanoseconds (int/float)
      • datetime object
      • already-unix seconds
    """
    if isinstance(epoch, datetime):
        return epoch.replace(tzinfo=timezone.utc).timestamp()

    # assume TT2000 if very large number
    if isinstance(epoch, (int, float)) and epoch > 1e12:
        return epoch * 1e-9 + TT2000_TO_UNIX_SECONDS

    return float(epoch)

def earth_heliocentric_coords(epoch):
    """
    Compute approximate Earth heliocentric ecliptic longitude and latitude (degrees)
    from a Unix epoch time. Simplified, no external libraries.

    Returns:
        lon_deg : float : heliocentric ecliptic longitude [0-360°]
        lat_deg : float : heliocentric ecliptic latitude (very small) in degrees
    """

    epoch_time = to_unix_seconds(epoch)

    # Convert epoch to Julian centuries since J2000
    dt = datetime.fromtimestamp(epoch_time, tz=timezone.utc)
    year = dt.year
    month = dt.month
    day = dt.day + dt.hour/24 + dt.minute/1440 + dt.second/86400

    if month <= 2:
        year -= 1
        month += 12
    A = int(year/100)
    B = 2 - A + int(A/4)
    JD = int(365.25*(year + 4716)) + int(30.6001*(month + 1)) + day + B - 1524.5

    T = (JD - 2451545.0) / 36525  # Julian centuries since J2000

    # Orbital elements for Earth (simplified)
    i = math.radians(0.00005)                  # inclination to ecliptic plane
    Omega = math.radians(-11.26064 + 0.01306*T)  # longitude of ascending node
    omega = math.radians(102.94719 + 0.323*T)    # argument of perihelion
    M = math.radians((357.529 + 35999.050*T) % 360)  # mean anomaly

    # Heliocentric ecliptic latitude (deg)
    beta = math.asin(math.sin(i) * math.sin(omega + M))
    lat_deg = math.degrees(beta)

    # Heliocentric ecliptic longitude (deg)
    lon = (omega + M + Omega) % (2*math.pi)
    lon_deg = math.degrees(lon)

    return lon_deg, lat_deg


def earth_ecliptic_longitude(epoch):
    """
    Approximate Earth heliocentric ecliptic longitude (deg)
    from Unix epoch time (seconds since 1970-01-01 UTC).

    Accuracy ~0.01–0.1 degrees.
    """

    epoch_seconds = to_unix_seconds(epoch)

    # Convert to Julian Date
    jd = epoch_seconds / 86400.0 + 2440587.5

    # Julian centuries since J2000
    T = (jd - 2451545.0) / 36525.0

    # Mean longitude (deg)
    L0 = 280.46646 + 36000.76983*T + 0.0003032*T**2
    L0 = np.mod(L0, 360.0)

    # Mean anomaly (deg)
    M = 357.52911 + 35999.05029*T - 0.0001537*T**2

    # Equation of center (deg)
    C = (1.914602 - 0.004817*T - 0.000014*T**2)*np.sin(np.deg2rad(M)) \
        + (0.019993 - 0.000101*T)*np.sin(np.deg2rad(2*M)) \
        + 0.000289*np.sin(np.deg2rad(3*M))

    # True longitude (Sun)
    true_long_sun = L0 + C

    # Earth heliocentric longitude = Sun longitude + 180°
    earth_long = np.mod(true_long_sun + 180.0, 360.0)

    return earth_long


def doy_fraction(t):
    start = datetime(t.year, 1, 1)
    return (t - start).total_seconds() / 86400.0 + 1

def angle_between(u, v):
    u = np.asarray(u)
    v = np.asarray(v)

    return np.arctan2(
        np.linalg.norm(np.cross(u, v)),
        np.dot(u, v)
    )   # radians

def spin_axis_from_vectors(V):
    """
    Estimate spin axis from look vectors.

    Parameters
    ----------
    V : (N,3) array
        Unit direction vectors

    Returns
    -------
    spin_axis : (3,) array
        Unit spin axis vector
    """

    V = np.asarray(V)

    # Normalize just in case
    V = V / np.linalg.norm(V, axis=1)[:, None]

    # Covariance matrix
    M = V.T @ V

    # Eigenvector with smallest eigenvalue
    evals, evecs = np.linalg.eigh(M)
    spin_axis = evecs[:, np.argmin(evals)]

    # Normalize
    spin_axis /= np.linalg.norm(spin_axis)

    return spin_axis


def find_pivot_angle(
    cdf,
    lat_var='hae_latitude',
    lon_var='hae_longitude',
    mid_index=19,
    nep_index=0,
    ram_index=899,
    nspin=3600
):

    #Load lat / lon
    # --------------------
    lat = cdf[lat_var][0, :nspin, mid_index]
    lon = cdf[lon_var][0, :nspin, mid_index]

    # Convert to radians
    colat = np.deg2rad(90.0 - lat)
    lon = np.deg2rad(lon)

    # --------------------
    # Cartesian look vectors
    # --------------------
    x = np.sin(colat) * np.cos(lon)
    y = np.sin(colat) * np.sin(lon)
    z = np.cos(colat)

    V = np.column_stack((x, y, z))   # (nspin, 3)

    # --------------------
    # NEP proxy solution
    # --------------------
    inep = np.argmax(z)
    isep = np.argmin(z)
    nep = V[inep]
    sep = V[isep]

    theta = angle_between(v1, v2)
    theta_deg = np.degrees(theta)
    pivot_ang = 0.5*theta_deg

    return pivot_ang


def compute_spin_axis_from_cdf_gen(
    cdf,
    lat_sc,
    lon_sc,
    lat_var='hae_latitude',
    lon_var='hae_longitude',
    sc_vel_var='sc_velocity',
    sc_pos_var='sc_position',
    mid_index=19,
    nep_index=0,
    ram_index=899,
    nspin=3600
):

    # --------------------
    # Load lat / lon
    # --------------------
    lat = cdf[lat_var][0, :nspin, mid_index]
    lon = cdf[lon_var][0, :nspin, mid_index]

    try: 
        scv = cdf[sc_vel_var][:]
    except:
        scv=np.array([small,small,small])
    try:
        pos = cdf[sc_pos_var][:]
    except:
        pos=np.array([0,0,0])

#    sun = np.array([-xsc,-ysc,-zsc])
#    dot = np.dot(scv, sun) 
#    scv = scv  - dot * sun

    nep_axis = np.array([0,0,1])
    to_sun = np.cross(nep_axis, scv)
    to_sun /= (np.linalg.norm(to_sun))

    sx, sy, sz = -1.0 * to_sun
    lon_sc_sun = np.rad2deg(np.arctan2(sy, sx)) % 360.0
   

    if (lon_sc_sun > lon_sc):

#        print(lon_sc_sun, lon_sc)

        lat_sc_rad = np.deg2rad(lat_sc)
        colat_sc_rad = np.deg2rad(90.0 - lat_sc)
        lon_sc_rad = np.deg2rad(lon_sc)
        
        xsc = np.sin(colat_sc_rad)*np.cos(lon_sc_rad )
        ysc = np.sin(colat_sc_rad)*np.sin(lon_sc_rad )
        zsc = np.cos(colat_sc_rad)

        to_sun = np.array([-xsc,-ysc,-zsc])

    # Convert to radians
    colat = np.deg2rad(90.0 - lat)
    lon = np.deg2rad(lon)

    # --------------------
    # Cartesian look vectors
    # --------------------
    x = np.sin(colat) * np.cos(lon)
    y = np.sin(colat) * np.sin(lon)
    z = np.cos(colat)

    V = np.column_stack((x, y, z))   # (nspin, 3)

    spin_axis = spin_axis_from_vectors(V)

    handed = np.sign(np.dot(spin_axis, to_sun))
    spin_axis *= handed

    # --------------------
    # Convert back to lat / lon
    # --------------------
    sx, sy, sz = spin_axis
    lat_spin = np.rad2deg(np.arcsin(sz))
    lon_spin = np.rad2deg(np.arctan2(sy, sx)) % 360.0

    # --------------------
    # Convert sc to lat / lon
    # --------------------
    sx, sy, sz = -1.0 * to_sun
    lat_sc = np.rad2deg(np.arcsin(sz))
    lon_sc = np.rad2deg(np.arctan2(sy, sx)) % 360.0

    # --------------------
    # Diagnostics
    # --------------------
    theta = angle_between(to_sun, spin_axis)
    theta_deg = np.degrees(theta)

    diagnostics = {
        "spin_axis": spin_axis,
        "mean_dot_orthogonality": np.mean(np.abs(V @ spin_axis)),
        "std_dot_orthogonality": np.std(V @ spin_axis),
        "solar_direction": to_sun,
        "sc_position": -1.0*to_sun, 
        "sc_ephemeris": pos,
        "sc_velocity":scv,
        "spin_angle": theta_deg
    }
    return spin_axis, lat_spin, lon_spin, lat_sc, lon_sc, diagnostics

def compute_spin_axis_from_cdf_90(
    cdf,
    lat_var='hae_latitude',
    lon_var='hae_longitude',
    sc_vel_var='sc_velocity',
    mid_index=19,
    nep_index=0,
    ram_index=899,
    nspin=3600
):
    """
    Compute spacecraft spin axis from HAE look directions.

    Parameters
    ----------
    cdf : spacepy.pycdf.CDF
        Open CDF file
    lat_var, lon_var : str
        Variable names for latitude / longitude (deg)
    esa_index : int
        ESA or look index
    nep_index : int
        Spin index used as NEP proxy
    ram_index : int
        Spin index used as RAM proxy
    nspin : int
        Number of spin samples

    Returns
    -------
    spin_axis : (3,) ndarray
        Unit vector spin axis (HAE Cartesian)
    lat_spin, lon_spin : float
        Spin axis latitude / longitude (deg)
    diagnostics : dict
        Extra useful stuff
    """

    # --------------------
    # Load lat / lon
    # --------------------
    lat = cdf[lat_var][0, :nspin, mid_index]
    lon = cdf[lon_var][0, :nspin, mid_index]


    # Convert to radians
    colat = np.deg2rad(90.0 - lat)
    lon = np.deg2rad(lon)

    # --------------------
    # Cartesian look vectors
    # --------------------
    x = np.sin(colat) * np.cos(lon)
    y = np.sin(colat) * np.sin(lon)
    z = np.cos(colat)

    V = np.column_stack((x, y, z))   # (nspin, 3)

    # --------------------
    # NEP proxy solution
    # --------------------
    inep = np.argmax(z)
    nep_index = inep
    nep_proxy = V[nep_index]
    ram_proxy = V[ram_index]
    spin_guess = np.cross(nep_proxy, ram_proxy)
   # print("1.")
   # print(nep_proxy)
   # print(ram_proxy)
   # print(spin_guess)
    spin_guess /= np.linalg.norm(spin_guess)
   # print("2.")
   # print(spin_guess)

    C = np.cross(nep_proxy, V)

    # Handedness sign per spin sample
    sign = np.sign(C @ spin_guess)

    # Optional: drop degenerate cases
    mask = sign != 0
    C = C[mask]
    sign = sign[mask]

    # Apply sign
    C *= sign[:, None]

    mag = np.linalg.norm(C, axis=1)
    mask = mag > 0

    Csel = C[mask]
    mag_sel = mag[mask]

    normed = Csel / mag_sel[:, None]

    spin_a = np.average(normed, axis=0)
#    spin_a = (C[mask] / mag[mask][:, None]).mean(axis=0)
    spin_a /= np.linalg.norm(spin_a)

    # print('spin_a',spin_a)

    # --------------------
    # RAM proxy solution
    # --------------------

    ram_proxy = V[ram_index]

    C = np.cross(V, ram_proxy)

    # Handedness sign per spin sample
    sign = np.sign(C @ spin_guess)

    # Optional: drop degenerate cases
    mask = sign != 0
    C = C[mask]
    sign = sign[mask]

    # Apply sign
    C *= sign[:, None]

    mag = np.linalg.norm(C, axis=1)
    mask = mag > 0

    Csel = C[mask]
    mag_sel = mag[mask]

    normed = Csel / mag_sel[:, None]

    spin_b = np.average(normed, axis=0)
#    spin_a = (C[mask] / mag[mask][:, None]).mean(axis=0)
    spin_b /= np.linalg.norm(spin_b)

#    spin_b = (C[mask] / mag[mask][:, None]).mean(axis=0)
#    spin_b /= np.linalg.norm(spin_b)

    # --------------------
    # Enforce handedness
    # --------------------
    # print(spin_a)
    # print(spin_b)
    # print(spin_guess)

    if np.dot(spin_a, spin_b) < 0:
        spin_b = -spin_b

    spin_axis = 0.5*(spin_a + spin_b)
    spin_axis /= np.linalg.norm(spin_axis)

    # --------------------
    # Convert back to lat / lon
    # --------------------
    sx, sy, sz = spin_axis
    lat_spin = np.rad2deg(np.arcsin(sz))
    lon_spin = np.rad2deg(np.arctan2(sy, sx)) % 360.0

    # --------------------
    # Diagnostics
    # --------------------
    diagnostics = {
        "spin_a": spin_a,
        "spin_b": spin_b,
        "mean_dot_orthogonality": np.mean(np.abs(V @ spin_axis)),
        "std_dot_orthogonality": np.std(V @ spin_axis)
    }

    return spin_axis, lat_spin, lon_spin, diagnostics


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

    return parser.parse_args()

# main

args = argParsing()

#file = "/Users/hafijulislam/Library/CloudStorage/Box-Box/First_light_maps/DN/Instrument_FM1_playback_301_ILO_SCI_DE_dec_20251102T170018_DN.csv"

try:
    spice.furnsh('./imap_meta.tm')
    print("1S07 Kernels loaded successfully!")
except Exception as e:
    print(f"1S07 Error loading kernels: {e}")

try:
    inst_id = spice.bodn2c('IMAP')
    print(f"IMAP NAIF ID: {inst_id}")
except:
    print("IMAP name not found in the loaded kernels.")

epoch = datetime(2010, 1, 1, 0, 0, 0)

cdf = pycdf.CDF(args.file)

epoch = cdf['epoch'][:]
yr1  = epoch[0].year
doy1 = int(doy_fraction(epoch[0]) )
sdoy1 = f"{doy1:03d}"
date1 = f"{yr1}{sdoy1}"

# Average epoch time
avg_epoch = epoch[0] + (epoch[-1] - epoch[0]) / 2.0

# If you want the exact mean of all samples instead:
# import numpy as np
# avg_epoch = epoch[0] + sum((t - epoch[0] for t in epoch), timedelta(0)) / len(epoch)

# Convert to UTC string
utc_time = avg_epoch.strftime("%Y-%m-%d %H:%M:%S")
et = spice.str2et(utc_time)

print("1S07 Average epoch =", avg_epoch)
print("1S07 UTC time      =", utc_time)
print("1S017 Date1         =", date1)

print(f"\n1S07 Evaluating at UTC Date: {utc_time}")
print(f"1S07 Time since J2000 (et): {et} seconds")

#doubles_counts: CDF_INT2 [1, 7, 3600, 40] NRV
#end_spin_number: CDF_INT8 [1]
#epoch: CDF_TIME_TT2000 [1]
#esa_energy_step: CDF_INT8 [7] NRV
#esa_mode: CDF_INT8 [1]
#exposure_time: CDF_FLOAT [1, 7, 3600, 40] NRV
#h_background_rates: CDF_FLOAT [1, 7, 3600, 40]
#h_background_rates_stat_uncert: CDF_FLOAT [1, 7, 3600, 40]
#h_background_rates_sys_err: CDF_FLOAT [1, 7, 3600, 40]
#h_counts: CDF_INT2 [1, 7, 3600, 40] NRV
#hae_latitude: CDF_DOUBLE [1, 3600, 40]
#hae_longitude: CDF_DOUBLE [1, 3600, 40]
#o_background_rates: CDF_FLOAT [1, 7, 3600, 40]
#o_background_rates_stat_uncert: CDF_FLOAT [1, 7, 3600, 40]
#o_background_rates_sys_err: CDF_FLOAT [1, 7, 3600, 40]
#o_counts: CDF_INT2 [1, 7, 3600, 40] NRV
#off_angle: CDF_DOUBLE [40] NRV
#pivot_angle: CDF_DOUBLE [1] NRV
#pointing_end_met: CDF_DOUBLE [1]
#pointing_start_met: CDF_DOUBLE [1]
#sc_direction_vector: CDF_DOUBLE [3] NRV
#sc_velocity: CDF_DOUBLE [3] NRV
#spin_angle: CDF_DOUBLE [3600] NRV
#start_spin_number: CDF_INT8 [1]
#triples_counts: CDF_INT2 [1, 7, 3600, 40] NRV

# lon_sc2, lat_sc2 = earth_heliocentric_coords(epoch[0])
lat_sc3 = 0.0
lon_sc3 = earth_ecliptic_longitude(avg_epoch )

# print("lons = ", lon_sc2, lon_sc3)

spin_axis, lat_spin, lon_spin, lat_sc, lon_sc, diag =\
     compute_spin_axis_from_cdf_gen(cdf, lat_sc3, lon_sc3)

# Convert spin axis to equatorial/J2000-like lon/lat
lon_spin_eq, lat_spin_eq = convert_spin_to_J2000(lon_spin, lat_spin)

# Defaults in case SPICE call fails
lon_ephem_deg = np.nan
lat_ephem_deg = np.nan

try:
    position, light_time = spice.spkpos('IMAP', et, 'ECLIPJ2000', 'NONE', 'SUN')
    radius, lon_ephem, lat_ephem = spice.reclat(position)

    lon_ephem_deg = (lon_ephem * spice.dpr()) % 360.0
    lat_ephem_deg = lat_ephem * spice.dpr()

    print(f"1S07 IMAP Position relative to Sun in ECLIPJ2000:")
    print(f"  X (km): {position[0]:.2f}")
    print(f"  Y (km): {position[1]:.2f}")
    print(f"  Z (km): {position[2]:.2f}")
    print(f"  Radius (km): {radius:.2f}")
    print(f"  RA / Longitude (deg): {(lon_ephem * spice.dpr()) % 360:.2f}")
    print(f"  DEC / Latitude (deg): {lat_ephem * spice.dpr():.2f}")
except Exception as e:
    print(f"Error calculating IMAP position: {e}")


#print("Spin axis (HAE Cartesian):", spin_axis)
#print(f"Spin axis lat/lon: {lat_spin:.3f}°, {lon_spin:.3f}°")
# print("⟂ sanity check (mean |dot|):", diag["mean_dot_orthogonality"])
# print("rough solar direction", diag["solar_direction"])
# print("spin axis angle to Sun angle", diag["spin_angle"])

with open(f'output/imap_lo_position_{date1}.csv', 'w') as fle:

    print_coord(fle, date1, spin_axis, 
                lon_sc, lat_sc, lon_sc3, lat_sc3, 
                lon_ephem, lat_ephem, lon_spin, 
                lat_spin, lon_spin_eq, lat_spin_eq,
                diag["sc_position"], diag["sc_velocity"], diag["spin_angle"])
   
#fluxT = flux.T
#dflxT = dflx.T

    

