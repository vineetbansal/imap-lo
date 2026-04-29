[ -z "$1" ] || file=$1
[ -z "$2" ] || file_de=$2
[ -z "$3" ] || file_hk=$3

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
    
    echo "1S04 input:" $file
    echo "1S04 input de:" $file_de
    echo "1S04 input hk:" $file_hk

    $python $pydir/hist_auto_gt_V3.py -f $file -e $file_de -k $file_hk -n 1 -a 7 -d 100 -t90 0.007 -toff 0.00875 -tram90 0.014 -tramoff 0.0175
    $python ../scripts/02autogt_convert.py $file $file_de $file_hk output2
    # $python $pydir/hist_auto_gt_V2.py -f $file -e $file_de -k $file_hk -n 1 -a 7 -d 100 -t90 0.007 -toff 0.00875
    # use 0.0042 in ram direction and 1.5 x 0.0042 combined for ESA 6 & 7 cut out whole spin
    # use 0.00525 s-1 for 75 & 105 deg 

fi
