# Trimmed to the minimum needed for 3S8_l1b_cg_corrected/cg_correction_V5.py.
#
# 3S8 reads 3S7/outdir and 3S5/outdir; 3S7 reads 3S5/outdir and 3S6/outdir;
# 3S5 and 3S6 read ../input_l1b_histrates plus config_files/imap_lo_goodtimes_2.csv
# and imap_lo_{H,O}_background.csv -- which 1S04 produces and update_goodtimes.sh
# copies into place.  Nothing else in this file feeds that chain.
#
# 3S5/3S6/3S7/3S8 themselves are NOT run here; use ./update_3s5_3s8.sh afterwards.
#
# Everything below is commented out, not deleted.  Original: update.sh.bak
[ -z "$1" ] || delaytime=$1

# cd 1S02-CDF-l1b-histRates

# ./driver.sh "$delaytime"

# cd ..

# cd 1S02-CDF-l1b-monitorRates

# ./driver.sh "$delaytime"

# cd ..

./update_goodtimes.sh "$delaytime"

# cd 1S05_l1b_histRates_plots

# ./driver.sh "$delaytime"

# cd ..

# cd 1S06_l1b_prostar_plots

# ./driver.sh "$delaytime"

# cd ..

# cd 1S07_CDF_l1c_position_velocity

# ./driver.sh "$delaytime"
# cd output 
# cp imap_lo_position.csv ../../input_sc_position

# cd ..
# cd ..

# cd 1S08_TOFreport_AllTimes

# ./driver.sh "$delaytime"

# cd ..

# cd 1S09_TOFreport_Goodtimes

# ./driver.sh "$delaytime"

# cd ..

# cd 1S10_histrates_Goodtimes

# ./driver.sh "$delaytime"

# cd ..

# cd 1S11_CDF_l1c_pseval

# ./driver.sh "$delaytime"

# cd ..

# cd 1S13_TOFspinbin

# ./driver.sh "$delaytime"

# cd ..

# cd 1S14_l1b_histogram_spinangle

# python3.11 l1b_to_spin.py

# cd ..

# cd 1S15_TOFspinbin_goodtime

# ./driver.sh "$delaytime"

# cd ..

# cd 1S16_l1b_histogram_spinangle_goodtime

# python3.11 l1b_to_spin.py

# cd ..

# cd 1S17_l1a_TOFspinbin

# ./driver.sh "$delaytime"

# cd ..

# cd 1S18_l1a_TOFspinbin_histogramFilter

# ./driver.sh "$delaytime"

# cd ..

# cd 1S19_l1b_histRates_autogoodtimes_diag

# ./driver.sh "$delaytime"

# cd ..

# cd 1S20_TOFspinbin_hires_0.3

# ./driver.sh "$delaytime"

# cd ..

# cd 1S21_TOFspinbin_hires_0.6

# ./driver.sh "$delaytime"

# cd ..

# cd 1S22_TOFspinbin_hires_1.2

# ./driver.sh "$delaytime"

# cd ..

# cd 1S23_TOFspinbin_hires_1.2_goodtimes

# ./driver.sh "$delaytime"

# cd ..

# cd 3S2_l1b_histRates_autoram

# python3.11 hist_auto_ram_V2.py

# cd ..

# cd 3S2_l1b_quickmaps

# ./batch_run_days.sh

# cd ..

# cd 3S3_l1b_Oxy_quickmaps

# ./batch_run_days.sh

# cd ..

# cd python

# python3.11 csv2yaml_nathan.py

# cd ..

# cd 3S4_l1b_SputterBootstrap

# ./batch_run.sh

# cd .. 

# cd 4S1_starsensorModel

# ./driver.sh "$delaytime"

# cd ..

# ./update_sync.sh
