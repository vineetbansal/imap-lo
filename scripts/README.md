# IMAP Lo Good-Times Detection Algorithm

Documentation for `02autogt_convert.py`, which identifies "good time" intervals from IMAP Lo histogram data.

## Overview

The algorithm is a threshold-based state machine that scans histogram cycles in time order, uses a 7-cycle rolling window to compute directional particle rates in two sky regions (RAM and anti-RAM), and marks intervals as "good" only when both rates are simultaneously below pivot-angle-dependent thresholds — broken by any gap or rate exceedance.

## Core Components

### 1. Pivot Angle Classification

The instrument's pivot angle is read from housekeeping data (`pcc_coarse_pot_pri`) as the median over hours 3–15 of the observation day. This determines which cut-rate (ram and anti-ram rate) thresholds to apply:

- **Near 90°** (88–92°): anti-RAM threshold = 0.007, RAM threshold = 0.014
- **Non-90°**: anti-RAM = 0.00875, RAM = 0.0175

A hardcoded `CUT_MAP` can override the threshold for specific (year, day-of-year) combinations.

### 2. Histogram Region Definitions

The algorithm partitions the 60-bin spatial histogram into two directional regions:

- **Anti-RAM bins**: bins 20–50 — used for the primary good-time signal
- **RAM bins**: bins 0–20 and 50–60, restricted to high ESA levels 6 & 7 — used as a secondary guard

(bins follow python convention and range from 0-20 actually include bins 0-19).

### 3. Sliding Window Rate Calculation

Each histogram cycle is ~420s (~7 min). For every cycle `i`, the algorithm computes rates using a **7-cycle averaging window**:

```
antiram_rate = sum(H counts in anti-RAM bins, over window) / exposure
ram_rate     = sum(H counts in RAM bins at high ESA, over window) / exposure_ram
```

Exposure time is estimated as half of the viewing time of viewing circle in the anti-ram direction. This corresponds to ~420s x 0.5. Ram exposure time is 2/7 of the anti-ram exposure time.

### 4. Good-Time State Machine

The algorithm maintains a `begin`/`end` state:

- **Opens** a good-time interval when **both** `antiram_rate < threshold` AND `ram_rate < ram_threshold`
- **Closes** it (and emits output) when **either** rate exceeds its threshold
- Also closes on **time gaps**: if consecutive cycles are more than ~100 s apart (`DELAY_MAX`) (this is an input argument to the script and may be changed), the open interval is closed and the gap cycle is skipped

### 5. Accumulation During Good Times

While inside a good-time window, the algorithm accumulates two parallel sets of rates and/or counts:

- **Synthetic floor** (bg (`sum_bg_cnts, og_cnts` for H, O respectively in the anti-ram direction): uses known absolute H, O floor rates × exposure — used for the output files.
- **Proxy floor** (`sum_bg1_cnts, og1_cnts`): proxy exposure in the anti-RAM direction and H and O counts respectively.

### 6. Output Files

For each day, four files are written to the output directory:

| File | Content |
|------|---------|
| `imap_lo_goodtimes_*.csv` | MET begin/end timestamps of good intervals |
| `imap_lo_HO_cnts_expo_*.csv` | H/O count and exposure accumulations per interval |
| `imap_lo_goodtimes_ideas_*.csv` | TOF peak window parameters for downstream analysis |
| `imap_lo_H/O_background_*.csv` | Background rate and sigma estimates for H and O |

## Usage

```bash
python 02autogt_convert.py <hist_cdf> <de_cdf> <hk_cdf> <output_dir>
```

Where:
- `hist_cdf` — L1B histogram CDF file
- `de_cdf` — L1B direct-events CDF file
- `hk_cdf` — housekeeping CDF file
- `output_dir` — directory where output CSV files are written

---

# IMAP Lo Sky Map Generation Algorithm

Documentation for `07maps_from_goodtimes.py`, which converts good-time-filtered histogram data into calibrated sky maps in ecliptic coordinates.

## Overview

The script runs in three sequential stages:

1. **`process1`** — masks histogram records to good-time intervals, computes the ecliptic sky pointing of each spin-angle bin from quaternion attitude data, and accumulates counts and exposure per bin into a flat CSV.
2. **`process2`** — bins the accumulated data onto a (30 colatitude × 60 longitude) ecliptic sky grid, applies the geometric factor and energy calibration, and writes one CSV per quantity per (pivot angle, ESA level) combination.
3. **`process3`** — reformats the per-quantity CSVs into SOC-compatible `.txt` files with a structured header.

## Core Components

### 1. Spin Axis Determination (`calculate_spin_angles`)

Quaternion CDF files (one or more, covering the observation window) are loaded and merged. Each quaternion rotates the spacecraft body frame into ECLIPJ2000. Applying every quaternion to the body-frame spin-axis vector `[0, 0, 1]` yields a set of spin-axis directions in ECLIPJ2000; these are averaged and normalised to obtain the mean spin axis. A fixed frame rotation (no SPICE kernels required) then converts the result from ECLIPJ2000 to J2000, giving the spin axis as an equatorial (RA, Dec) pair used in all subsequent pointing calculations.

### 2. Sky Pointing per Spin-Angle Bin (`create_ra_dec`)

For a given spin-axis direction and pivot angle the instrument sweeps a cone in the sky. The 360° rotation is divided into 60 bins of 6° each (bin centres at 3°, 9°, …, 357°).

A right-handed frame is built in the plane perpendicular to the spin axis:
- **NEP axis** — the North Ecliptic Pole projected onto the spin-perpendicular plane (spin angle 0° points here).
- **RAM axis** — the cross product of the spin axis and the NEP axis (completes the right-handed frame).

For each bin centre the 3D pointing direction is:

```
d = cos(pivot) * spin_axis
  + sin(pivot) * cos(spin_angle) * nep_axis
  + sin(pivot) * sin(spin_angle) * ram_axis
```

The result is converted from equatorial Cartesian to ecliptic longitude/latitude using the J2000 obliquity (23.439°). The function returns one (ecl_lon, ecl_lat) pair per bin.

### 3. Stage 1 — Good-Time Masking and Bin Accumulation (`process1`)

CDF epoch timestamps are converted to Mission Elapsed Time (MET) seconds relative to 2010-01-01. Each record is tested against the begin/end pairs in the good-times CSV; only records that fall inside at least one interval are kept.

Sky pointing is computed once per pivot angle (default: 75°, 90°, 105°) using the mean spin axis from the quaternion files.

For each ESA level (1–7):

- `h_counts` and `exposure_time_6deg` are summed over the good-time-masked records for each of the 60 spin-angle bins.
- The arrays are **rolled by `NEP_ROLL = 10`** (the width of the trailing RAM chunk, bins 50–59), shifting those bins to the front. After rolling, bins 0–29 cover the RAM hemisphere (0–180° spin angle) and bins 30–59 cover the anti-RAM hemisphere (180–360°), forming a contiguous NEP-frame layout.

All ESA levels and pivot angles are stacked into a single `map.csv` with columns `esa_level`, `pivot_angle`, `bins`, `ecl_lon`, `ecl_lat`, `counts`, `expo`, `spin_ra`, `spin_dec`.

### 4. Stage 2 — Sky Grid Projection and Calibration (`process2`)

`map.csv` is split by (pivot angle, ESA level). For each subset the 60 spin-angle bins are projected onto a **30 × 60 ecliptic grid** (30 colatitude × 60 longitude bins, each 6° × 6°):

```
imap = int(ecl_lon * 60 / 360)   # longitude bin 0–59
jmap = int((90 + ecl_lat) * 30 / 180)   # colatitude bin 0–29
```

Counts and exposure accumulate additively when multiple spin-angle bins map to the same sky pixel.

For each sky pixel with non-zero exposure the following quantities are computed, where `G` = geometric factor, `E` = ESA energy, `dG` = geometric factor uncertainty, and `B` = background rate from the H-background CSV:

| Quantity | Formula |
|----------|---------|
| `rate` | counts / expo |
| `flux` | rate / (G × E) |
| `rvar` | rate / expo  *(Poisson variance)* |
| `fvar` | flux² / counts  *(statistical flux variance)* |
| `fser` | rate × dG / (G² × E)  *(systematic flux error from G uncertainty)* |
| `fvto` | fvar + fser²  *(total flux variance)* |
| `brate` | B |
| `bvar` | B / expo |
| `bflux` | B / (G × E) |
| `bfvar` | bvar / (G × E)²  |
| `stbg` | rate / B  *(signal-to-background ratio)* |
| `svar` | rvar / B² + bvar / rate²  *(propagated S/B variance)* |
| `expo` | accumulated exposure (s) |
| `cnts` | accumulated counts |

One CSV is written per (pivot angle, ESA level, quantity) — 14 quantities × 3 pivot angles × 7 ESA levels = up to 294 files.

### 5. Stage 3 — SOC Text Format Export (`process3`)

Each per-quantity CSV (30 × 60 matrix) is converted to a `.txt` file with a structured comment header followed by tab-separated rows of scientific-notation values. The header encodes axis ranges, title, units, frame metadata (ECLIPJ2000 sky frame, J2000 position frame), and instrument geometry constants used by downstream SOC tools.

## Output Files

### `process1`

| File | Content |
|------|---------|
| `map.csv` | Flat table of counts and exposure per (esa_level, pivot_angle, spin-angle bin) with ecliptic pointing coordinates |

### `process2`

Files named `map_pivot-{angle}_esa-{level}_{quantity}.csv`, one per combination. Each is a 30-row × 60-column matrix on the ecliptic colatitude/longitude grid.

### `process3`

Files named `map_pivot-{angle}_esa-{level}_{quantity}.txt` — SOC-format versions of the `process2` CSVs with a structured header block.

## Usage

```bash
python 07maps_from_goodtimes.py
```

The script is currently configured via hardcoded paths in the `__main__` block:

```python
input_hist_cdf   = "<L1B histogram CDF>"
goodtime_file    = "<imap_lo_goodtimes_*.csv from 02autogt_convert.py>"
quaternion_files = ["<spacecraft quaternion L1A CDF>", ...]
output_dir       = "<directory for map.csv>"
```

`process2` then reads `output_dir/map.csv` and the H-background CSV produced by `02autogt_convert.py`, writing per-quantity CSVs to `output_dir/maps/`. `process3` converts those CSVs to SOC `.txt` format in `output_dir/soc/`.
