cd 3S5_l1b_ram_maps

./batch_run_days.sh

cd ..

cd 3S6_l1b_oxy_ram_maps

./batch_run_days.sh

cd ..

# YAML packaging step, not consumed by 3S7 or 3S8.  Its case=="A" branch reads
# 3S2_l1b_quickmaps/outdir and 3S3_l1b_Oxy_quickmaps/outdir, which update.sh no
# longer populates, so it would fail on missing paths.
# cd python

# python3.11 csv2yaml_nathan.py

# cd ..

cd 3S7_l1b_sputterbootstrap_ram

./batch_run.sh

cd .. 

cd 3S8_l1b_cg_corrected

./batch_run.sh

cd .. 


# rsyncs to /Users/nschwadron/Dropbox/... -- a macOS path that does not exist here.
# ./update_sync.sh
