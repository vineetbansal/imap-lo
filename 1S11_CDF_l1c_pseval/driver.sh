[ -z "$1" ] || delaytime=$1

data=.
#ident=Instrument_FM1_play
ident=Instrument_FM1_ilo_hvsci_

input=../input_l1c
output=./output

# Check if the target is a directory
if [ ! -d "$input" ]; then
  echo "1S11 Error: Directory '$directory' not found."
  exit 1
fi

# for file in "$input"/*; do
# find "$input" -maxdepth 1 -type f -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do
find "$input" -maxdepth 1 -type f -name "*.cdf" -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do


  # Check if the current item is a regular file (not a directory or other type)
  if [ -f "$file" ]; then
      echo "1S11 Processing file: $file"
  fi

    ./runIMAP-fmv1-read-l1c.sh "$file" 
done

cd $output
file1=`ls *_aram_counts_*.csv | head -n 1`
head -n 1 $file1 > imap_lo_antiram_counts.csv 
awk 'FNR>1' *_aram_counts_*.csv >>  imap_lo_antiram_counts.csv 

cd .. 

