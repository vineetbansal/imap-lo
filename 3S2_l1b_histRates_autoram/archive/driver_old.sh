_v2_ [ -z "$1" ] || delaytime=$1

input=../input_l1b_histrates
input_de=../input_de
input_hk=../input_hk
output=./output

# Check if the target is a directory
if [ ! -d "$input" ]; then
  echo "Error: Directory '$directory' not found."
  exit 1
fi

# for file in "$input"/*; do
# find "$input" -maxdepth 1 -type f -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do
find "$input" -maxdepth 1 -type f -name "*.cdf" -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do


  key=$(basename "$file" | grep -oE '_[0-9]{8}-repoint')

  match=$(ls "$input_de"/*"$key"* 2>/dev/null | head -n 1)

  mathk=$(ls "$input_hk"/*"$key"* 2>/dev/null | head -n 1)  

  if [[ -n "$match" ]]; then
    echo "3S2_l1b_histRates_autoram MATCH (DE):"
    echo "  hist = $file"
    echo "  de   = $match"

  # Check if the current item is a regular file (not a directory or other type)
    if [ -f "$file" ]; then
      echo "3S2_l1b_histRates_autoram Processing l1b HIST file: $file"
    fi

    if [ -f "$match" ]; then
      echo "3S2_l1b_histRates_autoram Processing l1b DE file: $match"
    fi

  else
    echo "3S2_l1b_histRates_autoram NO MATCH for $file"
    match="$file"
  fi

if [[ -n "$mathk" ]]; then
    echo "3S2_l1b_histRates_autoram MATCH (HK):"
    echo "  hist = $file"
    echo "  NHK   = $match"

  # Check if the current item is a regular file (not a directory or other type)
    if [ -f "$file" ]; then
      echo "3S2_l1b_histRates_autoram Processing l1b HIST file: $file"
    fi

    if [ -f "$mathk" ]; then
      echo "3S2_l1b_histRates_autoram Processing l1b HK file: $match"
    fi

  else
    echo "3S2_l1b_histRates_autoram NO MATCH for $file"
    mathk="$file"
  fi


  ofile="${file/#..\/input_l1b_histrates/./output}"
  ofile="${ofile/.cdf/}"
  echo "3S2_l1b_histRates_autoram Output GT file: $ofile"

  ./runIMAP-fmv1-auto_ram.sh "$file" "$match" "$mathk" "$ofile" 
  
done

cd $output 
cat imap_lo_goodtimes_*.csv > imap_lo_goodtimes.csv
cat imap_lo_H_background_*.csv > imap_lo_H_background.csv 
cat imap_lo_O_background_*.csv > imap_lo_O_background.csv 

for pattern in \
    "imap_lo_HO_cnts_expo_*.csv" \
    "imap_lo_ram_HO_cnts_expo_*.csv" \
    "imap_lo_r18_HO_cnts_expo_*.csv" \
    "imap_lo_r24_HO_cnts_expo_*.csv" \
    "imap_lo_r30_HO_cnts_expo_*.csv" \
    "imap_lo_r30_HO_peak_expo_*.csv"
do
    outfile="${pattern//\_\*/}"   # remove the * for output filename
    
    file1=$(ls $pattern | head -n 1)
    head -n 1 "$file1" > "$outfile"
    awk 'FNR>1' $pattern >> "$outfile"
done

cd ..


