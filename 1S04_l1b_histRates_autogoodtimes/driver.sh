[ -z "$1" ] || delaytime=$1

input=../input_l1b_histrates
input_de=../input_de
input_hk=../input_hk
output=./output

# Check if the target is a directory
if [ ! -d "$input" ]; then
  echo "1S04_l1b_histRates_autogoodtimes Error: Directory '$directory' not found."
  exit 1
fi

find "$input" -maxdepth 1 -type f -name "*.cdf" -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do
    echo "1S04_l1b_histRates_autogoodtimes New file found: $file"
    # your command here
#for file in "$input"/*; do
  key=$(basename "$file" | grep -oE '_[0-9]{8}-repoint')

  match=$(ls "$input_de"/*"$key"* 2>/dev/null | head -n 1)

  mathk=$(ls "$input_hk"/*"$key"* 2>/dev/null | head -n 1)  

  if [[ -n "$match" ]]; then
    echo "1S04_l1b_histRates_autogoodtimes MATCH (DE):"
    echo "  hist = $file"
    echo "  de   = $match"

  # Check if the current item is a regular file (not a directory or other type)
    if [ -f "$file" ]; then
      echo "1S04_l1b_histRates_autogoodtimes Processing l1b HIST file: $file"
    fi

    if [ -f "$match" ]; then
      echo "1S04_l1b_histRates_autogoodtimes Processing l1b DE file: $match"
    fi

  else
    echo "1S04_l1b_histRates_autogoodtimes NO MATCH for $file"
    match="$file"
  fi

if [[ -n "$mathk" ]]; then
    echo "1S04_l1b_histRates_autogoodtimes MATCH (HK):"
    echo "  hist = $file"
    echo "  NHK   = $match"

  # Check if the current item is a regular file (not a directory or other type)
    if [ -f "$file" ]; then
      echo "1S04_l1b_histRates_autogoodtimes Processing l1b HIST file: $file"
    fi

    if [ -f "$mathk" ]; then
      echo "1S04_l1b_histRates_autogoodtimes Processing l1b HK file: $match"
    fi

  else
    echo "1S04_l1b_histRates_autogoodtimes NO MATCH for $file"
    mathk="$file"
  fi

  ./runIMAP-fmv1-autogt.sh "$file" "$match" "$mathk" 
  
done

cd $output 
#cat imap_lo_goodtimes_*.csv > imap_lo_goodtimes.csv
> imap_lo_goodtimes.csv  # truncate/create the file first
for f in imap_lo_goodtimes_???????.csv; do
    [[ "$f" == "imap_lo_goodtimes_ideas.csv" ]] && continue
    cat "$f" >> imap_lo_goodtimes.csv
done
cat imap_lo_H_background_*.csv > imap_lo_H_background.csv 
cat imap_lo_O_background_*.csv > imap_lo_O_background.csv 
cat imap_lo_HO_cnts_expo_*.csv > imap_lo_HO_cnts_expo.csv

file1=`ls imap_lo_goodtimes_ideas_*.csv | head -n 1`
head -n 1 $file1 > imap_lo_goodtimes_ideas.csv 
awk 'FNR>1' imap_lo_goodtimes_ideas_*.csv >>  imap_lo_goodtimes_ideas.csv

cd ..
