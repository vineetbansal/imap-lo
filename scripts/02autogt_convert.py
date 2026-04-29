import sys
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from spacepy import pycdf
from spacepy.time import Ticktock


BG_RATE_ANTI_RAM_OVERRIDE = {
    (2026, 62): 0.0014,
    (2026, 64): 0.0,
    (2026, 65): 0.0,
    (2026, 91): 0.03
}

HISTOGRAM_CYCLE_EPOCHS = 420

N_CYCLE_SUM = 1
N_CYCLE_AVE = 7
N_ESA_LEVELS = 7
RAM_ESA_LEVELS = (5, 6)
RAM_HISTOGRAM_BINS = (slice(0, 20), slice(50, 60))
ANTI_RAM_HISTOGRAM_BINS = slice(20, 50)

BG_RATE_HYDROGEN = 0.0014925
BG_RATE_OXYGEN = 0.000136635

BG_RATE_MULTIPLIER = {"H": 1.0, "O": 0.3}
BG_RATE_DIVIDER = {"H": 50.0, "O": 150.0}

THRESHOLD_BG_RATE_RAM_90 = 0.014
THRESHOLD_BG_RATE_ANTI_RAM_90 = 0.007
THRESHOLD_BG_RATE_RAM_NON_90 = 0.0175
THRESHOLD_BG_RATE_ANTI_RAM_NON_90 = 0.00875

DELAY_MAX = 100
PIVOT_90_RANGE = 88, 92
EXPOSURE_FACTOR = 0.5

# ---------------------------------------


def print_lines(fgt, fcn, date, begin1, end1, sum_bg_cnts, sum_og_cnts, sum_bg_expo,
                bg_rate_nom, pivot, pivotp):
    begin2 = begin1 - 2
    end2 = end1 + 2

    print(
        f"{date},{int(begin2)},{int(end2)},0,59,Lo,1,1,1,1,1,1,1,# auto goodtimes bg_rate_nom = {bg_rate_nom:.6f}",
        file=fgt
    )
    print(
        f"{date},{int(begin2)},{int(end2)},30,59,Lo,{sum_bg_cnts},{sum_og_cnts},{sum_bg_expo},{pivot},{pivotp}",
        file=fcn
    )


def print_lines_tof_ideas(fideas, date, begin1, end1, header: bool = False):
    begin2 = begin1 - 2
    end2 = end1 + 2

    if header:
        print(
            f"date,begin,end,bin0,bin1,nbins,Lo,ESA1,ESA2,ESA3,ESA4,ESA5,ESA6,ESA7,Absent, Mode,TOF0lo,TOF0hi,nbins,TOF1lo,TOF1hi,nbins,TOF2lo,TOF2hi,nbins,TOF3lo,TOF3hi,nbins",
            file=fideas
        )
    else:
        print(
            f"{date},{int(begin2)},{int(end2)},0,59,60,Lo,1,1,1,1,1,1,1,0,1, 20.0,270.0,100,10.0,150.0,100,10.0,150.0,100,0.0,15.0,20",
            file=fideas
        )


def print_lines_background(element, file_handle, date, begin1, end1, sum_bg_cnts,
                           sum_bg_expo, bg_rate_nom):

    if sum_bg_expo == 0:
        bg_rate = bg_rate_nom * BG_RATE_MULTIPLIER[element]
        sigma_bg_rate = bg_rate
    else:
        bg_rate = sum_bg_cnts / sum_bg_expo
        sigma_bg_rate = np.sqrt(sum_bg_cnts) / sum_bg_expo

    if bg_rate == 0.0:
        bg_rate = bg_rate_nom / BG_RATE_DIVIDER[element]
        sigma_bg_rate = bg_rate
    if sigma_bg_rate == 0.0:
        sigma_bg_rate = bg_rate

    begin2 = begin1 - 60 * 2
    end2 = end1 - 60 * 4.5

    print(
        f"{date},{int(begin2)},{int(end2)},0,59,Lo,{bg_rate:.7f},{bg_rate:.7f},{bg_rate:.7f},{bg_rate:.7f},{bg_rate:.7f},{bg_rate:.7f},{bg_rate:.7f},rate",
        file=file_handle
    )
    print(
        f"{date},{int(begin2)},{int(end2)},0,59,Lo,{sigma_bg_rate:.7f},{sigma_bg_rate:.7f},{sigma_bg_rate:.7f},{sigma_bg_rate:.7f},{sigma_bg_rate:.7f},{sigma_bg_rate:.7f},{sigma_bg_rate:.7f},sigma",
        file=file_handle
    )


def met_from_epoch(t):
    dt = t - datetime(2010, 1, 1, 0, 0, 0) 
    return dt.total_seconds() + 9 


def process(input_hist_cdf: Path, input_de_cdf: Path, input_hk_cdf: Path, output_dir: Path):

    output_dir.mkdir(parents=True, exist_ok=True)

    cdf = pycdf.CDF(str(input_hist_cdf))
    cdf_hk = pycdf.CDF(str(input_hk_cdf))

    try:
        pivotp = pycdf.CDF(str(input_de_cdf))['pivot_angle'][0]
    except:
        pivotp = 0.0


    try:
        epoch_hk = cdf_hk['epoch']
        tt = Ticktock(epoch_hk, 'CDF')
        times = np.array(tt.UTC)
        t0_hk = times[0]
        start_time_hk = t0_hk + timedelta(hours=3)
        end_time_hk = t0_hk + timedelta(hours=15)
        mask_hk = (times >= start_time_hk) & (times <= end_time_hk)
        pri = cdf_hk['pcc_coarse_pot_pri'][...]

        pivot1 = np.nanmedian(pri[mask_hk])
        pivot = pivot1
        if np.isnan(pivot):
            pivot = 90.0
    except:
        pivot = 90.0

    try:
        first_begin = met_from_epoch(cdf_hk['epoch'][0])
        last_end = met_from_epoch(cdf_hk['epoch'][-1])
    except:
        first_begin = met_from_epoch(cdf['epoch'][0])
        last_end = met_from_epoch(cdf['epoch'][-1])

    epoch = cdf['epoch'][:]
    epoch_start = epoch[0]

    if PIVOT_90_RANGE[0] < pivot < PIVOT_90_RANGE[1]:
        bg_rate_ram_nominal = THRESHOLD_BG_RATE_RAM_90
        bg_rate_anti_ram_nominal = THRESHOLD_BG_RATE_ANTI_RAM_90
    else:
        bg_rate_ram_nominal = THRESHOLD_BG_RATE_RAM_NON_90
        bg_rate_anti_ram_nominal = THRESHOLD_BG_RATE_ANTI_RAM_NON_90

    bg_rate_anti_ram_nominal = BG_RATE_ANTI_RAM_OVERRIDE.get((epoch_start.year, epoch_start.timetuple().tm_yday), bg_rate_anti_ram_nominal)

    interval_nom = HISTOGRAM_CYCLE_EPOCHS * N_CYCLE_SUM

    exposure = HISTOGRAM_CYCLE_EPOCHS * N_CYCLE_AVE * EXPOSURE_FACTOR
    exposure_ram = exposure * len(RAM_ESA_LEVELS) / N_ESA_LEVELS
    exposure_sum = HISTOGRAM_CYCLE_EPOCHS * N_CYCLE_SUM * EXPOSURE_FACTOR

    hydrogen_anti_ram_counts = np.sum(cdf['h_counts'][:, :, ANTI_RAM_HISTOGRAM_BINS], axis=(1, 2))
    oxygen_anti_ram_counts = np.sum(cdf['o_counts'][:, :, ANTI_RAM_HISTOGRAM_BINS], axis=(1, 2))

    ram_esa_slice = slice(RAM_ESA_LEVELS[0], RAM_ESA_LEVELS[-1] + 1)
    d_ram = sum(
        np.sum(cdf['h_counts'][:, ram_esa_slice, b], axis=(1, 2))
        for b in RAM_HISTOGRAM_BINS
    )

    ncycle = np.shape(hydrogen_anti_ram_counts)[0]

    begin = end = 0.0

    sum_bg_cnts = sum_og_cnts = 0.0
    sum_bg_expo = sum_bg1_expo = 0.0
    sum_bg_cnts_proxy = sum_og_cnts_proxy = 0.0

    date_str = f"{epoch_start.year}{epoch_start.timetuple().tm_yday:03d}"

    with open(f'{output_dir}/imap_lo_goodtimes_{date_str}.csv', 'w') as fgt, \
            open(f'{output_dir}/imap_lo_HO_cnts_expo_{date_str}.csv', 'w') as fcn, \
            open(f'{output_dir}/imap_lo_goodtimes_ideas_{date_str}.csv', 'w') as fideas:

        print_lines_tof_ideas(fideas, date_str, 0, 0, header=True)

        for i in range(0, ncycle, N_CYCLE_SUM):

            if i + N_CYCLE_SUM < ncycle:
                interval = met_from_epoch(epoch[i + N_CYCLE_SUM]) - met_from_epoch(epoch[i])
            else:
                interval = interval_nom

            if interval > (interval_nom + DELAY_MAX):

                if begin > 0.0:
                    end = met_from_epoch(epoch[i - 1])

                    print_lines(fgt, fcn, date_str, begin, end, sum_bg_cnts_proxy, sum_og_cnts_proxy,
                                sum_bg1_expo, bg_rate_anti_ram_nominal, pivot, pivotp)
                    print_lines_tof_ideas(fideas, date_str, begin, end, header=False)

                    begin = 0.0
                    end = 0.0

                continue

            delta_time = 0.0
            if i > 0:
                delta_time = met_from_epoch(epoch[i]) - (met_from_epoch(epoch[i - 1]) + HISTOGRAM_CYCLE_EPOCHS)

            if (delta_time > DELAY_MAX) and (begin > 0.0):
                end = met_from_epoch(epoch[i - 1])

                print_lines(fgt, fcn, date_str, begin, end, sum_bg_cnts_proxy, sum_og_cnts_proxy,
                            sum_bg1_expo, bg_rate_anti_ram_nominal, pivot, pivotp)
                print_lines_tof_ideas(fideas, date_str, begin, end, header=False)

                begin = 0.0
                end = 0.0

            window_avg_start = max(int(i - N_CYCLE_AVE // 2), 0)
            window_avg_end = min(ncycle, window_avg_start + N_CYCLE_AVE)
            if (window_avg_end - window_avg_start) < N_CYCLE_AVE:
                window_avg_start = max(window_avg_end - N_CYCLE_AVE, 0)

            window_sum_start = max(int(i - N_CYCLE_SUM // 2), 0)
            window_sum_end = min(ncycle, window_sum_start + N_CYCLE_SUM)
            if (window_sum_end - window_sum_start) < N_CYCLE_SUM:
                window_sum_start = max(window_avg_end - N_CYCLE_SUM, 0)

            ram_rate = np.sum(d_ram[window_avg_start:window_avg_end]) / exposure_ram
            anti_ram_rate = np.sum(hydrogen_anti_ram_counts[window_avg_start:window_avg_end]) / exposure

            if (ram_rate < bg_rate_ram_nominal) and (anti_ram_rate < bg_rate_anti_ram_nominal):

                if begin == 0.0:
                    begin = met_from_epoch(epoch[i])

                # actual background estimate for the bg file
                sum_bg_cnts += BG_RATE_HYDROGEN * exposure
                sum_og_cnts += BG_RATE_OXYGEN * exposure
                sum_bg_expo += exposure

                # proxy in the antiram hemisphere
                sum_bg_cnts_proxy += np.sum(hydrogen_anti_ram_counts[window_sum_start:window_sum_end])
                sum_og_cnts_proxy += np.sum(oxygen_anti_ram_counts[window_sum_start:window_sum_end])
                sum_bg1_expo += exposure_sum

            else:

                if begin > 0.0:
                    end = met_from_epoch(epoch[i - 1])

                    print_lines(fgt, fcn, date_str, begin, end, sum_bg_cnts_proxy, sum_og_cnts_proxy,
                                sum_bg1_expo, bg_rate_anti_ram_nominal, pivot, pivotp)
                    print_lines_tof_ideas(fideas, date_str, begin, end, header=False)

                    begin = 0.0
                    end = 0.0

        if (end == 0.) and (begin > 0.0):
            end = met_from_epoch(epoch[ncycle - 1])
            if end > begin:
                print_lines(fgt, fcn, date_str, begin, end, sum_bg_cnts_proxy, sum_og_cnts_proxy,
                            sum_bg1_expo, bg_rate_anti_ram_nominal, pivot, pivotp)
                print_lines_tof_ideas(fideas, date_str, begin, end, header=False)

    with open(f'{output_dir}/imap_lo_H_background_{date_str}.csv', 'w') as f:
        if last_end > first_begin:
            print_lines_background("H", f, date_str, first_begin, last_end, sum_bg_cnts,
                                   sum_bg_expo, bg_rate_anti_ram_nominal)

    with open(f'{output_dir}/imap_lo_O_background_{date_str}.csv', 'w') as f:
        if last_end > first_begin:
            print_lines_background("O", f, date_str, first_begin, last_end,
                                   sum_og_cnts, sum_bg_expo, bg_rate_anti_ram_nominal)


if __name__ == "__main__":
    process(
        Path(sys.argv[1]),
        Path(sys.argv[2]),
        Path(sys.argv[3]),
        Path(sys.argv[4]),
    )
