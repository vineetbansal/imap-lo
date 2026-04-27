[ -z "$1" ] || delaytime=$1

input=../input_l1b_histrates
input_de=../input_de
input_hk=../input_hk
output=./output

# Check if the target is a directory
if [ ! -d "$input" ]; then
  echo "1S19_l1b_histRates_autogoodtimes Error: Directory '$input' not found."
  exit 1
fi


find "$input" -maxdepth 1 -type f -name "*.cdf" -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do
    echo "1S19_l1b_histRates_autogoodtimes New file found: $file"
    # your command here
#for file in "$input"/*; do
  key=$(basename "$file" | grep -oE '_[0-9]{8}-repoint')

  match=$(ls "$input_de"/*"$key"* 2>/dev/null | head -n 1)

  mathk=$(ls "$input_hk"/*"$key"* 2>/dev/null | head -n 1)  

  if [[ -n "$match" ]]; then
    echo "1S19_l1b_histRates_autogoodtimes MATCH (DE):"
    echo "  hist = $file"
    echo "  de   = $match"

  # Check if the current item is a regular file (not a directory or other type)
    if [ -f "$file" ]; then
      echo "1S19_l1b_histRates_autogoodtimes Processing l1b HIST file: $file"
    fi

    if [ -f "$match" ]; then
      echo "1S19_l1b_histRates_autogoodtimes Processing l1b DE file: $match"
    fi

  else
    echo "1S19_l1b_histRates_autogoodtimes NO MATCH for $file"
    match="$file"
  fi

if [[ -n "$mathk" ]]; then
    echo "1S19_l1b_histRates_autogoodtimes MATCH (HK):"
    echo "  hist = $file"
    echo "  NHK   = $mathk"

  # Check if the current item is a regular file (not a directory or other type)
    if [ -f "$file" ]; then
      echo "1S19_l1b_histRates_autogoodtimes Processing l1b HIST file: $file"
    fi

    if [ -f "$mathk" ]; then
      echo "1S19_l1b_histRates_autogoodtimes Processing l1b HK file: $mathk"
    fi

  else
    echo "1S19_l1b_histRates_autogoodtimes_diag NO MATCH for $file"
    mathk="$file"
  fi

#  ofile="${file/#..\/input/./output}"
#  ofile="${ofile/.cdf/}"
  stem=$(basename "$file" .cdf)
  ofile="$output/${stem}_goodrate"
  echo "1S19_l1b_histRates_autogoodtimes_diag Output GT root: $ofile"

  oroot="${ofile}_cut1"
  ./runIMAP-fmv1-autogt.sh "$file" "$match" "$mathk" "$oroot" "0.0014" "0.0021"
  oroot="${ofile}_cut2"
  ./runIMAP-fmv1-autogt.sh "$file" "$match" "$mathk" "$oroot" "0.0028" "0.0042"
  oroot="${ofile}_cut3"
  ./runIMAP-fmv1-autogt.sh "$file" "$match" "$mathk" "$oroot" "0.0042" "0.0063"
  oroot="${ofile}_cut4"
  ./runIMAP-fmv1-autogt.sh "$file" "$match" "$mathk" "$oroot" "0.007" "0.0105"
  oroot="${ofile}_cut5"
  ./runIMAP-fmv1-autogt.sh "$file" "$match" "$mathk" "$oroot" "0.0112" "0.0168"
  oroot="${ofile}_cut6"
  ./runIMAP-fmv1-autogt.sh "$file" "$match" "$mathk" "$oroot" "0.0168" "0.0252"

done

cd "$output" || exit 1
#cat imap_lo_goodtimes_*.csv > imap_lo_goodtimes.csv
for cut in cut1 cut2 cut3 cut4 cut5 cut6; do
  first_file=$(ls *_goodrate_${cut}*.csv 2>/dev/null | head -n 1)
  [ -z "$first_file" ] && continue

  head -n 1 "$first_file" > "goodrate_${cut}.csv"
  awk 'FNR > 1' *_goodrate_${cut}*.csv >> "goodrate_${cut}.csv"
done

cd ..

