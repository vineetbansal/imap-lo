[ -z "$1" ] || file=$1
[ -z "$2" ] || file_de=$2
[ -z "$3" ] || file_hk=$3
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
    
    echo "   3S2_l1b_histRates_autoram  hist_auto_ram.py input:" $file
    echo "   3S2_l1b_histRates_autoram  hist_auto_ram.py input de:" $file_de
    echo "   3S2_l1b_histRates_autoram  hist_auto_ram.py input hk:" $file_hk
    echo "   3S2_l1b_histRates_autoram  hist_auto_ram.py output:" $output
    
    $python $pydir/hist_auto_ram_V2.py -f $file -e $file_de -k $file_hk -o $output -n 7 -d 440

fi
