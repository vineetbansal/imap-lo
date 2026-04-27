[ -z "$1" ] || file=$1
[ -z "$2" ] || file_hk=$2
[ -z "$3" ] || output=$3

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
    echo "input hk:" $file_hk
    echo "output:" $output
    
    $python $pydir/star_cdf.py -s $file -k $file_hk -o $output 

fi
