[ -z "$1" ] || delaytime=$1

input=../input_l1b_histrates

# Check if the target is a directory
if [ ! -d "$input" ]; then
  echo "1S05_l1b_histRates_plots Error: Directory '$directory' not found."
  exit 1
fi

# for file in "$input"/*; do
find "$input" -maxdepth 1 -type f -name "*.cdf" -mtime "$delaytime" -print0 | while IFS= read -r -d '' file; do


  # Check if the current item is a regular file (not a directory or other type)
    if [ -f "$file" ]; then
      echo "1S05_l1b_histRates_plots Processing hist file: $file"
    fi

    ./runIMAP-fmv1-autogt.sh "$file" 
done

