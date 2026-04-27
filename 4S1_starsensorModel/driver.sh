[ -z "$1" ] || delaytime=$1

input=../input_prostar
input_sc=../input_sc_position
input_gc=../input_goodtime_context
output=./output

# Check if the target is a directory
if [ ! -d "$input" ]; then
  echo "1S06_l1b_prostar_plots Error: Directory '$directory' not found."
  exit 1
fi

scpos="$input_sc"/imap_lo_position.csv
gtcon="$input_gc"/imap_lo_HO_cnts_expo.csv

# for file in "$input"/*; do
find "$input" -maxdepth 1 -type f -name "*.cdf" -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do

  # Check if the current item is a regular file (not a directory or other type)
    if [ -f "$file" ]; then
      echo "4S1_starsensorModel Processing l1b  prostar file: $file"
    fi

  ofile="${file/#..\/input_prostar/./output}"
#  ofile="${file/../input_prostar/./output}"
  ofile="${ofile/.cdf/}"
  echo "4S1_starsensorModel Output GT file: $ofile"

  ./runIMAP-fmv1-mostar.sh "$file" "$scpos" "$gtcon" "$ofile" 
  
done



