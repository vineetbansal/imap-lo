[ -z "$1" ] || delaytime=$1

cd 1S13_TOFspinbin

./driver.sh "$delaytime"

cd ..

cd 1S14_l1b_histogram_spinangle

python3.11 l1b_to_spin.py

cd ..






