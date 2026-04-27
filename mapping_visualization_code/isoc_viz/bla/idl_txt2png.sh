#!/bin/sh
#
Id="idl_txt2png.sh" Xx=""
VERSION="$Id$Xx"
#
# Simple script to make a .png from a me_bin .txt
# with no frills.
#
ME=`basename $0`
USAGE="Usage: $ME file.txt [idl.sh]

which generates file.png assuming me_bin produced it.
If you name a second file, a script is created with the
actual IDL code executed together with processing comments.
"

file=${1-'--help'}
idls=${2-'idl_quiet.sh.errs'}
ping=${file/.txt/.png}

[ "$file" = "--help" ] && { echo "$USAGE"; exit 0; }
[ "$file" = "--version" ] && { echo "$VERSION"; exit 0; }
[ -s $file ] || { echo "$USAGE" ; exit 1; }

. idl_devel.sh
ppos='[.1,.15,.775,.9]'
cpos='[.825,.15,.850,.9]'
[ -z "$device" ] && device='z'
[ -z "$zrange" ] && zrange='[-999.9,-999.9]'
[ -z "$scaling" ] && scaling='linear'
[ -z "$ctable" ] && ctable=0
[ -z "$cbtitle" ] && cbtitle=$file

cmd=" \
    restore,'$restore'& $resolve &\
    ips={ isoc_plot } &\
    ips.ct=$ctable &\
    setup_"$device"_device,ips &\
    ips.cbartool='ver2' &\
    ips.scaling='$scaling' &\
    ips.zrange=$zrange &\
    ips.zexpand=1 &\
    make_me_bin_plot,ips,'"$file"',position=$ppos &\
    make_colorbar_xy,ips,ytitle='"$cbtitle"',position=$cpos &\
    make_png_from_xz,'$ping' "

idl_quiet.sh "$cmd" timeout=0
status=$?
rm -f "$idls"
[ -f "idl_quiet.sh.errs" ] && mv "idl_quiet.sh.errs" $idls

exit $status

#
# eof
#
