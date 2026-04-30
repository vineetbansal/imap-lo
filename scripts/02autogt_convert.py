import sys
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from spacepy import pycdf
from spacepy.time import Ticktock


ELEMS = ("H", "O")  # Ion species tracked

# Hours into the day (UTC) for HK data to calculate median for pivot angle estimation.
PIVOT_HK_HOUR_RANGE: tuple[int, int] = (3, 15)

# Per-day overrides for the anti-RAM background rate. Keyed by (year, day-of-year)
BG_RATE_ANTI_RAM_OVERRIDES: dict[tuple[int, int], float] = {
    (2026, 62): 0.0014,
    (2026, 64): 0.0,
    (2026, 65): 0.0,
    (2026, 91): 0.03
}

HISTOGRAM_CYCLE_EPOCHS: int = 420  # One histogram accumulation cycle duration [s]

N_CYCLE_SUM: int = 1   # Granularity of goodtime boundaries
N_CYCLE_AVE: int = 7   # Cycles to average over when estimating background rates
N_ESA_LEVELS: int = 7  # Total number of ESA levels
RAM_ESA_LEVELS: tuple[int, ...] = (6, 7)  # ESA levels for RAM estimation (1-indexed)

# Histogram angular bins (0-indexed) corresponding to the RAM and anti-RAM look directions
RAM_HISTOGRAM_BINS: tuple[slice, ...] = (slice(0, 20), slice(50, 60))
ANTI_RAM_HISTOGRAM_BINS: tuple[slice, ...] = (slice(20, 50),)

# Nominal background rates [counts/s] for each species
BG_RATES = {"H": 0.0014925, "O": 0.000136635}
# When no exposure is available, scale the nominal rate down as a conservative estimate
BG_RATE_FALLBACK_SCALE: dict[str, float] = {"H": 1.0, "O": 0.3}
# Minimum non-zero background rate floor = nominal / divisor
BG_RATE_FLOOR_DIVISOR: dict[str, float] = {"H": 50.0, "O": 150.0}

# Maximum acceptable background count rates [counts/s] for classifying a cycle as a "good time".
# Separate thresholds for RAM vs. anti-RAM, and for pivot near 90 deg vs. others
THRESHOLD_BG_RATE_RAM_90: float = 0.014
THRESHOLD_BG_RATE_ANTI_RAM_90: float = 0.007
THRESHOLD_BG_RATE_RAM_NON_90: float = 0.0175
THRESHOLD_BG_RATE_ANTI_RAM_NON_90: float = 0.00875

# Maximum time gap [s] between consecutive histogram epochs before treating them as
# separate intervals.
DELAY_MAX: int = 100
# Pivot angles within this range [degrees] are treated as "near 90".
PIVOT_90_RANGE: tuple[float, float] = 88., 92.
# Fraction of each cycle duration that contributes actual exposure.
EXPOSURE_FACTOR: float = 0.5


def save_bg_file(element, file_name, date, begin, end, synthetic_floor, goodtime_exposure_avg, bg_rate_anti_ram_nominal):
    """Write a per-element background-rate CSV for one day.

    Args:
        element: Ion species label (e.g. "H" or "O").
        file_name: Output CSV path.
        date: Day label string (YYYYDDD) written into the CSV.
        begin: MET of the first HK epoch for the day [s].
        end: MET of the last HK epoch for the day [s].
        synthetic_floor: Total model-predicted background counts accumulated over good times.
        goodtime_exposure_avg: Total exposure [s] accumulated over good-time intervals.
        bg_rate_anti_ram_nominal: Nominal anti-RAM threshold rate used as fallback.
    """
    if goodtime_exposure_avg == 0:
        # No good-time exposure accumulated; fall back to a scaled nominal rate.
        bg_rate = bg_rate_anti_ram_nominal * BG_RATE_FALLBACK_SCALE[element]
        sigma_bg_rate = bg_rate
    else:
        bg_rate = synthetic_floor / goodtime_exposure_avg
        sigma_bg_rate = np.sqrt(synthetic_floor) / goodtime_exposure_avg

    if bg_rate == 0.0:
        bg_rate = bg_rate_anti_ram_nominal / BG_RATE_FLOOR_DIVISOR[element]
        sigma_bg_rate = bg_rate
    if sigma_bg_rate == 0.0:
        sigma_bg_rate = bg_rate

    series = pd.Series({'date': date, 'begin': begin, 'end': end, 'bg_rate': bg_rate, 'bg_rate_sigma': sigma_bg_rate})
    series.to_frame().T.to_csv(file_name, header=True, index=False)


def _goodtime_row(date_str, begin, end, bg_rate_nom, proxy_floors, exposure_sum, pivot, pivot_de):
    # TODO: We're currently padding begin/end by 2 s to ensure complete cycles are covered at interval edges.
    return {
        'date': date_str, 'begin': int(begin - 2), 'end': int(end + 2),
        'bg_rate_nom': bg_rate_nom, 'sum_bg_cnts': proxy_floors['H'],
        'sum_og_cnts': proxy_floors['O'], 'sum_bg_expo': exposure_sum,
        'pivot': pivot, 'pivot_de': pivot_de
    }


def met_from_epoch(t: datetime):
    dt = t - datetime(2010, 1, 1, 0, 0, 0)
    return dt.total_seconds() + 9


def process(input_hist_cdf: Path, input_de_cdf: Path, input_hk_cdf: Path, output_dir: Path) -> None:
    """Identify good-time intervals and background rates for one day of Lo data.

    Reads histogram counts from the L1B histogram CDF, pivot angle from the DE CDF,
    and HK telemetry from the HK CDF.  Walks the histogram epochs in N_CYCLE_SUM
    blocks, computing sliding-window RAM and anti-RAM count rates for H ions and
    comparing them against pivot-dependent thresholds to classify each block as a
    good time or not.  Consecutive good-time blocks are merged into intervals.

    Writes a background-rate CSV file per ion species tracked, and one good-times CSV
    listing all identified intervals with accumulated exposure and counts

    Args:
        input_hist_cdf: Path to the L1B histogram CDF file.
        input_de_cdf: Path to the direct-events CDF file.
        input_hk_cdf: Path to the housekeeping CDF file.
        output_dir: Directory where output CSVs are written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    with pycdf.CDF(str(input_de_cdf)) as cdf_de:
        pivot_de = cdf_de['pivot_angle'][0] if 'pivot_angle' in cdf_de else 0.0

    with pycdf.CDF(str(input_hk_cdf)) as cdf_hk:
        if "pcc_coarse_pot_pri" in cdf_hk:
            hk_epoch_utctimes = np.array(Ticktock(cdf_hk['epoch'], 'CDF').UTC)
            hk_epoch_utctime0 = hk_epoch_utctimes[0]
            start_time_hk = hk_epoch_utctime0 + timedelta(hours=PIVOT_HK_HOUR_RANGE[0])
            end_time_hk = hk_epoch_utctime0 + timedelta(hours=PIVOT_HK_HOUR_RANGE[1])

            coarse_pot_pri = cdf_hk['pcc_coarse_pot_pri'][...]
            pivot = np.nanmedian(coarse_pot_pri[(hk_epoch_utctimes >= start_time_hk) & (hk_epoch_utctimes <= end_time_hk)])
            if np.isnan(pivot):
                pivot = 90.0
        else:
            pivot = 90.0

        first_begin = met_from_epoch(cdf_hk['epoch'][0])
        last_end = met_from_epoch(cdf_hk['epoch'][-1])

    if last_end <= first_begin:
        return

    with pycdf.CDF(str(input_hist_cdf)) as cdf_hist:
        epoch = cdf_hist['epoch'][:]
        n_epochs = epoch.shape[0]
        epoch_start = epoch[0]
        date_str = f"{epoch_start.year}{epoch_start.timetuple().tm_yday:03d}"

        # Choose background rate thresholds based on pivot orientation.
        if PIVOT_90_RANGE[0] < pivot < PIVOT_90_RANGE[1]:
            bg_rate_ram_nominal = THRESHOLD_BG_RATE_RAM_90
            bg_rate_anti_ram_nominal = THRESHOLD_BG_RATE_ANTI_RAM_90
        else:
            bg_rate_ram_nominal = THRESHOLD_BG_RATE_RAM_NON_90
            bg_rate_anti_ram_nominal = THRESHOLD_BG_RATE_ANTI_RAM_NON_90

        # Manual overrides of the anti-RAM threshold for anomalous days.
        bg_rate_anti_ram_nominal = BG_RATE_ANTI_RAM_OVERRIDES.get((epoch_start.year, epoch_start.timetuple().tm_yday), bg_rate_anti_ram_nominal)

        ram_esa_indices = [i - 1 for i in RAM_ESA_LEVELS]  # Convert to 0-indexed

        # Sum histogram counts over the relevant angular bins for each species and
        # direction. RAM counts use only certain ESA steps; anti-RAM counts use all.
        elem_ram_counts = {}
        elem_anti_ram_counts = {}
        for elem in ELEMS:
            elem_counts = cdf_hist[f'{elem.lower()}_counts'][...]
            elem_ram_counts[elem] = sum(
                np.sum(elem_counts[:, ram_esa_indices, b], axis=(1, 2))
                for b in RAM_HISTOGRAM_BINS
            )
            elem_anti_ram_counts[elem] = sum(
                np.sum(elem_counts[:, :, b], axis=(1, 2))
                for b in ANTI_RAM_HISTOGRAM_BINS
            )

    # Pre-compute expected exposure times [s] for the averaging and summing windows.
    exposure = HISTOGRAM_CYCLE_EPOCHS * N_CYCLE_AVE * EXPOSURE_FACTOR
    exposure_ram = exposure * len(RAM_ESA_LEVELS) / N_ESA_LEVELS
    exposure_sum = HISTOGRAM_CYCLE_EPOCHS * N_CYCLE_SUM * EXPOSURE_FACTOR

    # Walk through histogram epochs one N_CYCLE_SUM block at a time.
    begin = end = 0.0
    interval = HISTOGRAM_CYCLE_EPOCHS * N_CYCLE_SUM
    synthetic_floors = {e: 0.0 for e in ELEMS}   # Accumulated model-predicted BG counts
    proxy_floors = {e: 0.0 for e in ELEMS}       # Accumulated measured anti-RAM counts (BG proxy)
    goodtime_exposure_avg = goodtime_exposure_sum = 0.0
    goodtime_rows = []

    for i in range(0, n_epochs, N_CYCLE_SUM):

        measured_interval = interval
        if i + N_CYCLE_SUM < n_epochs:
            measured_interval = met_from_epoch(epoch[i + N_CYCLE_SUM]) - met_from_epoch(epoch[i])

        if measured_interval > (interval + DELAY_MAX):

            if begin > 0.0:
                end = met_from_epoch(epoch[i - 1])
                goodtime_rows.append(_goodtime_row(date_str, begin, end, bg_rate_anti_ram_nominal, proxy_floors, goodtime_exposure_sum, pivot, pivot_de))
                begin = end = 0.0
            continue

        # A large gap (missing data) forces the current good-time interval to close.
        delta_time = 0.0
        if i > 0:
            delta_time = met_from_epoch(epoch[i]) - (met_from_epoch(epoch[i - 1]) + HISTOGRAM_CYCLE_EPOCHS)

        if (delta_time > DELAY_MAX) and (begin > 0.0):
            end = met_from_epoch(epoch[i - 1])
            goodtime_rows.append(_goodtime_row(date_str, begin, end, bg_rate_anti_ram_nominal, proxy_floors, goodtime_exposure_sum, pivot, pivot_de))
            begin = end = 0.0

        # Sliding window centered on epoch i for rate averaging
        window_avg_start = max(int(i - N_CYCLE_AVE // 2), 0)
        window_avg_end = min(n_epochs, window_avg_start + N_CYCLE_AVE)
        if (window_avg_end - window_avg_start) < N_CYCLE_AVE:
            window_avg_start = max(window_avg_end - N_CYCLE_AVE, 0)

        # Sliding window centered on epoch i for accumulating counts
        window_sum_start = max(int(i - N_CYCLE_SUM // 2), 0)
        window_sum_end = min(n_epochs, window_sum_start + N_CYCLE_SUM)
        if (window_sum_end - window_sum_start) < N_CYCLE_SUM:
            window_sum_start = max(window_avg_end - N_CYCLE_SUM, 0)

        # Estimate background rates from the averaged H counts
        ram_rate = np.sum(elem_ram_counts['H'][window_avg_start:window_avg_end]) / exposure_ram
        anti_ram_rate = np.sum(elem_anti_ram_counts['H'][window_avg_start:window_avg_end]) / exposure

        # good-time = intervals where background rates are below threshold
        if (ram_rate < bg_rate_ram_nominal) and (anti_ram_rate < bg_rate_anti_ram_nominal):
            if begin == 0.0:
                begin = met_from_epoch(epoch[i])  # Start a new good-time interval

            for elem in ELEMS:
                synthetic_floors[elem] += BG_RATES[elem] * exposure
                proxy_floors[elem] += np.sum(
                    elem_anti_ram_counts['H'][window_sum_start:window_sum_end])

            goodtime_exposure_avg += exposure
            goodtime_exposure_sum += exposure_sum

        elif begin > 0.0:
            # Background exceeded threshold; Close the current good-time interval.
            end = met_from_epoch(epoch[i - 1])
            goodtime_rows.append(_goodtime_row(date_str, begin, end, bg_rate_anti_ram_nominal, proxy_floors, goodtime_exposure_sum, pivot, pivot_de))
            begin = end = 0.0

    if (end == 0.) and (begin > 0.0):
        end = met_from_epoch(epoch[n_epochs - 1])
        if end > begin:
            goodtime_rows.append(_goodtime_row(date_str, begin, end, bg_rate_anti_ram_nominal, proxy_floors, goodtime_exposure_sum, pivot, pivot_de))

    pd.DataFrame(goodtime_rows).to_csv(f'{output_dir}/imap_lo_goodtimes_{date_str}.csv', header=True, index=False)

    for elem in ELEMS:
        save_bg_file(elem, f'{output_dir}/imap_lo_{elem}_background_{date_str}.csv', date_str, first_begin, last_end, synthetic_floors[elem], goodtime_exposure_avg, bg_rate_anti_ram_nominal)


if __name__ == "__main__":
    input_hist_cdf, input_de_cdf, input_hk_cdf, output_dir = sys.argv[1:]
    process(Path(input_hist_cdf), Path(input_de_cdf), Path(input_hk_cdf), Path(output_dir))
