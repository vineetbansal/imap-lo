# Comparing a quicklook map against `imap_processing`

The runnable procedure — staging, the 3S5–3S8 chain, the CDF and the plot — is in
[`../README.md`](../README.md). This file covers the comparison step it invokes:

```bash
python scripts/compare_to_l2.py --pivot 90
```

which exits non-zero on a mismatch, so the chain can be run under `set -e`.

To iterate on 3S5 alone without re-staging:

```bash
cd 3S5_l1b_ram_maps && python l1b_to_spin.py && python map_SCFrame_V2.py && cd ..
python scripts/compare_to_l2.py --pivot 90
```

## Verify counts and exposure, not intensity

`ena_intensity` is `ena_count / exposure_factor / (G x E)`, and the median map
pixel holds **2-3 counts** accumulated from **2-4 pointings**, the largest of
which contributes about half its exposure. Poisson alone is 58-71% per pixel, so
one event landing in the neighbouring pixel is a 30-50% intensity swing. An
intensity diff cannot separate a real error from a single count moving over.

`ena_count` and `exposure_factor` are additive and integral. Compare those first
-- a mismatch in them points straight at the pointing or the bin that caused it,
and once they agree the intensity follows from a <= 2% calibration difference.
`compare_to_l2.py` reports all three, and passes or fails on the first two.

A clean run looks like this:

```
pivot 90: quicklook 87 pointings, lo_l2 rules 87 pointings

ESA |        ena_count         |     exposure_factor      |   ena_intensity
    |  total   median     p90  |  total   median     p90  |  total   >20% of px
 1  |   0.00%    0.00%    0.00% |   0.00%    0.00%    0.00% |   0.00%    0.0%
 ...
PASS: ena_count and exposure_factor agree to within 1.0% on every ESA level
```

`compare_to_l2.py` reimplements `lo_l2`'s accumulation rather than calling it,
because `lo_l2` needs the IMAP_DPS CK kernel and per-repoint goodtimes/bgrates
CDFs, and this tree carries neither. It holds the spin axis common to both sides,
so a PASS means the two agree **up to the attitude source** -- the quicklook
reads `pointing_file.csv`, `lo_l2` samples the DPS CK. Closing that last
difference needs the CK kernels in `input_SPICE/`.

It is a fast pre-check on every pointing the quicklook mapped, not a substitute
for diffing a real SDC product. Do that too, once the CDF is built -- see
[`../README.md`](../README.md), which records where the two currently stand.

## What the two pipelines have to agree on

These were all sources of 20%-scale per-pixel intensity differences, and each is
now handled the same way on both sides. They are worth re-checking whenever the
inputs or the config files change.

| | `lo_l2` | quicklook |
|---|---|---|
| Good-time mask | `ttj2000ns_to_met` | `epoch_to_met` in `l1b_to_spin.py` — a naive `epoch - 2010-01-01` is off by **-8.409 s** and drops 3.1% of cycles overall, up to 14% on a thin day |
| Cone geometry | `goodtimes["pivot"]` | `goodtime_pivot()` — the **measured** 74.990 / 90.096 / 104.944, not the nominal 75/90/105 in `share_pivot.csv`, which is only for routing |
| Input keying | by repointing (`_complete_pointings`) | by repointing — 2026-097 carries repoint00209 **and** repoint00211, and day-keyed filenames let one silently overwrite the other |
| Missing pointings | dropped with a warning | `l1b_to_spin.py` collects them and exits non-zero; a pointing that the goodtimes product has no intervals for is an expected drop, anything else is an error |
| Ram/anti-ram split | per spin-angle bin (`pset_valid_mask`) | per bin, before accumulation — masking finished pixels lets an anti-ram bin's counts survive in a pixel a ram bin also lands in |
| Background rate | `bg_rate_exposure / exposure` | exposure-weighted accumulation in `map_SCFrame_V2.py` |

Two known differences remain, both small and both deliberate:

- **Geometric factors.** The quicklook's hardcoded `gf x 0.63529412` matches
  `imap_lo_hydrogen-geometric-factor_v004.csv` `GF_Trpl_H` to <= 0.4% and the
  energies to <= 2%, for a <= 2.1% intensity difference that is constant per ESA
  level. Reading the ancillary directly would remove it.
- **Systematic errors.** `fser`/`fseu`/`fsel` come from global scale factors
  (1.574 / 0.367 x G); `lo_l2` uses the per-level `GF_Trpl_H_unc_plus/minus`
  columns. Different by construction.

## Pitfalls in the input staging

- `generate_pointing_file.py` treats pset versions >= v900 as synthetic, because a
  v997 product on 2026-001 gave an attitude 51.9 deg off. Some real days have
  **only** an out-of-band product: 2026-017 and 2026-018 carry a v997 whose axis
  is identical to the archived v001. Those are now recovered, gated on the spin
  axis landing within 10 deg of the Sun (real days sit at 3.3-4.0 deg). Losing
  them cost two whole pointings, about half of the pivot-90 map's exposure
  deficit.
- Run `generate_pointing_file.py` against a pset directory covering **every day
  you intend to map**. `input_l1c/archive/` and `input_l1c/hide/` are not
  searched; a day whose only pset has been moved there gets no row, and
  `l1b_to_spin.py` will then fail on it.
- `share_pivot.csv` has `No Data` rows; parse `Pivot` with `pd.to_numeric(...,
  errors="coerce")` rather than `astype(float)`.

---

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