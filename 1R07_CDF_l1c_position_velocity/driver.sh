[ -z "$1" ] || delaytime=$1

data=.
#ident=Instrument_FM1_play
ident=Instrument_FM1_ilo_hvsci_

input=../input_l1c_david
output=./output

# Check if the target is a directory
if [ ! -d "$input" ]; then
  echo "1R07_CDF_l1c_position_velocity Error: Directory '$directory' not found."
  exit 1
fi

# for file in "$input"/*; do
# find "$input" -maxdepth 1 -type f -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do
find "$input" -maxdepth 1 -type f -name "*.cdf" -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do

  # Check if the current item is a regular file (not a directory or other type)
  if [ -f "$file" ]; then
      echo "1R07_CDF_l1c_position_velocity Processing file: $file"
  fi

  ofile="${file/#..\/input_l1c_david/./output}"
  ofile="${ofile/.cdf/}"
  echo "1R07_CDF_l1c_position_velocity Output H file: $ofile"

    ./runIMAP-fmv1-read-l1c.sh "$file" "$ofile" 
done

cd $output
file1=`ls imap_lo_position_*.csv | head -n 1`
head -n 1 $file1 > imap_lo_position.csv 
awk 'FNR>1' imap_lo_position_*.csv >>  imap_lo_position.csv 


cd .. 

