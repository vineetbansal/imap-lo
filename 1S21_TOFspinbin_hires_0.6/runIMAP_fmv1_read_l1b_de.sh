[ -z "$1" ] || file=$1
[ -z "$2" ] || outputH=$2
[ -z "$3" ] || outputCO=$3

if [ -z "$1" ]
then
    echo "runIMAP-fmv1_convert_tofdn.sh takes 52 arguments to convert the events"

else

    #python=/opt/homebrew/bin/python3
    python=python3.11
    pydir=./

#    outd="$outdir"/gain_report

#   echo "Analyzing: $fileDE over TOF range and using $fileTOFBD for TOF MCP vals  "
#    echo " ... "

#    echo "outdir = $outdir"
#    mkdir -p "$outd"
    
#    echo "Running Rate: $fileRAWCNT"
#    $python $pydir/calcEfficiencies-RATE-TOF-BD.py -f $fileRAWCNT -b $fileTOFBD -m $mcpLo $mcpHi > "$outdir"/mcpGainReport.txt
    
    echo "  input:" $file
    echo "  H output:" $outputH
    echo "  CO output:" $outputCO

    $python $pydir/read_de.py -f $file -o $outputH -s 0 
    $python $pydir/read_de.py -f $file -o $outputCO -s 1

fi
