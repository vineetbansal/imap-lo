[ -z "$1" ] || delaytime=$1

input=../input_de
#input=./input
goodtime_file=../input_goodtime/imap_lo_goodtimes.csv
output=./output

# Check if the target is a directory
if [ ! -d "$input" ]; then
  echo "1S09_TOFreport_GoodTimes Error: Directory '$directory' not found."
  exit 1
fi

# for file in "$input"/*; do
#find "$input" -maxdepth 1 -type f -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do
find "$input" -maxdepth 1 -type f -name "*.cdf" -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do

  # Check if the current item is a regular file (not a directory or other type)
  if [ -f "$file" ]; then
      echo "1S09_TOFreport_GoodTimes Processing file: $file"
  fi

  ofile="${file/#..\/input_de/./output}"
#  ofile="${file/input/output}"
  ofile="${ofile/.cdf/.csv}"
  echo "1S09_TOFreport_GoodTimes Output H file: $ofile"

 ./runIMAP_fmv1_read_l1b_de.sh "$file" "$ofile" "$goodtime_file"

  datadir="${ofile/.csv/}"
  [ -d "$datadir" ] || mkdir "$datadir"

  if [ -n "$(tail -n +2 "$ofile" | head -n 1)" ]; then
    ./runIMAP-emv3-instrument-report.sh "$ofile" "$datadir"
  fi
  
done

