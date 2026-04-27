[ -z "$1" ] || file=$1
[ -z "$2" ] || datdir=$2

# source "../bash_functions/montage_utils.sh"

if [ -z "$1" ]
then
    echo "runIMAP-emv2-report.sh takes 2 arguments to run through direct events and make plots"
    echo "   arg1: direct event file name"
    echo "   arg2: data diretory"
    echo "example:"
    echo " ./runIMAP-emv2-report.sh Control_EM_EMv2c_T012_PSPL_R002_P10_M31_eStep7_DRK_TOF_DE_sample_20230516T174214_ ../../T012/run001"
else

    [ -d "$datdir"/"tof_report" ] || mkdir "$datdir"/"tof_report"

    ofile="$datdir"/"tof_report"/"EMv3"
    odir="$datdir"/"tof_report"
    #python=/opt/homebrew/bin/python3
    python=python3.11
    pydir=./
    echo "Analyzing: $file ... "
    echo " ... "

    mkdir -p $odir

    oneDPlot="$pydir"/"showIMAPLo-DE-1DTOF_V2.py"
    twoDPlot="$pydir"/"showIMAPLo-DE-2DTOF_V2.py"
    delay="$pydir"/"showIMAPLo-DE-delay_V2.py"
    checksum="$pydir"/"showIMAPLo-DE-CheckDist1D_V1.py"
    
    $python $oneDPlot -f $file -o "$ofile-11111" -t 0 -v 1 1 1 1 1 -xmax 330 -b 100 -ymin 0.8 
    $python $oneDPlot -f $file -o "$ofile-11111" -t 1 -v 1 1 1 1 1 -xmax 200 -b 100 -ymin 0.8 
    $python $oneDPlot -f $file -o "$ofile-11111" -t 2 -v 1 1 1 1 1 -xmax 160 -b 100 -ymin 0.8 
    files=$(for e in {1..3}; do for t in 0 1 2; do f="$ofile-11111TOF${t}ESA${e}.png"; [[ -f $f ]] && printf '%s ' "$f"; done; done); [[ -n $files ]] && montage $files -tile 3x3 -geometry +0+0 "$odir/p01.png"
    files=$(for e in {4..6}; do for t in 0 1 2; do f="$ofile-11111TOF${t}ESA${e}.png"; [[ -f $f ]] && printf '%s ' "$f"; done; done); [[ -n $files ]] && montage $files -tile 3x3 -geometry +0+0 "$odir/p02.png"
    files=(); for e in {7..7}; do for t in 0 1 2; do f="$ofile-11111TOF${t}ESA${e}.png"; [[ -f $f ]] && files+=("$f"); done; done; (( ${#files[@]} > 0 )) && montage "${files[@]}" -tile 3x1 -geometry +0+0 "$odir/p03.png"
        
    $python $oneDPlot -f $file -o "$ofile-11111" -t 0 -v 1 1 1 1 1 -s 1 -xmax 330 -b 100 -ymin 0.8 
    $python $oneDPlot -f $file -o "$ofile-11111" -t 1 -v 1 1 1 1 1 -s 1 -xmax 200 -b 100 -ymin 0.8 
    files=$(for e in {1..3}; do for t in 0 1; do f="$ofile-11111TOF${t}sESA${e}.png"; [[ -f $f ]] && printf '%s ' "$f"; done; done); [[ -n $files ]] && montage $files -tile 2x3 -geometry +0+0 "$odir/p04.png"
    files=$(for e in {4..6}; do for t in 0 1; do f="$ofile-11111TOF${t}sESA${e}.png"; [[ -f $f ]] && printf '%s ' "$f"; done; done); [[ -n $files ]] && montage $files -tile 2x3 -geometry +0+0 "$odir/p05.png"
    files=(); for e in {7..7}; do for t in 0 1; do f="$ofile-11111TOF${t}sESA${e}.png"; [[ -f $f ]] && files+=("$f"); done; done; (( ${#files[@]} > 0 )) && montage "${files[@]}" -tile 2x1 -geometry +0+0 "$odir/p06.png"
   
#    files=$(do for t in 0 1; do f="$ofile-11111TOF${t}sESA$7.png"; [[ -f $f ]] && printf '%s ' "$f"; done); [[ -n $files ]] && montage $files -tile 2x1 -geometry +0+0 "$odir/p06.png"
    echo " 1S08 Done with Triples 1D plots! "
    echo "       ... "
#    montage "$ofile-10010TOF0.png" "$ofile-01010TOF1.png" "$ofile-00110TOF2.png" -tile 3x1 -geometry +0+0  "$odir"/"p02.png"
    
    $python $oneDPlot -f $file -o "$ofile-10010" -t 0 -v 1 0 0 1 0 -s 1 -xmax 330 -b 150 -ymin 0.8 
    $python $oneDPlot -f $file -o "$ofile-01010" -t 1 -v 0 1 0 1 0 -s 1 -xmax 200 -b 150 -ymin 0.8 
#    montage "$ofile-10010TOF0s.png" "$ofile-01010TOF1s.png" -tile 2x1 -geometry +0+0  "$odir"/"s02.png"
    
    echo " 1S08 Done with Doubles 1D plots! "
    echo " ... "

    $python $oneDPlot -f $file -o "$ofile-10010-hi" -t 0 -v 1 0 0 1 0 -s 1 -xmax 50 -b 300 -ymin 0.8 
    $python $oneDPlot -f $file -o "$ofile-01010-hi" -t 1 -v 0 1 0 1 0 -s 1 -xmax 30 -b 300 -ymin 0.8 
#    montage "$ofile-10010-hiTOF0s.png" "$ofile-01010-hiTOF1s.png" -tile 2x1 -geometry +0+0  "$odir"/"s03.png"
    
    echo " 1S08 Done with HiRes Doubles 1D plots! "
    echo " ... "


    $python $delay -f $file -o "$ofile-11110" -v 1 1 1 1 0 
    $python $delay -f $file -o "$ofile-11111" -v 1 1 1 1 1 
    files=$(for e in {1..7}; do f="$ofile-11111ESA${e}.png"; [[ -f $f ]] && printf '%s ' "$f"; done); [[ -n $files ]] && montage $files -tile 3x3 -geometry +0+0 "$odir/p07.png"
  

    $python $twoDPlot -f $file -o "$ofile-11111" -tx 0 -ty 1 -v 1 1 1 1 1 -s 1 -xmax 330 -b 200 -ymax 210
    $python $twoDPlot -f $file -o "$ofile-11111" -tx 0 -ty 2 -v 1 1 1 1 1 -s 1 -xmax 330 -b 200 -ymax 150 
    files=$(for e in {1..3}; do
        for s in "0svsTOF1s" "0svsTOF2"; do
            f="$ofile-11111ESA${e}TOF${s}.png"
            [[ -f $f ]] && printf '%s ' "$f"
        done
    done); \
    [[ -n $files ]] && montage $files -tile 2x3 -geometry +0+0 "$odir/p08.png" || echo "1S08 No files for p08"

    files=$(for e in {4..6}; do
        for s in "0svsTOF1s" "0svsTOF2"; do
            f="$ofile-11111ESA${e}TOF${s}.png"
            [[ -f $f ]] && printf '%s ' "$f"
        done
    done); \
    [[ -n $files ]] && montage $files -tile 2x3 -geometry +0+0 "$odir/p09.png" || echo "1S08 No files for p09"

    files=$(for e in {7..7}; do
        for s in "0svsTOF1s" "0svsTOF2"; do
            f="$ofile-11111ESA${e}TOF${s}.png"
            [[ -f $f ]] && printf '%s ' "$f"
        done
    done); \
    [[ -n $files ]] && montage $files -tile 2x1 -geometry +0+0 "$odir/p10.png" || echo "1S08 No files for p10"


    $python $oneDPlot -f $file -o "$ofile-10000nf" -t 0 -v 1 0 0 0 0 -xmax 330 -b 150 -ymin 0.8 
    $python $oneDPlot -f $file -o "$ofile-01000nf" -t 1 -v 0 1 0 0 0 -xmax 200 -b 150 -ymin 0.8 
    $python $oneDPlot -f $file -o "$ofile-00100nf" -t 2 -v 0 0 1 0 0 -xmax 160 -b 150 -ymin 0.8 
  #  montage "$ofile-10000nfTOF0.png" "$ofile-01000nfTOF1.png" "$ofile-00100nfTOF2.png" -tile 3x1 -geometry +0+0  "$odir"/"p07.png"
    echo " Done with Singles 1D plots (no filter)! "
    
    $python $oneDPlot -f $file -o "$ofile-11000nf" -t 0 -v 1 1 0 0 0 -xmax 330 -b 150 -ymin 0.8 
    $python $oneDPlot -f $file -o "$ofile-11000nf" -t 1 -v 1 1 0 0 0 -xmax 200 -b 150 -ymin 0.8 
    $python $oneDPlot -f $file -o "$ofile-01100nf" -t 2 -v 0 1 1 0 0 -xmax 160 -b 150 -ymin 0.8 
  #  montage "$ofile-11000nfTOF0.png" "$ofile-11000nfTOF1.png" "$ofile-01100nfTOF2.png" -tile 3x1 -geometry +0+0  "$odir"/"p08.png"
    
    $python $oneDPlot -f $file -o "$ofile-10100nf" -t 0 -v 1 0 1 0 0 -xmax 330 -b 150 -ymin 0.8 
    $python $oneDPlot -f $file -o "$ofile-01100nf" -t 1 -v 0 1 1 0 0 -xmax 200 -b 150 -ymin 0.8 
    $python $oneDPlot -f $file -o "$ofile-10100nf" -t 2 -v 1 0 1 0 0 -xmax 160 -b 150 -ymin 0.8 


    $python $oneDPlot -f $file -o "$ofile-10010nf" -t 0 -v 1 0 0 1 0 -s 1 -xmax 330 -b 150 -ymin 0.8 
    $python $oneDPlot -f $file -o "$ofile-01010nf" -t 1 -v 0 1 0 1 0 -s 1 -xmax 200 -b 150 -ymin 0.8 
  #  montage "$ofile-10010nfTOF0s.png" "$ofile-01010nfTOF1s.png" -tile 2x1 -geometry +0+0  "$odir"/"s10.png"

    echo " 1S08 ... "

    $python $oneDPlot -f $file -o "$ofile-11010nf" -t 0 -v 1 1 0 1 0 -s 1 -xmax 330 -b 150 -ymin 0.8 
    $python $oneDPlot -f $file -o "$ofile-11010nf" -t 1 -v 1 1 0 1 0 -s 1 -xmax 200 -b 150 -ymin 0.8 
    $python $oneDPlot -f $file -o "$ofile-10110nf" -t 0 -v 1 0 1 1 0 -s 1 -xmax 330 -b 150 -ymin 0.8 
    $python $oneDPlot -f $file -o "$ofile-01110nf" -t 1 -v 0 1 1 1 0 -s 1 -xmax 200 -b 150 -ymin 0.8 
    $python $oneDPlot -f $file -o "$ofile-11110nf" -t 0 -v 1 1 1 1 0 -s 1 -xmax 330 -b 150 -ymin 0.8 
    $python $oneDPlot -f $file -o "$ofile-11110nf" -t 1 -v 1 1 1 1 0 -s 1 -xmax 200 -b 150 -ymin 0.8 
    files=$(for e in {1..3}; do for t in 0 1; do f="$ofile-11110nfTOF${t}sESA${e}.png"; [[ -f $f ]] && printf '%s ' "$f"; done; done); [[ -n $files ]] && montage $files -tile 2x3 -geometry +0+0 "$odir/p11.png"
    files=$(for e in {4..6}; do for t in 0 1; do f="$ofile-11110nfTOF${t}sESA${e}.png"; [[ -f $f ]] && printf '%s ' "$f"; done; done); [[ -n $files ]] && montage $files -tile 2x3 -geometry +0+0 "$odir/p12.png"
    files=(); for e in {7..7}; do for t in 0 1; do f="$ofile-11110nfTOF${t}sESA${e}.png"; [[ -f $f ]] && files+=("$f"); done; done; (( ${#files[@]} > 0 )) && montage "${files[@]}" -tile 2x1 -geometry +0+0 "$odir/p13.png"

    $python $checksum -f $file -o "$ofile-checksum_0_15-" -t 2 -tmin 0 -tmax 15 -b 2000 -xmin -1000 -xmax 1000 -dn 1 -at 1 
    $python $checksum -f $file -o "$ofile-checksum_15_35-" -t 2 -tmin 15 -tmax 35 -b 2000 -xmin -1000 -xmax 1000 -dn 1 -at 1
    $python $checksum -f $file -o "$ofile-checksum_35_150-" -t 2 -tmin 35 -tmax 150 -b 2000 -xmin -1000 -xmax 1000 -dn 1 -at 1
    
    files=$(for e in {1..7}; do f="$ofile-checksum_0_15-ESA${e}TOF2.png"; [[ -f $f ]] && printf '%s ' "$f"; done); [[ -n $files ]] && montage $files -tile 3x3 -geometry +0+0 "$odir/p14.png"
    files=$(for e in {1..7}; do f="$ofile-checksum_15_35-ESA${e}TOF2.png"; [[ -f $f ]] && printf '%s ' "$f"; done); [[ -n $files ]] && montage $files -tile 3x3 -geometry +0+0 "$odir/p15.png"
    files=$(for e in {1..7}; do f="$ofile-checksum_35_150-ESA${e}TOF2.png"; [[ -f $f ]] && printf '%s ' "$f"; done); [[ -n $files ]] && montage $files -tile 3x3 -geometry +0+0 "$odir/p16.png"
  
    $python $checksum -f $file -o "$ofile-checksum_0_15-HiRes-" -t 2 -tmin 0 -tmax 15 -b 30 -xmin -15 -xmax 15 -dn 1 -at 1 
    $python $checksum -f $file -o "$ofile-checksum_15_35-HiRes-" -t 2 -tmin 15 -tmax 35 -b 30 -xmin -15 -xmax 15 -dn 1 -at 1 
    $python $checksum -f $file -o "$ofile-checksum_35_150-HiRes-" -t 2 -tmin 35 -tmax 150 -b 30 -xmin -15 -xmax 15 -dn 1 -at 1 
    
    files=$(for e in {1..7}; do f="$ofile-checksum_0_15-HiRes-ESA${e}TOF2.png"; [[ -f $f ]] && printf '%s ' "$f"; done); [[ -n $files ]] && montage $files -tile 3x3 -geometry +0+0 "$odir/p17.png"
    files=$(for e in {1..7}; do f="$ofile-checksum_15_35-HiRes-ESA${e}TOF2.png"; [[ -f $f ]] && printf '%s ' "$f"; done); [[ -n $files ]] && montage $files -tile 3x3 -geometry +0+0 "$odir/p18.png"
    files=$(for e in {1..7}; do f="$ofile-checksum_35_150-HiRes-ESA${e}TOF2.png"; [[ -f $f ]] && printf '%s ' "$f"; done); [[ -n $files ]] && montage $files -tile 3x3 -geometry +0+0 "$odir/p19.png"

    shopt -s nullglob  # ensures empty globs expand to nothing instead of the literal pattern
    files=( "$odir"/p??.png )

    if (( ${#files[@]} > 0 )); then
        magick "${files[@]}" "$odir"/tof_report.pdf
    else
        echo "1S08: No pages found, skipping PDF generation."
    fi

fi
