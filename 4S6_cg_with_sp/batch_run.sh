#!/bin/sh

echo "CG corrected maps with survival probabiliy"
python3.11 cg_correction_V4_wsp.py

echo "Generating CG Plots"
python3.11 plot_map_DN.py

echo "masking"
python3.11 post_mask_v3.py

echo "Generating CG Plots"
python3.11 plot_map_DN_masked.py

python3.11 cg_csv2yaml_nathan.py
