#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import argparse
from datetime import datetime
from spacepy import pycdf

# ----------------------------------------------------------------------
# TOF selection / calibration constants
# ----------------------------------------------------------------------

TOF3_L = [11.0, 7.0, 3.5, 0.0]
TOF3_H = [15.0, 11.0, 7.0, 3.5]

E_PEAK_H = [20.0, 10.0, 10.0]

H_PEAK_L = [20.0, 10.0, 10.0]
H_PEAK_H = [70.0, 50.0, 40.0]

CO_PEAK_L = [100.0, 60.0, 60.0]
CO_PEAK_H = [270.0, 150.0, 150.0]

# EU = C0 + C1 * ADC
ADC_TOF0 = [5.5252E-01,  1.6837E-01]
ADC_TOF1 = [-7.2018E-01, 1.6512E-01]
ADC_TOF2 = [3.7442E-01,  1.6641E-01]
ADC_TOF3 = [4.6726E-01,  1.7144E-01]

LEFT_SCI_BOUNDARY = 20

TICK_TO_SEC = 4.096e-3


# ----------------------------------------------------------------------
# Arguments
# ----------------------------------------------------------------------

def argParsing():
    parser = argparse.ArgumentParser(
        description="L1A direct-event reader using L1B-style ideas selections."
    )

    parser.add_argument(
        "-f", "--file",
        help="the L1A direct-event CDF file",
        dest="file",
        required=True
    )

    parser.add_argument(
        "-k", "--hkfile",
        help="the L1B housekeeping CDF file",
        dest="file_hk",
        required=True
    )

    parser.add_argument(
        "-g", "--goodtime_ideas_file",
        help="the goodtime ideas file",
        dest="goodtime_file",
        required=True
    )

    parser.add_argument(
        "-o", "--outputFile",
        help="output file base name",
        dest="outFile",
        required=True
    )

    return parser.parse_args()


def doy_fraction(t):
    start = datetime(t.year, 1, 1)
    return 1.0 + (t - start).total_seconds() / 86400.0


# ----------------------------------------------------------------------
# L1A reader that produces L1B-like event arrays
# ----------------------------------------------------------------------

def load_l1a_events_l1b_like(l1a_file, hk_file):
    cdf = pycdf.CDF(l1a_file)

    coincidence_type = cdf["coincidence_type"][:]
    mode             = cdf["mode"][:]
    de_time          = cdf["de_time"][:]
    esa_step         = cdf["esa_step"][:]

    tof0_raw = cdf["tof0"][:]
    tof1_raw = cdf["tof1"][:]
    tof2_raw = cdf["tof2"][:]
    tof3_raw = cdf["tof3"][:]
    cksm     = cdf["cksm"][:]

    shcoarse = np.asarray(cdf["shcoarse"][:])
    de_count = np.asarray(cdf["de_count"][:])

    cdf.close()

    if shcoarse.ndim != 1 or de_count.ndim != 1:
        raise ValueError(
            f"Expected 1D shcoarse/de_count arrays, got "
            f"shcoarse={shcoarse.shape}, de_count={de_count.shape}"
        )

    if len(shcoarse) != len(de_count):
        print(
            f"WARNING: shcoarse/de_count length mismatch: "
            f"{len(shcoarse)} vs {len(de_count)}"
        )
        n_packet = min(len(shcoarse), len(de_count))
        shcoarse = shcoarse[:n_packet]
        de_count = de_count[:n_packet]

    if np.any(de_count < 0):
        raise ValueError("de_count contains negative values")

    # Packet-level shcoarse expanded to event-level MET-like array
    met = np.repeat(shcoarse, de_count)

    n_event = min(
        len(met),
        len(coincidence_type),
        len(mode),
        len(de_time),
        len(esa_step),
        len(tof0_raw),
        len(tof1_raw),
        len(tof2_raw),
        len(tof3_raw),
        len(cksm)
    )

    if n_event != len(met):
        print(
            f"WARNING: L1A event alignment mismatch. "
            f"Expanded shcoarse={len(met)}, tof0={len(tof0_raw)}. "
            f"Truncating all arrays to {n_event}."
        )

    met              = met[:n_event]
    coincidence_type = coincidence_type[:n_event]
    mode             = mode[:n_event]
    de_time          = de_time[:n_event]
    esa_step         = esa_step[:n_event]

    tof0_raw = tof0_raw[:n_event]
    tof1_raw = tof1_raw[:n_event]
    tof2_raw = tof2_raw[:n_event]
    tof3_raw = tof3_raw[:n_event]
    cksm     = cksm[:n_event]

    print("L1A sanity check:")
    print("  expanded shcoarse events =", len(met))
    print("  tof0 events              =", len(tof0_raw))
    print("  de_time events           =", len(de_time))
    print("  first shcoarse           =", met[0] if len(met) else "NONE")
    print("  last  shcoarse           =", met[-1] if len(met) else "NONE")

    # ------------------------------------------------------------------
    # Reconstruct/calibrate TOFs
    # ------------------------------------------------------------------
    #
    # For mode == 1 golden triples, reconstruct TOF1 from checksum relation.
    # The raw L1A TOFs are ADC-like values and are converted to ns here.
    #

    tof1d = (
        tof0_raw
        + tof3_raw
        - tof2_raw
        - cksm
        + 2 * LEFT_SCI_BOUNDARY
    )

    tof0 = tof0_raw * ADC_TOF0[1] + ADC_TOF0[0]
    tof1 = tof1d    * ADC_TOF1[1] + ADC_TOF1[0]
    tof2 = tof2_raw * ADC_TOF2[1] + ADC_TOF2[0]
    tof3 = tof3_raw * ADC_TOF3[1] + ADC_TOF3[0]

    # Flight correction
    tof0 = tof0 + 0.5 * tof3
    tof1 = tof1 - 0.5 * tof3

    # ------------------------------------------------------------------
    # Compute spinbin from L1A de_time and HK spin period
    # ------------------------------------------------------------------

    cdf_hk = pycdf.CDF(hk_file)
    spin_period = cdf_hk["spin_period"][:]
    cdf_hk.close()

    spin_period_ave = np.nanmean(spin_period)
    print("L1A spin period average =", spin_period_ave)

    deg_per_sec = 360.0 / spin_period_ave

    nep_spinphase = de_time * TICK_TO_SEC * deg_per_sec + 60.0
    nep_spinphase %= 360.0

    spinbin = np.round(10.0 * nep_spinphase).astype(int) % 3600

    # L1B script used spinbin * 60 / 3600 to compare against 0..59 bins
    spinbin2 = (spinbin * 60 / 3600).astype(int)

    return {
        "met": met,
        "esa_step": esa_step,
        "spinbin": spinbin,
        "spinbin2": spinbin2,

        # L1B-equivalent names:
        # absent selection in ideas file maps to L1A coincidence_type
        # mode_bit selection in ideas file maps to L1A mode
        "absent": coincidence_type,
        "mode_bit": mode,

        "tof0": tof0,
        "tof1": tof1,
        "tof2": tof2,
        "tof3": tof3,
    }


# ----------------------------------------------------------------------
# Main filtering routine
# ----------------------------------------------------------------------

def filter_and_write_cdf(cdf_file, hk_file, goodtime_file, out_file):
    ev = load_l1a_events_l1b_like(cdf_file, hk_file)

    met      = ev["met"]
    esa_step = ev["esa_step"]
    spinbin  = ev["spinbin"]
    spinbin2 = ev["spinbin2"]
    absent   = ev["absent"]
    mode_bit = ev["mode_bit"]
    tof0     = ev["tof0"]
    tof1     = ev["tof1"]
    tof2     = ev["tof2"]
    tof3     = ev["tof3"]

    N = len(met)

    # ------------------------------------------------------------------
    # Load goodtime ideas CSV
    # ------------------------------------------------------------------

    df = pd.read_csv(
        goodtime_file,
        usecols=range(28),
        dtype=str
    )

    print(
        "1S12 goodtime selection: file=",
        goodtime_file,
        ", fields=",
        df.iloc[0].to_dict()
    )

    df.columns = [
        "date", "time_start", "time_end", "bin_start", "bin_end", "nbins_bin",
        "inst", "esa1", "esa2", "esa3", "esa4", "esa5", "esa6", "esa7",
        "absent", "mode", "tof0lo", "tof0hi", "tof0bins",
        "tof1lo", "tof1hi", "tof1bins",
        "tof2lo", "tof2hi", "tof2bins",
        "tof3lo", "tof3hi", "tof3bins"
    ]

    numeric_cols_int = [
        "date", "time_start", "time_end", "bin_start", "bin_end", "nbins_bin",
        "esa1", "esa2", "esa3", "esa4", "esa5", "esa6", "esa7",
        "absent", "mode",
        "tof0bins", "tof1bins", "tof2bins", "tof3bins"
    ]

    df[numeric_cols_int] = df[numeric_cols_int].astype(int)

    numeric_cols_float = [
        "tof0lo", "tof0hi",
        "tof1lo", "tof1hi",
        "tof2lo", "tof2hi",
        "tof3lo", "tof3hi"
    ]

    df[numeric_cols_float] = df[numeric_cols_float].astype(float)

    time_start = df["time_start"].to_numpy()
    time_end   = df["time_end"].to_numpy().copy()

    bin_start = df["bin_start"].to_numpy()
    bin_end   = df["bin_end"].to_numpy()

    esa_flags = df[
        ["esa1", "esa2", "esa3", "esa4", "esa5", "esa6", "esa7"]
    ].to_numpy()

    absent_select = df["absent"].to_numpy()
    mode_select   = df["mode"].to_numpy()

    tof0_start = df["tof0lo"].to_numpy()
    tof0_end   = df["tof0hi"].to_numpy()

    tof1_start = df["tof1lo"].to_numpy()
    tof1_end   = df["tof1hi"].to_numpy()

    tof2_start = df["tof2lo"].to_numpy()
    tof2_end   = df["tof2hi"].to_numpy()

    tof3_start = df["tof3lo"].to_numpy()
    tof3_end   = df["tof3hi"].to_numpy()

    ngoodt = len(time_end)
    time_end_copy = time_end.copy()

    print("Number of goodtime idea rows =", ngoodt)
    print("Number of L1A events         =", N)

    # ------------------------------------------------------------------
    # Write one output file per ESA
    # ------------------------------------------------------------------

    ntot = 0

    for esa in range(1, 8):
        outfile_esa = f"{out_file}_ESA{esa}.csv"

        with open(outfile_esa, "w") as fle:
            print(
                "met,tof3,tof2,tof1,tof0,absent,mode_bit,spinbin,esa_step",
                file=fle
            )

            esa_index = esa - 1

            # Reset time_end for this ESA
            time_end[:] = time_end_copy[:]

            # Disable goodtime rows where this ESA flag is zero
            for itime in range(ngoodt):
                if esa_flags[itime, esa_index] == 0:
                    time_end[itime] = time_start[itime] - 1

            # ----------------------------------------------------------
            # Vectorized mask calculations
            # ----------------------------------------------------------

            met_check = (
                (met[:, None] >= time_start[None, :])
                &
                (met[:, None] <= time_end[None, :])
            )

            spin_check = (
                (spinbin2[:, None] >= bin_start[None, :])
                &
                (spinbin2[:, None] <= bin_end[None, :])
            )

            esa_check = esa_step[:, None] == esa

            absent_check = absent[:, None] == absent_select[None, :]

            mode_check = mode_bit[:, None] == mode_select[None, :]

            tof0_check = (tof0_start[None, :] > 999) | (
                (tof0[:, None] >= tof0_start[None, :])
                &
                (tof0[:, None] <= tof0_end[None, :])
            )

            tof1_check = (tof1_start[None, :] > 999) | (
                (tof1[:, None] >= tof1_start[None, :])
                &
                (tof1[:, None] <= tof1_end[None, :])
            )

            tof2_check = (tof2_start[None, :] > 999) | (
                (tof2[:, None] >= tof2_start[None, :])
                &
                (tof2[:, None] <= tof2_end[None, :])
            )

            tof3_check = (tof3_start[None, :] > 999) | (
                (tof3[:, None] >= tof3_start[None, :])
                &
                (tof3[:, None] <= tof3_end[None, :])
            )

            event_pass = (
                met_check
                &
                spin_check
                &
                esa_check
                &
                absent_check
                &
                mode_check
                &
                tof0_check
                &
                tof1_check
                &
                tof2_check
                &
                tof3_check
            )

            mask = np.any(event_pass, axis=1)

            # ----------------------------------------------------------
            # Optional diagnostic: first-event offsets per goodtime
            # ----------------------------------------------------------

            pair_check = met_check & esa_check

            offset_start = met[:, None] - time_start[None, :]
            offset_good = np.where(pair_check, offset_start, np.nan)

            has_event_per_goodtime = np.any(pair_check, axis=0)

            min_offset_per_goodtime = np.full(ngoodt, np.nan)

            if np.any(has_event_per_goodtime):
                min_offset_per_goodtime[has_event_per_goodtime] = np.nanmin(
                    offset_good[:, has_event_per_goodtime],
                    axis=0
                )

                good_min_offsets = min_offset_per_goodtime[has_event_per_goodtime]

                print("minimum offset per goodtime interval for ESA:", esa)
                print("  N goodtimes:", good_min_offsets.size)
                print("  min   :", np.min(good_min_offsets))
                print("  max   :", np.max(good_min_offsets))
                print("  median:", np.median(good_min_offsets))
                print("  mean  :", np.mean(good_min_offsets))
                print("  std   :", np.std(good_min_offsets))
            else:
                print("No goodtime intervals had events for ESA:", esa)

            # ----------------------------------------------------------
            # Filter arrays and write
            # ----------------------------------------------------------

            filtered = {
                "met": met[mask],
                "tof3": tof3[mask],
                "tof2": tof2[mask],
                "tof1": tof1[mask],
                "tof0": tof0[mask],
                "absent": absent[mask],
                "mode_bit": mode_bit[mask],
                "spinbin": spinbin[mask],
                "esa_step": esa_step[mask],
            }

            n = len(filtered["met"])

            if n > 0:
                for row in zip(
                    filtered["met"],
                    filtered["tof3"],
                    filtered["tof2"],
                    filtered["tof1"],
                    filtered["tof0"],
                    filtered["absent"],
                    filtered["mode_bit"],
                    filtered["spinbin"],
                    filtered["esa_step"],
                ):
                    print(",".join(map(str, row)), file=fle)

            ntot += mask.sum()

            print(
                f"ESA = {esa}, Filtered {mask.sum()} / {N} rows "
                f"written to {outfile_esa}"
            )

    print("Total selected L1A events =", ntot)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

args = argParsing()

filter_and_write_cdf(
    cdf_file=args.file,
    hk_file=args.file_hk,
    goodtime_file=args.goodtime_file,
    out_file=args.outFile
)