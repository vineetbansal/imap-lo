#!/bin/bash
source ~/.zshrc
source ~/.bashrc
conda activate mapenv

echo "3S2_l1b_quickmaps L1B histrates to spin angle distribution Started "
python3.11 l1b_to_spin.py

#Create Maps
python3.11 map_SCFrame.py

# Convert csv to text
python3.11 csv_to_soc.py

# Plot Maps
python3.11 plot_map_DN.py

# convert to yaml stuff
# python3.11 csv2yaml.py
