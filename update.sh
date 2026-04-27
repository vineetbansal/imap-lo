[ -z "$1" ] || delaytime=$1

cd 1S02-CDF-l1b-histRates

./driver.sh "$delaytime"

cd ..

cd 1S02-CDF-l1b-monitorRates

./driver.sh "$delaytime"

cd ..

cd 1S04_l1b_histRates_autogoodtimes

 ./driver.sh "$delaytime"
cd output 
cp imap_lo_goodtimes.csv ../../input_goodtime
cp imap_lo_HO_cnts_expo.csv ../../input_goodtime_context
cp imap_lo_goodtimes.csv ../../3S2_l1b_quickmaps/config_files/imap_lo_goodtimes_2.csv
cp imap_lo_goodtimes.csv ../../3S3_l1b_Oxy_quickmaps/config_files/imap_lo_goodtimes_2.csv
cp imap_lo_goodtimes_ideas.csv ../../1S12_TOFideas

cp imap_lo_H_background.csv ../../3S2_l1b_quickmaps/config_files
cp imap_lo_O_background.csv ../../3S3_l1b_Oxy_quickmaps/config_files

cd ..
cd ..

cd 1S05_l1b_histRates_plots

./driver.sh "$delaytime"

cd ..

cd 1S06_l1b_prostar_plots

./driver.sh "$delaytime"

cd ..

cd 1S07_CDF_l1c_position_velocity

./driver.sh "$delaytime"
cd output 
cp imap_lo_position.csv ../../input_sc_position

cd ..
cd ..

cd 1S08_TOFreport_AllTimes

./driver.sh "$delaytime"

cd ..

cd 1S09_TOFreport_Goodtimes

./driver.sh "$delaytime"

cd ..

cd 1S10_histrates_Goodtimes

./driver.sh "$delaytime"

cd ..

cd 1S11_CDF_l1c_pseval

./driver.sh "$delaytime"

cd ..

cd 1S13_TOFspinbin

./driver.sh "$delaytime"

cd ..

cd 1S14_l1b_histogram_spinangle

python3.11 l1b_to_spin.py

cd ..

cd 1S15_TOFspinbin_goodtime

./driver.sh "$delaytime"

cd ..

cd 1S16_l1b_histogram_spinangle_goodtime

python3.11 l1b_to_spin.py

cd ..

cd 1S17_l1a_TOFspinbin

./driver.sh "$delaytime"

cd ..

cd 1S18_l1a_TOFspinbin_histogramFilter

./driver.sh "$delaytime"

cd ..

cd 1S19_l1b_histRates_autogoodtimes_diag

./driver.sh "$delaytime"

cd ..

cd 1S20_TOFspinbin_hires_0.3

./driver.sh "$delaytime"

cd ..

cd 1S21_TOFspinbin_hires_0.6

./driver.sh "$delaytime"

cd ..

cd 1S22_TOFspinbin_hires_1.2

./driver.sh "$delaytime"

cd ..

cd 1S23_TOFspinbin_hires_1.2_goodtimes

./driver.sh "$delaytime"

cd ..

cd 3S2_l1b_histRates_autoram

./driver.sh "$delaytime"

cd ..

cd 3S2_l1b_quickmaps

./batch_run_days.sh

cd ..

cd 3S3_l1b_Oxy_quickmaps

./batch_run_days.sh

cd ..

cd python

python3.11 csv2yaml_nathan.py 

cd ..

cd 3S4_l1b_SputterBootstrap

./batch_run.sh

cd .. 

cd 4S1_starsensorModel

./driver.sh "$delaytime"

cd ..

./update_sync.sh
