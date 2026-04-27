[ -z "$1" ] || file=$1
[ -z "$2" ] || file_scpos=$2
[ -z "$3" ] || file_gtcontext=$3
[ -z "$4" ] || output=$4

if [ -z "$1" ]
then
    echo "runIMAP-fmv1_convert_tofdn.sh takes 52 arguments to convert the events"

else

    #python=/opt/homebrew/bin/python3
    python=python3.11
    #python=python3
    pydir=./

#    outd="$outdir"/gain_report

#   echo "Analyzing: $fileDE over TOF range and using $fileTOFBD for TOF MCP vals  "
#    echo " ... "

#    echo "outdir = $outdir"
#    mkdir -p "$outd"
    
#    echo "Running Rate: $fileRAWCNT"
#    $python $pydir/calcEfficiencies-RATE-TOF-BD.py -f $fileRAWCNT -b $fileTOFBD -m $mcpLo $mcpHi > "$outdir"/mcpGainReport.txt
    
    echo "input:" $file
    echo "input sc position:" $file_scpos
    echo "input gt context:" $file_gtcontext
    echo "output:" $output
    
    # note that output assumes no .csv .. star_ppm_105 for instance
    $python makePointing_stars_V3-105.py -o $output -f ./catalog_Vt_7.csv -s $file -p $file_scpos -g $file_gtcontext -r 0.4 -m 5 -n 1. -xmax 360
  #  $python $pydir/star_cdf.py -s $file -k $file_hk -o $output 

fi
