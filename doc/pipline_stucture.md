# IMAP-Lo Report Pipeline Structure

Date: 2026-04-17
Version: 2.0 (Draft)

## BLUF

This document summarizes the current IMAP-Lo report pipeline, including data inputs, automated processing stages, derived products, diagnostics, validation tools, and legacy utilities. It is intended to support continuity, onboarding, maintenance, and future development.

## 1. Purpose and Scope

The IMAP-Lo quick pipeline ingests source data products from the Science Data Center (SDC), generates operational diagnostics and science-ready intermediate products, and supports validation of Level 1 through higher-level map products.

## 2. Documentation

### `doc/`

Contains pipeline documentation, revision notes, and supporting memos.

### `doc/memos/`

Detailed technical notes, background analyses, and implementation history.

## 3. Main Driver Scripts

### `fetchLoGtInputs.sh`

Shell script used to retrieve new files through the API.

### `update.sh`

Primary update script for the pipeline.

* Accepts an argument specifying the number of days to refresh.
* Example: `./update.sh -1` updates files with timestamps from the last day.

### Partial Update Scripts

* `update_1S05.sh`
* `update_1S08.sh`
* `update_1S09.sh`
* `update_1S10.sh`
* `update_1S11.sh`
* `update_1S13-14.sh`
* `update_sync.sh`

Used for selective reprocessing of portions of the pipeline.

## 4. Input Data Sources

### Standard Inputs

* `input_de/` — Level 1B annotated direct events
* `input_goodtime/` — Generated good-time intervals
* `input_goodtime_context/` — Context for each good-time interval (e.g., H counts, CO counts, PPM angle)
* `input_hk/` — Hardware housekeeping
* `input_shk/` — Software housekeeping
* `input_l1a_de/` — Level 1A direct events
* `input_l1b_histrates/` — Level 1B histogram rates
* `input_l1b_monitorrates/` — Level 1B monitor rates
* `input_l1c/` — Level 1C pointing sets
* `input_prostar/` — Processed star sensor data
* `input_sc_position/` — Spacecraft position and spin-state data derived from Level 1C products

### Informal / Supplemental Inputs

* `input_l1c_david/` — Supplemental Level 1C variants provided for operations support while SPICE content lagged official deliveries.

## 5. Standard Level 1 Pipeline Products

* `1S02-CDF-l1b-histRates/` — Histogram rates exported to CSV
* `1S02-CDF-l1b-monitorRates/` — Monitor rates exported to CSV
* `1S04_l1b_histRates_autogoodtimes/` — Automatically generated good-time intervals
* `1S05_l1b_histRates_plots/` — Daily histogram quicklook plots for H and O
* `1S06_l1b_prostar_plots/` — Daily processed star sensor plots
* `1S07_CDF_l1c_position_velocity/` — Position, spin, and spacecraft velocity data in CSV form
* `1S08_TOFreport_AllTimes/` — Daily TOF reports over all times
* `1S09_TOFreport_Goodtimes/` — TOF reports filtered by good times
* `1S10_histrates_Goodtimes/` — Histogram rates filtered by good times
* `1S11_CDF_l1c_pseval/` — Pointing-set evaluation files
* `1S13_TOFspinbin/` — TOF distributions binned into 6° NEP phase bins for H and O
* `1S14_l1b_histogram_spinangle/` — Corresponding histogram spin-angle distributions
* `1S15_TOFspinbin_goodtime/` — Good-time filtered TOF spin-bin distributions
* `1S16_l1b_histogram_spinangle_goodtime/` — Good-time filtered histogram spin-angle distributions
* `1S17_l1a_TOFspinbin/` — Level 1A TOF spin-phase validation products
* `1S18_l1a_TOFspinbin_histogramFilter/` — Level 1A DE products binned identically to histograms for cross-validation
* `1S19_l1b_histRates_autogoodtimes_diag/` — Diagnostics for statistical evaluation of good-time selection
* `1S20_TOFspinbin_hires_0.3/` — High-resolution 0.3° spin-phase products
* `1S21_TOFspinbin_hires_0.6/` — High-resolution 0.6° spin-phase products
* `1S22_TOFspinbin_hires_1.2/` — High-resolution 1.2° spin-phase products

## 6. Off-Pipeline Level 1 Products

### `1S12_TOFideas/`

Interactive TOF analysis utilities using CSV selection sheets. Supports filtering by time, ESA step, spin bin, and event type.

### `1R07_CDF_l1c_position_velocity/`

Used to evaluate alternate Level 1C position products.

## 7. Higher-Level Products

### Level 3

* `3S2_l1b_histRates_autoram/` — Moment and fit peaks in spin-phase distributions
* `3S2_l1b_quickmaps/` — Hydrogen flux maps from Level 1B histograms
* `3S3_l1b_Oxy_quickmaps/` — Oxygen quick maps
* `3S4_l1b_SputterBootstrap/` — Sputter/bootstrap corrected histogram maps

### Level 4

* `4S1_starsensorModel/` — Star sensor simulations using stellar maps

## 8. Utilities and Support Areas

* `algorithms/` — Algorithm development material and validation spreadsheets
* `archive/` — Legacy or deprecated content pending cleanup
* `bash_functions/` — Shared shell helper functions
* `data/` — Intermediate fetched data products
* `diagnostics/` — Diagnostic outputs
* `logs/` — Update run logs
* `mapping_visualization_code/` — Map visualization and projection tools
* `python/` — Miscellaneous Python utilities
* `software_loads/` — Software load documentation and release notes

## 9. Current Operational Risks / Gaps

* Documentation coverage remains incomplete in several areas.
* Some supplemental inputs exist due to lagging upstream products.
* Legacy content should be reviewed for retirement or consolidation.







