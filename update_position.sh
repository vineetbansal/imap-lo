[ -z "$1" ] || delaytime=$1

cd 1S07_CDF_l1c_position_velocity

./driver.sh "$delaytime"
cd output 
cp imap_lo_position.csv ../../input_sc_position

cd ..
cd ..

./update_sync.sh
