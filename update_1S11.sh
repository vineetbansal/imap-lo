[ -z "$1" ] || delaytime=$1

cd 1S11_CDF_l1c_pseval

./driver.sh "$delaytime"

cd ..


