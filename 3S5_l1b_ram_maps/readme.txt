# L1B Histogram CDF to Spin-Angle Map Processing Pipeline

To run the pipeline execute the following:

------------------------------------------
sh batch_run_days.sh 
------------------------------------------

This pipeline processes IMAP-Lo L1B histogram-rate data into spin-angle–resolved
distributions and generates spacecraft-frame maps, text products, and
diagnostic plots.

## Prerequisites

Before running the processing pipeline, ensure the following directory structure
and files are in place:

1. L1B Histogram-Rate Files
   All L1B histogram-rate (histrates) files must be located in:
   ./l1b_histrates/

2. Configuration Files
   All required configuration files must reside in:
   ./config_files/

   The file names must exactly match the following conventions:
   imap_lo_goodtimes_2.csv
   pointing_file.csv
   share_pivot.csv

3. Python Environment

   * Python 3 must be available in your environment.
   * All required Python dependencies for the processing scripts must be
     installed prior to execution.

## Processing Steps

The pipeline is executed via the following bash script:
------------------------------------------------------
#!/bin/bash

echo "L1B histrates to spin angle distribution Started"

# Convert L1B histogram rates to spin-angle distributions

python3 l1b_to_spin.py

# Create spacecraft-frame maps

python3 map_SCFrame.py

# Convert CSV products to SOC-compatible text format

python3 csv_to_soc.py

# Generate diagnostic and science plots

python3 plot_map_DN.py
-------------------------------------------------
Each step depends on the successful completion of the previous one.

## Outputs

1. Automatic Directory Creation
   All required output and plot directories are created automatically during
   processing.

2. Final Data Products
   Spin-angle–resolved map products are generated in:
   - CSV format (.csv)
   - SOC-compatible text format (.txt)

3. Plots
   All diagnostic and science plots are saved in their designated plot directory.

4. Intermediate Products
   Daily spin-angle–distributed count data are saved as intermediate outputs and
   used in subsequent processing steps.

## Notes

* Ensure that file naming conventions and directory paths are strictly followed
  to avoid runtime errors.
* The pipeline is designed to be run from the top-level working directory.
