[ -z "$1" ] || delaytime=$1

cd 1S10_histrates_Goodtimes

rm -f -r output/*

./driver.sh "$delaytime"

cd ..

cd 1S16_l1b_histogram_spinangle_goodtime

rm -f -r l1b_hist_csv/*

python3.11 l1b_to_spin.py

cd ..

cd 1S24_l1a_TOFspinbin_histogramFilter_goodtime

rm -f -r output/*

./driver.sh "$delaytime"

cd .. 

./update_sync.sh
