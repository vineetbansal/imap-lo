#!/bin/sh

echo "Creating Bootstrapped and Sputtering Products"
python3.11 correction_v2.py

echo "Generating Plots"
python3.11 plot_map_DN.py

python3.11 corrected_csv2yaml_nathan.py
