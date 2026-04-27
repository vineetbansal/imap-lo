[ -z "$1" ] || goodtimes_ideas=$1

input=../input_de
# for local debugging
# input=./input_de

#input=./input
goodtime_file=$goodtimes_ideas


oselect="${goodtime_file/.csv/}"
odir="./output/${oselect}"
[ -d "$odir" ] || mkdir "$odir"

# Check if the target is a directory
if [ ! -d "$input" ]; then
  echo "Error: Directory '$directory' not found."
  exit 1
fi

for file in "$input"/*.cdf; do
#find "$input" -maxdepth 1 -type f -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do

  # Check if the current item is a regular file (not a directory or other type)
  if [ -f "$file" ]; then
      echo "Processing file: $file"
  fi

    ofile="${file/#..\/input_de/${odir}}"

# for local debugging
#  ofile="${file/#.\/input_de/${odir}}"
#  ofile="${file/input/output}"
  ofile="${ofile/.cdf/}"
  echo "Output file: $ofile"

  ./runIMAP_fmv1_read_l1b_de.sh "$file" "$ofile" "$goodtime_file"

  datadir="${odir}"
#  [ -d "$datadir" ] || mkdir "$datadir"

#  ./runIMAP-emv3-instrument-report.sh "$ofile" "$datadir"

done


for esa in {1..7}; do
    files=( "$odir"/*_ESA${esa}.csv )
    outfile="${odir}/TOF_select_ESA${esa}.csv"

    # build list without the outfile
    in_files=()
    for f in "${files[@]}"; do
        [[ "$f" == "$outfile" ]] && continue
        in_files+=( "$f" )
    done

    (( ${#in_files[@]} == 0 )) && continue

    # write header
    head -n 1 "${in_files[0]}" > "$outfile"

    # append data
    for f in "${in_files[@]}"; do
        awk 'FNR>1' "$f" >> "$outfile"
    done

    # delete originals
    rm -f "${in_files[@]}"
done

files=( "$odir"/TOF_select_ESA*.csv )
(( ${#files[@]} == 0 )) && exit 0

outfile="$odir/TOF_select.csv"

head -n 1 "${files[0]}" > "$outfile"
for f in "${files[@]}"; do
    awk 'FNR>1' "$f" >> "$outfile"
done

cp $goodtimes_ideas "$odir"

ofile="$odir/TOF_select.csv"
datadir="$odir"
file=$goodtime_file
bin=$(cut -d',' -f6 "${file}" | sed -n '2p')
bin0=$(cut -d',' -f19 "${file}" | sed -n '2p')
bin1=$(cut -d',' -f22 "${file}" | sed -n '2p')
bin2=$(cut -d',' -f25 "${file}" | sed -n '2p')
bin3=$(cut -d',' -f28 "${file}" | sed -n '2p')

#-d',' → comma delimiter
#-f19 → column 19
#sed -n '2p' → grabs row 2 (skip header)

./runIMAP-emv3-instrument-report.sh "$ofile" "$datadir" "$bin" "$bin0" "$bin1" "$bin2" "$bin3" 

rsync -av --ignore-existing ./  /Users/nschwadron/Dropbox/IMAP-Lo/quicklook/1S12_TOFideas/

