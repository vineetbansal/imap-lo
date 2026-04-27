[ -z "$1" ] || delaytime=$1

data=.
#ident=Instrument_FM1_play
ident=Instrument_FM1_ilo_hvsci_

input=../input_l1b_histrates
output=./output
goodtime_file=../input_goodtime/imap_lo_goodtimes.csv

# Check if the target is a directory
if [ ! -d "$input" ]; then
  echo "1S10 Error: Directory '$directory' not found."
  exit 1
fi

# for file in "$input"/*; do
find "$input" -maxdepth 1 -type f -name "*.cdf" -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do

  # Check if the current item is a regular file (not a directory or other type)
  if [ -f "$file" ]; then
      echo "1S10 Processing file: $file"
  fi

  datadir="${ofile/.csv/}"
  [ -d "$datadir" ] || mkdir "$datadir"

#  ofile="${file/input/output}"
  ofile="${file/#..\/input_l1b_histrates/./output}"
  ofile="${ofile/.cdf/}"
  datadir="${ofile}"

  echo "1S10 Output H file: $ofile"

  ./runIMAP-fmv1-convert-hist.sh "$file" "$ofile" "$goodtime_file"

  [ -d "$datadir" ] || mkdir "$datadir"
  mv "$ofile"*.csv "$datadir" 
  rm -f "$ofile"*.csv

done

