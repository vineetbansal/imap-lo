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
source setup.sh 
cd $IMAP_DATA_DIR

# Get rid f any old data (commented out 8/14/2027)
# rm -rf imap/lo/l1a/*
# rm -rf imap/lo/l1b/*

# Fetch the latest DE, NHK, and HISTRATES products from the SDC
# Annoying thta you can't do a query-and-download in one step...

echo "fetching l1b prostar"
FILES=`imap-data-access query --instrument lo --data-level l1b --descriptor prostar --version latest --start-date $1 --end-date $2 | awk '/imap_/ {print $17}'`
for file in $FILES; do
    imap-data-access download $file
done
echo "got l1b prostar"

cd ..

# Move the new data to the location of the Lo team's auto-gt tool
echo "copying files into new homes"
cp $IMAP_DATA_DIR/imap/lo/l1b/*/*/*_prostar* ./input_prostar
echo "done copying over"

cd input_prostar
./move_crap.sh
cd ..

echo "done cleaning up homes"
echo "done being done, ie bye .. "
