#!/bin/bash
# Run against the activated uv venv (see README); python3.11 is a shim to
# /media/vineetb/delta/projects/imap/lo/.venv/bin/python.
#source ~/.zshrc
#source ~/.bashrc
#conda activate mapenv

echo "3S3_l1b_Oxy_quickmaps L1B histrates to spin angle distribution Started "
python3.11 l1b_to_spin.py

#Create Maps
python3.11 map_SCFrame_V2.py

# Convert csv to text
# python3.11 csv_to_soc.py

# Plot Maps
python3.11 plot_map_DN.py
