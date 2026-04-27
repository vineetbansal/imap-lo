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
cd /Users/nschwadron/Computer/IMAP_Lo/quickpipeline

# Get rid of any old Lo L1B products before starting
rm -rf data/imap/lo/l1b/*

# Fetch the latest DE, NHK, and HISTRATES products from the SDC
# Annoying thta you can't do a query-and-download in one step...
FILES=`imap-data-access query --instrument lo --data-level l1a --descriptor de --version latest --start-date $1 --end-date $2 | awk '/imap_/ {print $17}'`
for file in $FILES; do
    imap-data-access download $file
done

# Clear out the old data in the Lo team's auto-gt tool
#rm -rf data/imap/ancillary/lo/temp/1S4_l1b_histRates_autogoodtimes/input/*
#rm -rf data/imap/ancillary/lo/temp/1S4_l1b_histRates_autogoodtimes/input_de/*
#rm -rf data/imap/ancillary/lo/temp/1S4_l1b_histRates_autogoodtimes/nhk/*

# Move the new data to the location of the Lo team's auto-gt tool
cp data/imap/lo/l1a/*/*/*_de* ./input_l1a_de

#cd input_l1a_de
#./move_crap.sh
#cd ..
