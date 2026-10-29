cd 3S5_l1b_ram_maps

./batch_run_days.sh

cd ..

cd 3S6_l1b_oxy_ram_maps

./batch_run_days.sh

cd ..

# cd python

# python3.11 csv2yaml_nathan.py

# cd ..

cd 3S7_l1b_sputterbootstrap_ram

./batch_run.sh

cd ..

cd 3S8_l1b_cg_corrected

./batch_run.sh

cd ..


# ./update_sync.sh
