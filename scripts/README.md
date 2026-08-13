# IMAP Lo Good-Times Detection Algorithm

Implemented in `pipeline.genererate_goodtimes`.

1. **Load SPICE kernels** — furnish the leap-second (LSK) and spacecraft clock (SCLK) kernels required for epoch conversions.
2. **Read input CDFs**
   - L1B histogram CDF (`histrates`): epoch and per-element counts arrays (`h_counts`, etc.) indexed by `[epoch, esa_step, spin_bin_6]`.
   - L1B direct-events CDF (`de`): pivot angle (`pivot_de`) - not directly used by the algorithm.
   - Housekeeping CDF (`nhk`): coarse potential (`pcc_coarse_pot_pri`) used for actual pivot-angle determination.
3. **Fetch ancillary overrides** — query and download the `bg-rates-anti-ram-overrides` ancillary table from `imap_data_access`; these allow per-day manual corrections to the background-rate estimates.
4. **Delegate to `l1b_bgrates_and_goodtimes`** — the core algorithm (implemented in `imap_processing`) ingests the three datasets and ancillary files and returns:
   - `bgrates_ds`: per-element background rates (counts/s) keyed by element name (e.g. `H`, `O`).
   - `goodtimes_ds`: good-time intervals as MET start/end pairs, pivot angle, and pivot angle derived from direct events.

   ### Overview

   The algorithm is a threshold-based state machine that scans histogram cycles in time order, uses a 7-cycle rolling window to compute directional particle rates in two sky regions (RAM and anti-RAM), and marks intervals as "good" only when both rates are simultaneously below pivot-angle-dependent thresholds — broken by any gap or rate exceedance.

   ### Core Components

   #### 1. Pivot Angle Classification

   The instrument's pivot angle is read from housekeeping data (`pcc_coarse_pot_pri`) as the median over hours 3–15 of the observation day. This determines which cut-rate thresholds to apply:

   - **Near 90°** (88–92°): anti-RAM threshold = 0.007, RAM threshold = 0.014
   - **Non-90°**: anti-RAM = 0.00875, RAM = 0.0175

   An ancillary file can override the threshold for specific (year, day-of-year) combinations.

   #### 2. Histogram Region Definitions

   The algorithm partitions the 60-bin spatial histogram into two directional regions:

   - **Anti-RAM bins**: bins 20–50 — used for the primary good-time signal
   - **RAM bins**: bins 0–20 and 50–60, restricted to high ESA levels 6 & 7 — used as a secondary guard

   (Bins follow Python convention; range 0–20 includes bins 0–19.)

   #### 3. Sliding Window Rate Calculation

   Each histogram cycle is ~420 s (~7 min). For every cycle `i`, the algorithm computes rates using a **7-cycle averaging window**:

   ```
   antiram_rate = sum(H counts in anti-RAM bins, over window) / exposure
   ram_rate     = sum(H counts in RAM bins at high ESA, over window) / exposure_ram
   ```

   Exposure time is estimated as half of the viewing time of the viewing circle in the anti-RAM direction (~420 s × 0.5). RAM exposure time is 2/7 of the anti-RAM exposure time.

   #### 4. Good-Time State Machine

   The algorithm maintains a `begin`/`end` state:

   - **Opens** a good-time interval when **both** `antiram_rate < threshold` AND `ram_rate < ram_threshold`
   - **Closes** it (and emits output) when **either** rate exceeds its threshold
   - Also closes on **time gaps**: if consecutive cycles are more than ~100 s apart (`DELAY_MAX`, a configurable input argument), the open interval is closed and the gap cycle is skipped

   #### 5. Accumulation During Good Times

   While inside a good-time window, the algorithm accumulates two parallel sets of counts:

   - **Synthetic floor** for H and O respectively in the anti-RAM direction): uses known absolute H and O floor rates × exposure — used for output files.
   - **Proxy floor** : proxy exposure in the anti-RAM direction and H and O counts respectively.
5. **Write good-times CSV** — one row per good-time interval with columns `date`, `begin` (MET), `end` (MET), `pivot`, `pivot_de`.  File name: `imap_lo_goodtimes_<YYYYDDD>.csv`.
6. **Return** pivot angle, CSV path, and background-rate dict for downstream use.

---

# IMAP Lo Sky Map Generation Algorithm

Three sequential steps, implemented in `pipeline.filter_and_bin` → `pipeline.grid_and_calibrate` → `pipeline.write_soc`.

## Step 1 — Filter and bin (`filter_and_bin`)

1. **Derive spin-axis direction** — load one or more spacecraft quaternion CDFs (filtered to good-time intervals), apply each attitude quaternion to the body-frame z-axis `[0, 0, 1]` to get the spin-axis direction in ECLIPJ2000, average and normalise.  Result: mean spin-axis ecliptic longitude and latitude in degrees (ECLIPJ2000).
2. **Mask to good-time intervals** — convert CDF epoch (datetime) to MET seconds and keep only histogram records whose MET falls within at least one `[begin, end]` interval from the good-times CSV.
3. **Compute sky pointing** — all geometry is performed in ECLIPJ2000.  For each of 60 spin-angle bins (bin centres 3°, 9°, …, 357°, 6° wide), trace the boresight cone (half-angle = pivot angle) around the spin axis.  The perpendicular plane is anchored to the North Ecliptic Pole — which is exactly `[0, 0, 1]` in ECLIPJ2000 — so that spin-angle 0° points toward the NEP; the orthogonal axis points toward the ram direction.  Each bin's ECLIPJ2000 Cartesian direction is converted to ecliptic longitude/latitude via `cartesian_to_spherical`.
4. **Accumulate counts and exposure** — for each ESA level, sum `h_counts` and `exposure_time_6deg` over the good-time-masked records.  Roll the 60-bin array by `NEP_ROLL` (a fixed offset derived from the Lo instrument spin-phase offset) so that RAM bins (0–29, 0–180°) and anti-RAM bins (30–59, 180–360°) are contiguous.
5. **Write `map.csv`** — one row per (ESA level × spin-angle bin) with columns `esa_level`, `bins`, `ecl_lon`, `ecl_lat`, `counts`, `expo`, `spin_ra`, `spin_dec`.

## Step 2 — Grid and calibrate (`grid_and_calibrate`)

1. **Project onto sky grid** — map the 60 spin-angle bins onto a 30 × 60 ecliptic grid (30 colatitude bins × 60 longitude bins, 6° each) by converting ecliptic lon/lat to integer grid indices.  Counts and exposure accumulate additively for bins that share a pixel.
2. **Compute per-pixel quantities** (only for pixels with non-zero exposure):

   | Column | Formula |
   |--------|---------|
   | `cnts` | raw counts |
   | `expo` | exposure time (s) |
   | `rate` | `cnts / expo` |
   | `rvar` | `rate / expo` (Poisson variance) |
   | `flux` | `rate / (G × E)` where G = geometric factor, E = ESA energy (keV) |
   | `fvar` | `flux² / cnts` (Poisson flux variance) |
   | `fser` | `rate × ΔG / (G² × E)` (systematic from geo-factor uncertainty) |
   | `fvto` | `fvar + fser²` (total flux variance) |
   | `brate` | hydrogen background rate (counts/s) |
   | `bvar` | `brate / expo` |
   | `bflux` | `brate / (G × E)` |
   | `bfvar` | `bvar / (G × E)²` |
   | `stbg` | `rate / brate` (signal-to-noise ratio) |
   | `svar` | propagated variance of `stbg` |

3. **Write per-quantity CSVs** — one 30 × 60 CSV per (ESA level × quantity): `map_esa-{level}_{quantity}.csv`.

## Step 3 — Write SOC files (`write_soc`)

Convert each calibration CSV to a SOC-compatible `.txt` file: a structured comment header encodes axis ranges, title, units, frame metadata (ECLIPJ2000 sky frame, J2000 position frame), and instrument geometry constants, followed by tab-separated rows of values in scientific notation.