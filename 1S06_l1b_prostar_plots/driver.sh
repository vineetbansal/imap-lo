[ -z "$1" ] || delaytime=$1

input=../input_prostar
input_hk=../input_hk
output=./output

# Check if the target is a directory
if [ ! -d "$input" ]; then
  echo "1S06_l1b_prostar_plots Error: Directory '$directory' not found."
  exit 1
fi

# for file in "$input"/*; do
find "$input" -maxdepth 1 -type f -name "*.cdf" -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do

  key=$(basename "$file" | grep -oE '_[0-9]{8}-repoint')

  match=$(ls "$input_hk"/*"$key"* 2>/dev/null | head -n 1)


  if [[ -n "$match" ]]; then
    echo " 1S06_l1b_prostar_plots MATCH (DE):"
    echo "  hist = $file"
    echo "  HK   = $match"

  # Check if the current item is a regular file (not a directory or other type)
    if [ -f "$file" ]; then
      echo "1S06_l1b_prostar_plots Processing l1b  prostar file: $file"
    fi

    if [ -f "$match" ]; then
      echo "1S06_l1b_prostar_plots Processing l1b HK file: $match"
    fi

  else
    echo "1S06_l1b_prostar_plots NO MATCH for $file"
    match="$file"
  fi

  ofile="${file/#..\/input_prostar/./output}"
#  ofile="${file/../input_prostar/./output}"
  ofile="${ofile/.cdf/}"
  echo "1S06_l1b_prostar_plots Output GT file: $ofile"

  ./runIMAP-fmv1-prostar.sh "$file" "$match" "$ofile" 
  
done



