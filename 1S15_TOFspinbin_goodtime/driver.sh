[ -z "$1" ] || delaytime=$1

input=../input_de
output=./output
#input=./input
goodtime_file=../input_goodtime/imap_lo_goodtimes.csv

# Check if the target is a directory
if [ ! -d "$input" ]; then
  echo "Error 1S15: Directory '$directory' not found."
  exit 1
fi

#for file in "$input"/*.cdf; do
#find "$input" -maxdepth 1 -type f -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do
find "$input" -maxdepth 1 -type f -name "*.cdf" -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do

  # Check if the current item is a regular file (not a directory or other type)
  if [ -f "$file" ]; then
      echo "1S15 Processing file: $file"
  fi

  ofile="${file/#..\/input_de/./output}"
  ofile="${ofile/.cdf/}"

    datadirH="${ofile}_H"
  [ -d "$datadirH" ] || mkdir "$datadirH"

  datadirCO="${ofile}_CO"
  [ -d "$datadirCO" ] || mkdir "$datadirCO"

  ofileH="${datadirH}/Direct_Events"
  ofileCO="${datadirCO}/Direct_Events"
  echo "1S15 Output files: $ofileH $ofileCO"

  ./runIMAP_fmv1_read_l1b_de.sh "$file" "$ofileH" "$ofileCO" "$goodtime_file"

#  ./runIMAP-emv3-instrument-report.sh "$ofile" "$datadir"

    odir="${datadirH}"
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
    #(( ${#files[@]} == 0 )) && exit 0
    if (( ${#files[@]} > 0 )); then

        outfile="${odir}/TOF_select.csv"

        head -n 1 "${files[0]}" > "$outfile"
        for f in "${files[@]}"; do
            awk 'FNR>1' "$f" >> "$outfile"
        done

        ofile="$odir/TOF_select.csv"
        datadir="$odir"
        
        nlines=$(wc -l < "${ofile}")
        if (( ${nlines} > 3)); then
            ./runIMAP-emv3-instrument-report.sh "$ofile" "$datadir" "60" "100" "100" "100" "20" 
        fi

    fi


    odir="${datadirCO}"
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
    #(( ${#files[@]} == 0 )) && exit 0
    if (( ${#files[@]} > 0 )); then

        outfile="$odir/TOF_select.csv"

        head -n 1 "${files[0]}" > "$outfile"
        for f in "${files[@]}"; do
            awk 'FNR>1' "$f" >> "$outfile"
        done

        ofile="$odir/TOF_select.csv"
        datadir="$odir"
        nlines=$(wc -l < "${ofile}")
        if (( ${nlines} > 3)); then
            ./runIMAP-emv3-instrument-report.sh "$ofile" "$datadir" "60" "100" "100" "100" "20" 
        fi
    fi

done
