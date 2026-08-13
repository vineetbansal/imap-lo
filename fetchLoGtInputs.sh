#!/usr/bin/env bash

# This tool expects two input arguments: the start and end dates
# These should be in the format of YYYYMMdd, e.g. 20260205

# Input checking, rudimentary
if [[ -z "$1" ]]; then
    echo "Start date must be specified!"
    exit 1;
fi
if [[ -z "$2" ]]; then
    echo "End date must be specified!"
    exit 1;
fi

# Go to the root path where data will be downloaded to
cd $IMAP_DATA_DIR

# Fetch the latest DE, NHK, and HISTRATES products from the SDC
# Annoying thta you can't do a query-and-download in one step...

echo "fetchign l1a"
FILES=`imap-data-access query --instrument lo --data-level l1a --descriptor de --version latest --start-date $1 --end-date $2 | awk '/imap_/ {print $17}'`
for file in $FILES; do
    imap-data-access download $file
done
echo "got l1a"

echo "fetching l1b de"
FILES=`imap-data-access query --instrument lo --data-level l1b --descriptor de --version latest --start-date $1 --end-date $2 | awk '/imap_/ {print $17}'`
for file in $FILES; do
    imap-data-access download $file
done
echo "got l1b de"

echo "fetching l1b nhk"
FILES=`imap-data-access query --instrument lo --data-level l1b --descriptor nhk --version latest --start-date $1 --end-date $2 | awk '/imap_/ {print $17}'`
for file in $FILES; do
    imap-data-access download $file
done
echo "got l1b nhk"

echo "fetching l1b histrates"
FILES=`imap-data-access query --instrument lo --data-level l1b --descriptor histrates --version latest --start-date $1 --end-date $2 | awk '/imap_/ {print $17}'`
for file in $FILES; do
    imap-data-access download $file
done
echo "got l1b histrates"

echo "fetching l1b shk"
FILES=`imap-data-access query --instrument lo --data-level l1b --descriptor shk --version latest --start-date $1 --end-date $2 | awk '/imap_/ {print $17}'`
for file in $FILES; do
    imap-data-access download $file
done
echo "got l1b shk"

echo "fetching l1b monitorrates"
FILES=`imap-data-access query --instrument lo --data-level l1b --descriptor monitorrates --version latest --start-date $1 --end-date $2 | awk '/imap_/ {print $17}'`
for file in $FILES; do
    imap-data-access download $file
done
echo "got l1b monitorrates"

echo "fetching l1b prostar"
FILES=`imap-data-access query --instrument lo --data-level l1b --descriptor prostar --version latest --start-date $1 --end-date $2 | awk '/imap_/ {print $17}'`
for file in $FILES; do
    imap-data-access download $file
done
echo "got l1b prostar"

echo "fetching l1b goodtimes"
FILES=`imap-data-access query --instrument lo --data-level l1b --descriptor goodtimes --version latest --start-date $1 --end-date $2 | awk '/imap_/ {print $17}'`
for file in $FILES; do
    imap-data-access download $file
done
echo "got l1b goodtimes"

echo "fetching l1c pset"
FILES=`imap-data-access query --instrument lo --data-level l1c --descriptor pset --version latest --start-date $1 --end-date $2 | awk '/imap_/ {print $17}'`
for file in $FILES; do
    imap-data-access download $file
done
echo "got l1c pset"



# Clear out the old data in the Lo team's auto-gt tool
#rm -rf imap/ancillary/lo/temp/1S4_l1b_histRates_autogoodtimes/input/*
#rm -rf imap/ancillary/lo/temp/1S4_l1b_histRates_autogoodtimes/input_de/*
#rm -rf imap/ancillary/lo/temp/1S4_l1b_histRates_autogoodtimes/nhk/*

# Move the new data to the location of the Lo team's auto-gt tool
echo "copying files into new homes"
cp imap/lo/l1a/*/*/*_de* ./input_l1a_de
cp imap/lo/l1b/*/*/*_histrates* ./input_l1b_histrates
cp imap/lo/l1b/*/*/*_monitorrates* ./input_l1b_monitorrates
cp imap/lo/l1b/*/*/*_de* ./input_de
cp imap/lo/l1b/*/*/*_nhk* ./input_hk
cp imap/lo/l1b/*/*/*_shk* ./input_shk
cp imap/lo/l1b/*/*/*_prostar* ./input_prostar
cp imap/lo/l1c/*/*/*_pset* ./input_l1c
echo "done copying over"

echo "cleaning up homes"
cd input_l1a_de
./move_crap.sh
cd ..

cd input_de
./move_crap.sh
cd ..

cd input_l1b_histrates
./move_crap.sh
cd ..

cd input_hk
./move_crap.sh
cd ..

cd input_shk
./move_crap.sh
cd ..

cd input_l1b_monitorrates
./move_crap.sh
cd ..

cd input_prostar
./move_crap.sh
cd ..

cd input_l1c
./move_crap.sh
cd ..
echo "done cleaning up homes"
echo "done being done, ie bye .. "
