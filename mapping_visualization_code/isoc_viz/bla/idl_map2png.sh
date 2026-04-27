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
ppos='[.05,.15,.95,.95]'
cpos='[.05,.10,.95,.125]'
[ -z "$device" ] && device='z'
[ -z "$zrange" ] && zrange='[-999.9,-999.9]'
[ -z "$ctable" ] && ctable=0
[ -z "$scaling" ] && scaling='linear'
[ -z "$maproj" ] && maproj='Mollweide'
[ -z "$p0lon" ] && p0lon=0
[ -z "$p0lat" ] && p0lat=0
[ -z "$plot_title" ] && plot_title=' '
[ -z "$cbtitle" ] && cbtitle=$file
center="p0lon=$p0lon,p0lat=$p0lat"

cmd=" \
    restore,'$restore'& $resolve &\
    ips={ isoc_plot } &\
    ips.ct=$ctable &\
    setup_"$device"_device,ips &\
    ips.cbartool='ver2' &\
    ips.scaling='$scaling' &\
    ips.zrange=$zrange &\
    ips.zexpand=1 &\
    setup_map_name,ips,'$maproj' &\
    make_me_bin_map,ips,'"$file"',position=$ppos,$center &\
    make_colorbar_xy,ips,xtitle='"$cbtitle"',position=$cpos &\
    make_title_overlay_normal,ips,'$plot_title',0.5,0.9,sized=5,align=0.5 &\
    make_png_from_xz,'$ping' "

idl_quiet.sh "$cmd" timeout=0
status=$?
rm -f "$idls"
[ -f "idl_quiet.sh.errs" ] && mv "idl_quiet.sh.errs" $idls

exit $status

#
# eof
#
