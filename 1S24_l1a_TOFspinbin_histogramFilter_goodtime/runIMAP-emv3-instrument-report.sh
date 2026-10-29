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

    spinangle="$pydir"/"showIMAPLo-DE-1D-spinbin.py"
    
    $python $spinangle -f $file -o "$ofile-spinangle-" -b $bin -xmin 0 -xmax 360 -v 0 0 0 0 0 -noplot 1
   # files=$(for e in {1..7}; do f="$ofile-spinangle-ESA${e}.csv"; [[ -f $f ]] && printf '%s ' "$f"; done); [[ -n $files ]] && paste -d, $files > NEP_allESA.csv 
    for e in {1..7}; do
        f="$ofile-spinangle-ESA${e}.csv"
        [[ -f $f ]] && files+=("$f")
    done

    if (( ${#files[@]} > 0 )); then

        tmpfiles=()

        for f in "${files[@]:1}"; do
            tmp=$(mktemp)
            cut -d, -f3 "$f" > "$tmp"
            tmpfiles+=("$tmp")
        done

        paste -d, "${files[0]}" "${tmpfiles[@]}" \
            > "${ofile}_spinangle.csv"

        rm -f "${tmpfiles[@]}"
    fi

fi
