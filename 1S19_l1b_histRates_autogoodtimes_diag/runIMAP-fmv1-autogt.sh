[ -z "$1" ] || file=$1
[ -z "$2" ] || file_de=$2
[ -z "$3" ] || file_hk=$3
[ -z "$4" ] || output=$4
[ -z "$5" ] || tnom=$5
[ -z "$6" ] || toff=$6

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
    echo "input de:" $file_de
    echo "input hk:" $file_hk
    echo "output:" $output
    
    $python $pydir/hist_auto_gt.py -f $file -e $file_de -k $file_hk -o $output -n 7 -t90 $tnom -toff $toff

fi
