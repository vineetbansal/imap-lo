#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 09:55:18 2026

@author: hafijulislam
"""

import spiceypy as spice

# Load everything listed in your meta-kernel
try:
    spice.furnsh('imap_meta.tm')
    print("Kernels loaded successfully!")
except Exception as e:
    print(f"Error loading kernels: {e}")

# Example: Check the IMAP-Lo instrument ID
# Note: IMAP NAIF IDs usually follow the pattern (Spacecraft ID * 1000) - Instrument No.
# For IMAP, the spacecraft ID is -130
try:
    inst_id = spice.bodn2c('IMAP')
    print(f"IMAP NAIF ID: {inst_id}")
except:
    print("IMAP name not found in the loaded kernels.")
    
# 1. Provide a human-readable UTC Time string
utc_time = "2025-10-15" 

# `str2et` converts the UTC string into Ephemeris Time (ET), 
# which is the number of seconds since the J2000 epoch.
et = spice.str2et(utc_time)

print(f"\nEvaluating at UTC Date: {utc_time}")
print(f"Time since J2000 (et): {et} seconds")

# 2. Get Position of Earth (399) relative to the SUN (10) as RA/DEC in ECLIPJ2000
try:
    position, light_time = spice.spkpos('EARTH', et, 'ECLIPJ2000', 'NONE', 'SUN')
    radius, lon, lat = spice.reclat(position)
    print(f"EARTH Position relative to Sun in ECLIPJ2000:")
    print(f"  X (km): {position[0]:.2f}")
    print(f"  Y (km): {position[1]:.2f}")
    print(f"  Z (km): {position[2]:.2f}")
    print(f"  Radius (km): {radius:.2f}")
    print(f"  RA / Longitude (deg): {(lon * spice.dpr()) % 360:.2f}")
    print(f"  DEC / Latitude (deg): {lat * spice.dpr():.2f}")
except Exception as e:
    print(f"Error calculating EARTH position: {e}")

# 3. Get Position of L1 Lagrange Point (NAIF ID: 391) relative to the SUN
print("\nAttempting to get L1 Lagrange point position (as a proxy for IMAP)...")
try:
    position, light_time = spice.spkpos('391', et, 'ECLIPJ2000', 'NONE', 'SUN')
    radius, lon, lat = spice.reclat(position)
    print(f"L1 Position relative to Sun in ECLIPJ2000:")
    print(f"  X (km): {position[0]:.2f}")
    print(f"  Y (km): {position[1]:.2f}")
    print(f"  Z (km): {position[2]:.2f}")
    print(f"  Radius (km): {radius:.2f}")
    print(f"  RA / Longitude (deg): {(lon * spice.dpr()) % 360:.2f}")
    print(f"  DEC / Latitude (deg): {lat * spice.dpr():.2f}")
except Exception as e:
    print(f"Failed to calculate L1 position.")
    print(f"Details: {e}")


# 3. Get Position of L1 Lagrange Point (NAIF ID: 391) relative to the SUN
print("\nAttempting to get IMAP position ...")
try:
    position, light_time = spice.spkpos('IMAP', et, 'ECLIPJ2000', 'NONE', 'SUN')
    radius, lon, lat = spice.reclat(position)
    print(f"IMAP Position relative to Sun in ECLIPJ2000:")
    print(f"  X (km): {position[0]:.2f}")
    print(f"  Y (km): {position[1]:.2f}")
    print(f"  Z (km): {position[2]:.2f}")
    print(f"  Radius (km): {radius:.2f}")
    print(f"  RA / Longitude (deg): {(lon * spice.dpr()) % 360:.2f}")
    print(f"  DEC / Latitude (deg): {lat * spice.dpr():.2f}")
except Exception as e:
    print(f"Failed to calculate IMAP position.")
    print(f"Details: {e}")

# Always clear the pool when done
spice.kclear()
