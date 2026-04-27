[ -z "$1" ] || file=$1
[ -z "$2" ] || output=$2

if [ -z "$1" ]
then
    echo "runIMAP-fmv1_convert_tofdn.sh takes 52 arguments to convert the events"

else

    #python=/opt/homebrew/bin/python3
    python=python3.11
    pydir=./

#    echo "Running Rate: $fileRAWCNT"
#    $python $pydir/calcEfficiencies-RATE-TOF-BD.py -f $fileRAWCNT -b $fileTOFBD -m $mcpLo $mcpHi > "$outdir"/mcpGainReport.txt
    
    echo "   l1c_reader.py input:" $file
    echo "   l1c_reader.py output:" $output
    
    $python $pydir/l1c_reader.py -f $file -o $output 

fi
