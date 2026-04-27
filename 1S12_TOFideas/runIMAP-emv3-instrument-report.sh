[ -z "$1" ] || file=$1
[ -z "$2" ] || datdir=$2
[ -z "$3" ] || bin=$3
[ -z "$4" ] || bin0=$4
[ -z "$5" ] || bin1=$5
[ -z "$6" ] || bin2=$6
[ -z "$7" ] || bin3=$7

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
    holecheck="$pydir"/"tofShift-Hunt-DE-TOF_V1.py"
    spinangle="$pydir"/"showIMAPLo-DE-1D-spinbin.py"
    
    $python $oneDPlot -f $file -o "$ofile-00000" -t 0 -v 0 0 0 0 0 -xmax 330 -b 100 -ymin 0.8  -b $bin0
    $python $oneDPlot -f $file -o "$ofile-00000" -t 1 -v 0 0 0 0 0 -xmax 200 -b 100 -ymin 0.8  -b $bin1
    $python $oneDPlot -f $file -o "$ofile-00000" -t 2 -v 0 0 0 0 0 -xmax 160 -b 100 -ymin 0.8  -b $bin2
    files=$(for e in {1..3}; do for t in 0 1 2; do f="$ofile-00000TOF${t}ESA${e}.png"; [[ -f $f ]] && printf '%s ' "$f"; done; done); [[ -n $files ]] && montage $files -tile 3x3 -geometry +0+0 "$odir/p01.png"
    files=$(for e in {4..6}; do for t in 0 1 2; do f="$ofile-00000TOF${t}ESA${e}.png"; [[ -f $f ]] && printf '%s ' "$f"; done; done); [[ -n $files ]] && montage $files -tile 3x3 -geometry +0+0 "$odir/p02.png"
    files=(); for e in {7..7}; do for t in 0 1 2; do f="$ofile-000000TOF${t}ESA${e}.png"; [[ -f $f ]] && files+=("$f"); done; done; (( ${#files[@]} > 0 )) && montage "${files[@]}" -tile 3x1 -geometry +0+0 "$odir/p03.png"

     
    $python $oneDPlot -f $file -o "$ofile-00000" -t 0 -v 0 0 0 0 0 -s 1 -xmax 330 -b 100 -ymin 0.8  -b $bin0
    $python $oneDPlot -f $file -o "$ofile-00000" -t 1 -v 0 0 0 0 0 -s 1 -xmax 200 -b 100 -ymin 0.8  -b $bin1
    files=$(for e in {1..3}; do for t in 0 1; do f="$ofile-00000TOF${t}sESA${e}.png"; [[ -f $f ]] && printf '%s ' "$f"; done; done); [[ -n $files ]] && montage $files -tile 2x3 -geometry +0+0 "$odir/p04.png"
    files=$(for e in {4..6}; do for t in 0 1; do f="$ofile-00000TOF${t}sESA${e}.png"; [[ -f $f ]] && printf '%s ' "$f"; done; done); [[ -n $files ]] && montage $files -tile 2x3 -geometry +0+0 "$odir/p05.png"
    files=(); for e in {7..7}; do for t in 0 1; do f="$ofile-00000TOF${t}sESA${e}.png"; [[ -f $f ]] && files+=("$f"); done; done; (( ${#files[@]} > 0 )) && montage "${files[@]}" -tile 2x1 -geometry +0+0 "$odir/p06.png"

    
    echo " Done with Triples 1D plots! "
    echo " ... "
#    $python $oneDPlot -f $file -o "$ofile-10010" -t 0 -v 1 0 0 1 0 -xmax 330 -b 150 -ymin 0.8 -nf 1 -opt 1
#    $python $oneDPlot -f $file -o "$ofile-01010" -t 1 -v 0 1 0 1 0 -xmax 200 -b 150 -ymin 0.8 -nf 1 -opt 1
#    $python $oneDPlot -f $file -o "$ofile-00110" -t 2 -v 0 0 1 1 0 -xmax 160 -b 150 -ymin 0.8 -nf 1 -opt 1
#    montage "$ofile-10010TOF0.png" "$ofile-01010TOF1.png" "$ofile-00110TOF2.png" -tile 3x1 -geometry +0+0  "$odir"/"p02.png"
    
#    $python $oneDPlot -f $file -o "$ofile-10010" -t 0 -v 1 0 0 1 0 -s 1 -xmax 330 -b 150 -ymin 0.8 -nf 1 -opt 1
#    $python $oneDPlot -f $file -o "$ofile-01010" -t 1 -v 0 1 0 1 0 -s 1 -xmax 200 -b 150 -ymin 0.8 -nf 1 -opt 1
#    montage "$ofile-10010TOF0s.png" "$ofile-01010TOF1s.png" -tile 2x1 -geometry +0+0  "$odir"/"s02.png"
    
    echo " Done with Doubles 1D plots! "
    echo " ... "
#    $python $oneDPlot -f $file -o "$ofile-10010-hi" -t 0 -v 1 0 0 1 0 -xmax 50 -b 300 -ymin 0.8 -nf 1 -opt 1
#    $python $oneDPlot -f $file -o "$ofile-01010-hi" -t 1 -v 0 1 0 1 0 -xmax 30 -b 300 -ymin 0.8 -nf 1 -opt 1
#    $python $oneDPlot -f $file -o "$ofile-00110-hi" -t 2 -v 0 0 1 1 0 -xmax 30 -b 300 -ymin 0.8 -nf 1 -opt 1
#    montage "$ofile-10010-hiTOF0.png" "$ofile-01010-hiTOF1.png" "$ofile-00110-hiTOF2.png"  -tile 3x1 -geometry +0+0  "$odir"/"p03.png"
    
 #   $python $oneDPlot -f $file -o "$ofile-10010-hi" -t 0 -v 1 0 0 1 0 -s 1 -xmax 50 -b 300 -ymin 0.8 -nf 1 -opt 1
 #   $python $oneDPlot -f $file -o "$ofile-01010-hi" -t 1 -v 0 1 0 1 0 -s 1 -xmax 30 -b 300 -ymin 0.8 -nf 1 -opt 1
#    montage "$ofile-10010-hiTOF0s.png" "$ofile-01010-hiTOF1s.png" -tile 2x1 -geometry +0+0  "$odir"/"s03.png"
    
    echo " Done with HiRes Doubles 1D plots! "
    echo " ... "

 #   $python $delay -f $file -o "$ofile-00010" -v 0 0 0 1 0 -nf 1 -opt 1
 #   $python $delay -f $file -o "$ofile-10010" -v 1 0 0 1 0 -nf 1 -opt 1
 #   $python $delay -f $file -o "$ofile-00110" -v 0 0 1 1 0 -nf 1 -opt 1
 #   $python $delay -f $file -o "$ofile-01010" -v 0 1 0 1 0 -nf 1 -opt 1
    $python $delay -f $file -o "$ofile-00000" -v 0 0 0 0 0  -b $bin3
 #   $python $delay -f $file -o "$ofile-21111" -v 2 1 1 1 1 -nf 1 -opt 1
    files=$(for e in {1..7}; do f="$ofile-00000ESA${e}.png"; [[ -f $f ]] && printf '%s ' "$f"; done); [[ -n $files ]] && montage $files -tile 3x3 -geometry +0+0 "$odir/p07.png"
   
  #  montage $ofile-21111ESA[1-7].png -tile 3x3 -geometry +0+0 "$odir/p07.png" 
 #   montage "$ofile-11111.png" "$ofile-10010.png" "$ofile-01010.png" "$ofile-00110.png" -tile 2x2 -geometry +0+0  "$odir"/"p04.png"
 #   echo " Done with standard delay line plots! "
 #   echo " ... "
 #   $python $delay -f $file -o "$ofile-10010-t0gt20" -v 1 0 0 1 0 -tmin 20.0 -nf 1 -opt 1
 #   $python $delay -f $file -o "$ofile-10010-t0lt20" -v 1 0 0 1 0 -tmax 20.0 -nf 1 -opt 1
 #   montage "$ofile-10010-t0gt20.png" "$ofile-10010-t0lt20.png" "$ofile-00010.png" "$ofile-11110.png"  -tile 2x2 -geometry +0+0  "$odir"/"p05.png"
    
#    $python $twoDPlot -f $file -o "$ofile-11111" -tx 0 -ty 1 -v 1 1 1 1 1 -xmax 330 -b 200 -ymax 210 -opt 1
#    $python $twoDPlot -f $file -o "$ofile-11111" -tx 0 -ty 2 -v 1 1 1 1 1 -xmax 330 -b 200 -ymax 150 -opt 1
#    montage "$ofile-11111TOF0vs1.png" "$ofile-11111TOF0vs2.png" -tile 2x1 -geometry +0+0  "$odir"/"p06.png"
    $python $twoDPlot -f $file -o "$ofile-00000" -tx 0 -ty 1 -v 0 0 0 0 0 -s 1 -xmax 330 -b $bin0 -ymax 210 
    $python $twoDPlot -f $file -o "$ofile-00000" -tx 0 -ty 2 -v 0 0 0 0 0 -s 1 -xmax 330 -b $bin0 -ymax 150 
    files=$(for e in {1..3}; do
        for s in "0svsTOF1s" "0svsTOF2"; do
            f="$ofile-00000ESA${e}TOF${s}.png"
            [[ -f $f ]] && printf '%s ' "$f"
        done
    done); \
    [[ -n $files ]] && montage $files -tile 2x3 -geometry +0+0 "$odir/p08.png" || echo "1S08 No files for p08"

    files=$(for e in {4..6}; do
        for s in "0svsTOF1s" "0svsTOF2"; do
            f="$ofile-00000ESA${e}TOF${s}.png"
            [[ -f $f ]] && printf '%s ' "$f"
        done
    done); \
    [[ -n $files ]] && montage $files -tile 2x3 -geometry +0+0 "$odir/p09.png" || echo "1S08 No files for p09"

    files=$(for e in {7..7}; do
        for s in "0svsTOF1s" "0svsTOF2"; do
            f="$ofile-00000ESA${e}TOF${s}.png"
            [[ -f $f ]] && printf '%s ' "$f"
        done
    done); \
    [[ -n $files ]] && montage $files -tile 2x1 -geometry +0+0 "$odir/p10.png" || echo "1S08 No files for p10"

#    echo " Done with 2D plots! "
#    echo " ... "

#    $python $oneDPlot -f $file -o "$ofile-10000nf" -t 0 -v 1 0 0 0 0 -xmax 330 -b 150 -ymin 0.8 -nf 1 -opt 1
#    $python $oneDPlot -f $file -o "$ofile-01000nf" -t 1 -v 0 1 0 0 0 -xmax 200 -b 150 -ymin 0.8 -nf 1 -opt 1
#    $python $oneDPlot -f $file -o "$ofile-00100nf" -t 2 -v 0 0 1 0 0 -xmax 160 -b 150 -ymin 0.8 -nf 1 -opt 1
  #  montage "$ofile-10000nfTOF0.png" "$ofile-01000nfTOF1.png" "$ofile-00100nfTOF2.png" -tile 3x1 -geometry +0+0  "$odir"/"p07.png"
#    echo " Done with Singles 1D plots (no filter)! "
    
#    $python $oneDPlot -f $file -o "$ofile-11000nf" -t 0 -v 1 1 0 0 0 -xmax 330 -b 150 -ymin 0.8 -nf 1 -opt 1
#    $python $oneDPlot -f $file -o "$ofile-11000nf" -t 1 -v 1 1 0 0 0 -xmax 200 -b 150 -ymin 0.8 -nf 1 -opt 1
#    $python $oneDPlot -f $file -o "$ofile-01100nf" -t 2 -v 0 1 1 0 0 -xmax 160 -b 150 -ymin 0.8 -nf 1 -opt 1
  #  montage "$ofile-11000nfTOF0.png" "$ofile-11000nfTOF1.png" "$ofile-01100nfTOF2.png" -tile 3x1 -geometry +0+0  "$odir"/"p08.png"
    
 #   $python $oneDPlot -f $file -o "$ofile-10100nf" -t 0 -v 1 0 1 0 0 -xmax 330 -b 150 -ymin 0.8 -nf 1 -opt 1
 #   $python $oneDPlot -f $file -o "$ofile-01100nf" -t 1 -v 0 1 1 0 0 -xmax 200 -b 150 -ymin 0.8 -nf 1 -opt 1
 #   $python $oneDPlot -f $file -o "$ofile-10100nf" -t 2 -v 1 0 1 0 0 -xmax 160 -b 150 -ymin 0.8 -nf 1 -opt 1
  #  montage "$ofile-10100nfTOF0.png" "$ofile-01100nfTOF1.png" "$ofile-10100nfTOF2.png" -tile 3x1 -geometry +0+0  "$odir"/"p09.png"

#    $python $oneDPlot -f $file -o "$ofile-10010nf" -t 0 -v 1 0 0 1 0 -xmax 330 -b 150 -ymin 0.8 -nf 1 -opt 1
#    $python $oneDPlot -f $file -o "$ofile-01010nf" -t 1 -v 0 1 0 1 0 -xmax 200 -b 150 -ymin 0.8 -nf 1 -opt 1
#    $python $oneDPlot -f $file -o "$ofile-00110nf" -t 2 -v 0 0 1 1 0 -xmax 160 -b 150 -ymin 0.8 -nf 1 -opt 1
  #  montage "$ofile-10010nfTOF0.png" "$ofile-01010nfTOF1.png" "$ofile-00110nfTOF2.png" -tile 3x1 -geometry +0+0  "$odir"/"p10.png"

 #   $python $oneDPlot -f $file -o "$ofile-10010nf" -t 0 -v 1 0 0 1 0 -s 1 -xmax 330 -b 150 -ymin 0.8 -nf 1 -opt 1
 #   $python $oneDPlot -f $file -o "$ofile-01010nf" -t 1 -v 0 1 0 1 0 -s 1 -xmax 200 -b 150 -ymin 0.8 -nf 1 -opt 1
  #  montage "$ofile-10010nfTOF0s.png" "$ofile-01010nfTOF1s.png" -tile 2x1 -geometry +0+0  "$odir"/"s10.png"

    echo " ... "

 #   $python $oneDPlot -f $file -o "$ofile-11010nf" -t 0 -v 1 1 0 1 0 -xmax 330 -b 150 -ymin 0.8 -nf 1 -opt 1
 #   $python $oneDPlot -f $file -o "$ofile-11010nf" -t 1 -v 1 1 0 1 0 -xmax 200 -b 150 -ymin 0.8 -nf 1 -opt 1
 #   $python $oneDPlot -f $file -o "$ofile-01110nf" -t 2 -v 0 1 1 1 0 -xmax 160 -b 150 -ymin 0.8 -nf 1 -opt 1
  #  montage "$ofile-11010nfTOF0.png" "$ofile-11010nfTOF1.png" "$ofile-01110nfTOF2.png" -tile 3x1 -geometry +0+0  "$odir"/"p11.png"

#    $python $oneDPlot -f $file -o "$ofile-11010nf" -t 0 -v 1 1 0 1 0 -s 1 -xmax 330 -b 150 -ymin 0.8 -nf 1 -opt 1
#    $python $oneDPlot -f $file -o "$ofile-11010nf" -t 1 -v 1 1 0 1 0 -s 1 -xmax 200 -b 150 -ymin 0.8 -nf 1 -opt 1
  #  montage "$ofile-11010nfTOF0s.png" "$ofile-11010nfTOF1s.png" -tile 2x1 -geometry +0+0  "$odir"/"s11.png"


#    $python $oneDPlot -f $file -o "$ofile-10110nf" -t 0 -v 1 0 1 1 0 -xmax 330 -b 150 -ymin 0.8 -nf 1 -opt 1
#    $python $oneDPlot -f $file -o "$ofile-01110nf" -t 1 -v 0 1 1 1 0 -xmax 200 -b 150 -ymin 0.8 -nf 1 -opt 1
#    $python $oneDPlot -f $file -o "$ofile-10110nf" -t 2 -v 1 0 1 1 0 -xmax 160 -b 150 -ymin 0.8 -nf 1 -opt 1
#    montage "$ofile-10110nfTOF0.png" "$ofile-01110nfTOF1.png" "$ofile-10110nfTOF2.png" -tile 3x1 -geometry +0+0  "$odir"/"p12.png"

#    $python $oneDPlot -f $file -o "$ofile-10110nf" -t 0 -v 1 0 1 1 0 -s 1 -xmax 330 -b 150 -ymin 0.8 -nf 1 -opt 1
#    $python $oneDPlot -f $file -o "$ofile-01110nf" -t 1 -v 0 1 1 1 0 -s 1 -xmax 200 -b 150 -ymin 0.8 -nf 1 -opt 1
#    montage "$ofile-10110nfTOF0s.png" "$ofile-01110nfTOF1s.png" -tile 2x1 -geometry +0+0  "$odir"/"s12.png"

#    $python $oneDPlot -f $file -o "$ofile-11110nf" -t 0 -v 1 1 1 1 0 -xmax 330 -b 150 -ymin 0.8 -nf 1 -opt 1
#    $python $oneDPlot -f $file -o "$ofile-11110nf" -t 1 -v 1 1 1 1 0 -xmax 200 -b 150 -ymin 0.8 -nf 1 -opt 1
#    $python $oneDPlot -f $file -o "$ofile-11110nf" -t 2 -v 1 1 1 1 0 -xmax 160 -b 150 -ymin 0.8 -nf 1 -opt 1
#    montage $ofile-11110TOF[0-2]sESA[1-3].png -tile 3x3 -geometry +0+0 "$odir/p07.png"
#    montage $ofile-11110TOF[0-2]sESA[4-6].png -tile 3x3 -geometry +0+0 "$odir/p08.png"
#    montage $ofile-11110TOF[0-2]sESA7.png     -tile 3x1 -geometry +0+0 "$odir/p09.png"
#    montage "$ofile-11110nfTOF0.png" "$ofile-11110nfTOF1.png" "$ofile-11110nfTOF2.png" -tile 3x1 -geometry +0+0  "$odir"/"p13.png"

#    $python $oneDPlot -f $file -o "$ofile-11110nf" -t 0 -v 1 1 1 1 0 -s 1 -xmax 330 -b 150 -ymin 0.8 -nf 1 -opt 1
#    $python $oneDPlot -f $file -o "$ofile-11110nf" -t 1 -v 1 1 1 1 0 -s 1 -xmax 200 -b 150 -ymin 0.8 -nf 1 -opt 1
#    montage $(for e in {1..3}; do echo $ofile-11110nfTOF{0,1}sESA$e.png; done) -tile 2x3 -geometry +0+0 "$odir/p11.png"
#    montage $(for e in {4..6}; do echo $ofile-11110nfTOF{0,1}sESA$e.png; done) -tile 2x3 -geometry +0+0 "$odir/p12.png"
#    montage $ofile-11110nfTOF[0-1]sESA7.png     -tile 2x1 -geometry +0+0 "$odir/p13.png"

#    $python $delay -f $file -o "$ofile-11110nf" -v 1 1 1 1 0 -nf 1 -opt 1
#    $python $delay -f $file -o "$ofile-11111nf" -v 1 1 1 1 1 -nf 1 -opt 1
#    montage "$ofile-11111nf.png" "$ofile-11110nf.png"  -tile 2x1 -geometry +0+0  "$odir"/"p14.png"

#    $python $delay -f $file -o "$ofile-11010nf" -v 1 1 0 1 0 -nf 1 -opt 1
#    $python $delay -f $file -o "$ofile-10110nf" -v 1 0 1 1 0 -nf 1 -opt 1
#    $python $delay -f $file -o "$ofile-01110nf" -v 0 1 1 1 0 -nf 1 -opt 1
#    montage "$ofile-11010nf.png" "$ofile-10110nf.png" "$ofile-01110nf.png"  -tile 2x2 -geometry +0+0  "$odir"/"p15.png"
    
#    $python $delay -f $file -o "$ofile-00010nf" -v 0 0 0 1 0 -nf 1 -opt 1
#    $python $delay -f $file -o "$ofile-10010nf" -v 1 0 0 1 0 -nf 1 -opt 1
#    $python $delay -f $file -o "$ofile-00110nf" -v 0 0 1 1 0 -nf 1 -opt 1
#    $python $delay -f $file -o "$ofile-01010nf" -v 0 1 0 1 0 -nf 1 -opt 1
#    montage "$ofile-00010nf.png" "$ofile-10010nf.png" "$ofile-00110nf.png" "$ofile-01010nf.png" -tile 2x2 -geometry +0+0  "$odir"/"p16.png"
    
#    $python $delay -f $file -o "$ofile-10010-t0gt20nf" -v 1 0 0 1 0 -tmin 20.0 -nf 1 -opt 1
#    $python $delay -f $file -o "$ofile-10010-t0lt20nf" -v 1 0 0 1 0 -tmax 20.0 -nf 1 -opt 1
#    montage "$ofile-10010-t0gt20nf.png" "$ofile-10010-t0lt20nf.png"  -tile 2x1 -geometry +0+0  "$odir"/"p17.png"
    
#    $python $checksum -f $file -o "$ofile-checksum_0_15-" -t 2 -tmin 0 -tmax 15 -b 100 -xmin -300 -xmax 300 -at 1 -opt 1
#    $python $checksum -f $file -o "$ofile-checksum_15_35-" -t 2 -tmin 15 -tmax 35 -b 100 -xmin -300 -xmax 300 -at 1 -opt 1
#    $python $checksum -f $file -o "$ofile-checksum_35_150-" -t 2 -tmin 35 -tmax 150 -b 100 -xmin -300 -xmax 300 -at 1 -opt 1
    
#    montage "$ofile-checksum_0_15-TOF2.png" "$ofile-checksum_15_35-TOF2.png" "$ofile-checksum_35_150-TOF2.png" -tile 2x2 -geometry +0+0  "$odir"/"p18.png"

#    $python $checksum -f $file -o "$ofile-checksum_0_15-HiRes-" -t 2 -tmin 0 -tmax 15 -b 100 -xmin -5 -xmax 5 -at 1 -opt 1
#    $python $checksum -f $file -o "$ofile-checksum_15_35-HiRes-" -t 2 -tmin 15 -tmax 35 -b 100 -xmin -5 -xmax 5 -at 1 -opt 1
#    $python $checksum -f $file -o "$ofile-checksum_35_150-HiRes-" -t 2 -tmin 35 -tmax 150 -b 100 -xmin -5 -xmax 5 -at 1 -opt 1
    
#    montage "$ofile-checksum_0_15-HiRes-TOF2.png" "$ofile-checksum_15_35-HiRes-TOF2.png" "$ofile-checksum_35_150-HiRes-TOF2.png" -tile 2x2 -geometry +0+0  "$odir"/"p19.png"

#   echo "Doing DN Checksum plots now!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"

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

    $python $spinangle -f $file -o "$ofile-spinangle-" -b $bin -xmin 0 -xmax 360 -v 0 0 0 0 0
    files=$(for e in {1..7}; do f="$ofile-spinangle-ESA${e}.png"; [[ -f $f ]] && printf '%s ' "$f"; done); [[ -n $files ]] && montage $files -tile 3x3 -geometry +0+0 "$odir/p20.png"

 #   montage "$ofile-spinangle-ESA[1-7].png" -tile 3x3 -geometry +0+0  "$odir"/"p17.png"
    
#    montage "$ofile-checksum_0_15-HiRes-TOF2.png" "$ofile-checksum_15_35-HiRes-TOF2.png" "$ofile-checksum_35_150-HiRes-TOF2.png" -tile 2x2 -geometry +0+0  "$odir"/"p21.png"
    
#    $python $holecheck -f $file -o "$ofile-11110-10010" -t 0 -vTrp 1 1 1 1 0 -vDbl 1 0 0 1 0 -xmax 60 -b 100 -ymin 0.8 -opt 1
    
#    $python $holecheck -f $file -o "$ofile-11111-10010" -t 0 -vTrp 1 1 1 1 1 -vDbl 1 0 0 1 0 -xmax 60 -b 100 -ymin 0.8 -opt 1
    
#    $python $holecheck -f $file -o "$ofile-11110-10010-lng" -t 0 -vTrp 1 1 1 1 0 -vDbl 1 0 0 1 0 -xmax 350 -b 100 -ymin 0.8 -opt 1
    
#    $python $holecheck -f $file -o "$ofile-11111-10010-lng" -t 0 -vTrp 1 1 1 1 1 -vDbl 1 0 0 1 0 -xmax 350 -b 100 -ymin 0.8 -opt 1
    
#    montage "$ofile-11110-10010TOF0.png" "$ofile-11111-10010TOF0.png" "$ofile-11110-10010-lngTOF0.png" "$ofile-11111-10010-lngTOF0.png" -tile 2x2 -geometry +0+0  "$odir"/"p22.png"

#    $python $holecheck -f $file -o "$ofile-11110-01010" -t 1 -vTrp 1 1 1 1 0 -vDbl 0 1 0 1 0 -xmax 40 -b 100 -ymin 0.8 -opt 1
    
#    $python $holecheck -f $file -o "$ofile-11111-01010" -t 1 -vTrp 1 1 1 1 1 -vDbl 0 1 0 1 0 -xmax 40 -b 100 -ymin 0.8 -opt 1
    
#    $python $holecheck -f $file -o "$ofile-11110-01010-lng" -t 1 -vTrp 1 1 1 1 0 -vDbl 0 1 0 1 0 -xmax 300 -b 100 -ymin 0.8 -opt 1
    
#    $python $holecheck -f $file -o "$ofile-11111-01010-lng" -t 1 -vTrp 1 1 1 1 1 -vDbl 0 1 0 1 0 -xmax 300 -b 100 -ymin 0.8 -opt 1
    
#    montage "$ofile-11110-01010TOF1.png" "$ofile-11111-01010TOF1.png" "$ofile-11110-01010-lngTOF1.png" "$ofile-11111-01010-lngTOF1.png" -tile 2x2 -geometry +0+0  "$odir"/"p23.png"
    
    
#    $python $holecheck -f $file -o "$ofile-11110-00110" -t 2 -vTrp 1 1 1 1 0 -vDbl 0 0 1 1 0 -xmax 40 -b 100 -ymin 0.8 -opt 1
    
#    $python $holecheck -f $file -o "$ofile-11111-00110" -t 2 -vTrp 1 1 1 1 1 -vDbl 0 0 1 1 0 -xmax 40 -b 100 -ymin 0.8 -opt 1
    
#    $python $holecheck -f $file -o "$ofile-11110-00110-lng" -t 2 -vTrp 1 1 1 1 0 -vDbl 0 0 1 1 0 -xmax 300 -b 100 -ymin 0.8 -opt 1
    
#    $python $holecheck -f $file -o "$ofile-11111-00110-lng" -t 2 -vTrp 1 1 1 1 1 -vDbl 0 0 1 1 0 -xmax 300 -b 100 -ymin 0.8 -opt 1
    
#    montage "$ofile-11110-00110TOF2.png" "$ofile-11111-00110TOF2.png" "$ofile-11110-00110-lngTOF2.png" "$ofile-11111-00110-lngTOF2.png" -tile 2x2 -geometry +0+0  "$odir"/"p24.png"

    shopt -s nullglob  # ensures empty globs expand to nothing instead of the literal pattern
    files=( "$odir"/p??.png )

    if (( ${#files[@]} > 0 )); then
        magick "${files[@]}" "$odir"/tof_report.pdf
    else
        echo "IDEAS: No pages found, skipping PDF generation."
    fi


fi
