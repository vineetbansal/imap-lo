[ -z "$1" ] || delaytime=$1

input=../input_de
output=./output

if [ ! -d "$input" ]; then
  echo "1S08_TOFreport_AllTimes Error: Directory '$input' not found."
  exit 1
fi
find "$input" -maxdepth 1 -type f -name "*.cdf" -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do
  echo "1S08_TOFreport_AllTimes Processing file: $file"

  ofile="${file/#..\/input_de/./output}"
  ofile="${ofile/.cdf/.csv}"
  echo "1S08_TOFreport_AllTimes Output H file: $ofile"

  ./runIMAP_fmv1_read_l1b_de.sh "$file" "$ofile"

  datadir="${ofile/.csv/}"
  [ -d "$datadir" ] || mkdir "$datadir"

   if [ -n "$(tail -n +2 "$ofile" | head -n 1)" ]; then
    ./runIMAP-emv3-instrument-report.sh "$ofile" "$datadir"
   fi

done