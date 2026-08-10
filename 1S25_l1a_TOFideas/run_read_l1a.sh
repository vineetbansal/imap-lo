#!/bin/bash

l1afile="$1"
hkfile="$2"
ofile="$3"
goodtime_file="$4"

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
    
    echo "  IDEAS input:" $l1afile
    echo "  IDEAS output:" $ofile
    
    $python read_l1a_de_ideas.py \
        -f "$l1afile" \
        -k "$hkfile" \
        -o "$ofile" \
        -g "$goodtime_file"

fi
