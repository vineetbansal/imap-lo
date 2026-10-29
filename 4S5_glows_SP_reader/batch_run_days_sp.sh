#!/bin/bash
#source ~/.zshrc
#source ~/.bashrc
#conda activate mapenv

python3.11 glows_l3e_to_spin.py \
  --glows-dir ../input_glows/l3e \
  --goodtime-file ../input_goodtime/imap_lo_goodtimes.csv \
  --pointing-file ../3S2_l1b_quickmaps/config_files/pointing_file.csv \
  --pivot-csv ../3S2_l1b_quickmaps/config_files/share_pivot.csv \
  --out-dir ./outdir_glows \
  --start-date 20251108

python3.11 map_SCFrame_SP.py
