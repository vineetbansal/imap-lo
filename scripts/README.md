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

Each histogram cycle is 420s (=7 min). For every cycle `i`, the algorithm computes rates using a **7-cycle averaging window**:

```
antiram_rate = sum(H counts in anti-RAM bins, over window) / exposure
ram_rate     = sum(H counts in RAM bins at high ESA, over window) / exposure_ram
```

Exposure time is estimated as half of the viewing time of viewing circle in the anti-ram direction. This corresponds to 420s x 0.5.

### 4. Good-Time State Machine

The algorithm maintains a `begin`/`end` state:

- **Opens** a good-time interval when **both** `antiram_rate < threshold` AND `ram_rate < ram_threshold`
- **Closes** it (and emits output) when **either** rate exceeds its threshold
- Also closes on **time gaps**: if consecutive cycles are more than 100 s apart (`DELAY_MAX`), the open interval is closed and the gap cycle is skipped

### 5. Accumulation During Good Times

While inside a good-time window, the algorithm accumulates two parallel sets of counts:

- **Synthetic background** (`sum_bg_cnts/og_cnts`): uses known absolute H/O background rates × exposure — used for the background output files
- **Proxy background** (`sum_bg1_cnts/og1_cnts`): actual anti-RAM H and O counts — written into the counts/exposure CSV

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
