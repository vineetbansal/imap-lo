#!/bin/bash

[ -z "$1" ] || goodtimes_ideas=$1

input=../input_l1a_de
hkinput=../input_hk

goodtime_file="$goodtimes_ideas"

oselect="${goodtime_file/.csv/}"
odir="./output/${oselect}"
[ -d "$odir" ] || mkdir -p "$odir"

if [ ! -d "$input" ]; then
  echo "Error: Directory '$input' not found."
  exit 1
fi

if [ ! -d "$hkinput" ]; then
  echo "Error: Directory '$hkinput' not found."
  exit 1
fi

if [ ! -f "$goodtime_file" ]; then
  echo "Error: goodtime ideas file '$goodtime_file' not found."
  exit 1
fi

for file in "$input"/*.cdf; do

  [ -f "$file" ] || continue

  echo "Processing L1A DE file: $file"

  base=$(basename "$file")

  # Extract YYYYMMDD-repointNNNNN
  key=$(echo "$base" | grep -oE '[0-9]{8}-repoint[0-9]+')

  if [ -z "$key" ]; then
    echo "WARNING: Could not extract date/repoint key from $base"
    continue
  fi

  # Find matching HK file
  hkfile=$(ls "$hkinput"/*"$key"*.cdf 2>/dev/null | sort | tail -n 1)

  if [ -z "$hkfile" ]; then
    echo "WARNING: No matching HK file found for key $key"
    continue
  fi

  echo "Matched HK file: $hkfile"

  ofile="${file/#..\/input_l1a_de/${odir}}"
  ofile="${ofile/.cdf/}"

  echo "Output file base: $ofile"

  ./run_read_l1a.sh "$file" "$hkfile" "$ofile" "$goodtime_file"

done


# ----------------------------------------------------------------------
# Consolidate per-ESA outputs
# ----------------------------------------------------------------------

for esa in {1..7}; do
    files=( "$odir"/*_ESA${esa}.csv )
    outfile="${odir}/TOF_select_ESA${esa}.csv"

    in_files=()
    for f in "${files[@]}"; do
        [ -f "$f" ] || continue
        [[ "$f" == "$outfile" ]] && continue
        in_files+=( "$f" )
    done

    (( ${#in_files[@]} == 0 )) && continue

    head -n 1 "${in_files[0]}" > "$outfile"

    for f in "${in_files[@]}"; do
        awk 'FNR>1' "$f" >> "$outfile"
    done

    rm -f "${in_files[@]}"
done


# ----------------------------------------------------------------------
# Consolidate all ESA files
# ----------------------------------------------------------------------

files=( "$odir"/TOF_select_ESA*.csv )

real_files=()
for f in "${files[@]}"; do
    [ -f "$f" ] && real_files+=( "$f" )
done

(( ${#real_files[@]} == 0 )) && exit 0

outfile="$odir/TOF_select.csv"

head -n 1 "${real_files[0]}" > "$outfile"

for f in "${real_files[@]}"; do
    awk 'FNR>1' "$f" >> "$outfile"
done


# ----------------------------------------------------------------------
# Copy goodtime ideas file and make report
# ----------------------------------------------------------------------

cp "$goodtimes_ideas" "$odir"

ofile="$odir/TOF_select.csv"
datadir="$odir"
file="$goodtime_file"

bin=$(cut -d',' -f6  "$file" | sed -n '2p')
bin0=$(cut -d',' -f19 "$file" | sed -n '2p')
bin1=$(cut -d',' -f22 "$file" | sed -n '2p')
bin2=$(cut -d',' -f25 "$file" | sed -n '2p')
bin3=$(cut -d',' -f28 "$file" | sed -n '2p')

./runIMAP-emv3-instrument-report.sh \
  "$ofile" "$datadir" "$bin" "$bin0" "$bin1" "$bin2" "$bin3"


# ----------------------------------------------------------------------
# Sync to Dropbox quicklook
# ----------------------------------------------------------------------

rsync -av --ignore-existing ./ /Users/nschwadron/Dropbox/IMAP-Lo/quicklook/1S25_l1a_TOFideas/
