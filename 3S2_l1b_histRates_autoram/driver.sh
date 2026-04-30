#!/bin/bash
set -euo pipefail

[ -z "$1" ] || delaytime="${1:-1}"

input="../input_l1b_histrates"
input_de="../input_de"
input_hk="../input_hk"
output="./output"

mkdir -p "$output"

lockfile="./3S2_l1b_histRates_autoram.lock"
exec 9>"$lockfile"
if !flock -n 9; then
  echo "3S2_l1b_histRates_autoram already running. Exiting."
  exit 1
fi

# Check if the target is a directory
if [ ! -d "$input" ]; then
  echo "Error: Directory '$directory' not found."
  exit 1
fi

# for file in "$input"/*; do
# find "$input" -maxdepth 1 -type f -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do
find "$input" -maxdepth 1 -type f -name "*.cdf" -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do

  base=$(basename "$file")
  key=$(echo "$base" | grep -oE '_[0-9]{8}-repoint[0-9]+' || true)
#  key=$(basename "$file" | grep -oE '_[0-9]{8}-repoint')

  if [[ -z "$key" ]]; then
    echo "3S2_l1b_histRates_autoram SKIP: could not extract date/repoint key from $file"
    continue
  fi

# we comment out old versions
  match=$(find "$input_de" -maxdepth 1 -type f -name "*${key}*.cdf" | head -n 1 || true)
  mathk=$(find "$input_hk" -maxdepth 1 -type f -name "*${key}*.cdf" | head -n 1 || true)
#  match=$(ls "$input_de"/*"$key"* 2>/dev/null | head -n 1)
#  mathk=$(ls "$input_hk"/*"$key"* 2>/dev/null | head -n 1)  

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


  #ofile="${file/#..\/input_l1b_histrates/./output}"
  #ofile="${ofile/.cdf/}"


  ofile="$output/${base%.cdf}"
  echo "3S2_l1b_histRates_autoram Output base: $ofile"

  ./runIMAP-fmv1-auto_ram.sh "$file" "$match" "$mathk" "$ofile" 
  
done

cd $output 

shopt -s nullglob

rm -f imap_lo_goodtimes.csv imap_lo_goodtimes.csv.tmp
cat imap_lo_goodtimes_*.csv > imap_lo_goodtimes.csv.tmp
mv imap_lo_goodtimes.csv.tmp imap_lo_goodtimes.csv

rm -f imap_lo_H_background.csv imap_lo_H_background.csv.tmp
cat imap_lo_H_background_*.csv > imap_lo_H_background.csv.tmp
mv imap_lo_H_background.csv.tmp imap_lo_H_background.csv

rm -f imap_lo_O_background.csv imap_lo_O_background.csv.tmp
cat imap_lo_O_background_*.csv > imap_lo_O_background.csv.tmp
mv imap_lo_O_background.csv.tmp imap_lo_O_background.csv

for pattern in \
    "imap_lo_HO_cnts_expo_*.csv" \
    "imap_lo_ram_HO_cnts_expo_*.csv" \
    "imap_lo_r18_HO_cnts_expo_*.csv" \
    "imap_lo_r24_HO_cnts_expo_*.csv" \
    "imap_lo_r30_HO_cnts_expo_*.csv" \
    "imap_lo_r30_HO_peak_expo_*.csv"
do
    outfile="${pattern/_\*/}"
    tmpfile="${outfile}.tmp"

    rm -f "$outfile" "$tmpfile"

    files=( $pattern )

    if (( ${#files[@]} == 0 )); then
        echo "No files for $pattern"
        continue
    fi

    echo "Bundling $pattern -> $outfile"

    head -n 1 "${files[0]}" > "$tmpfile"
    awk 'FNR>1' "${files[@]}" >> "$tmpfile"
    mv "$tmpfile" "$outfile"
done


cd ..


