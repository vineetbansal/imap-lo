#!/bin/sh
#

Id="nn_ra.sh" Xx=""
VERSION="$Id$Xx"

# plot a map with one or more line overlays
ME=`basename $0`
USAGE="Usage: $ME fluxmap.txt expmap.txt output_tag fill 
                  p0lon p0lat min max title overline1.txt 
                  overline2.txt ...

which generates a nice plot, output_tag.png,
that has the  fluxmap overplotted with one or 
more lines. and text file output_tag.fxnn.txt
that has the filled map. 
This script uses a Molleweide projection
in Ecliptic J2000 coordinates

fluxmap.txt   -- the fluxmap
expmap.txt    -- the exposure map
output_tag    -- tag for all created output
fill          -- flux value of any holes in the map. 
min           -- the minimum value for colorbar
max           -- the maximum value for colorbar
title         -- title for colorbar
overline1.txt -- txt file with coordinates of line (two col list 
                 of lon,lat pairs in deg
.. place as many different overline files as desired. 

OPTIONS (set as global parameters)

p0lon         -- the center long (deg); default 255.4
p0lat         -- the center lat  (deg); default 5.1
mapframe      -- frame to be used; default ECLIPJ2000
mapname       -- projection scheme; default Mollweide
"

infile=${1-"Input.txt"}  ; shift
expmap=${1-"Expmap.txt"} ; shift
outtag=${1-"Output_tag"} ; shift
fill=${1-0}              ; shift
rmin=${1-"0"}            ; shift 
rmax=${1-0}              ; shift
title=${1-"diff Flux"}   ; shift

[ "$infile" = "--help" ] && { echo "$USAGE"; exit 0; }
[ "$infile" = "--version" ] && { echo "$VERSION"; exit 0; }
[ -s $infile ] || { echo "$USAGE" ; exit 1; }

idlt=${outtag}.sh.tmp

[ -f $infile ] || { echo Need an input file, da; exit; }

[ "$mapname" ] || { mapname="Mollweide"; }

[ "$mapframe" ] || { mapframe="ECLIPJ2000"; }

[ "$p0lon" ] || {  p0lon="255.399429"; }

[ "$p0lat" ] || {  p0lat="5.098670"; }

n=0
while [ $# -gt 0 ] ; do 
    overlay[n]=$1; shift
    n=`expr $n + 1`
done
 
# i=0
# while [ $i -lt $n ] ; do
#    echo ${overlay[$i]}
#    i=`expr $i + 1`  
# done 


nn_ra.sh $infile $expmap $outtag $fill 10.0

infile=$outtag.fxnn.txt

opt1="   ips.zrange=[ $rmin , $rmax ]"
if [ $rmax -eq 0 ]
then
    opt1=" "
fi

cat > fuckme.txt <<EOF
    restore,'$IBEX_ROOT/$IBEX_ARCH/share/isoc/idl/all_isoc_modules.sav'
  
    ips={ isoc_plot } 
    ips.ct=0 
    setup_zvar_device,ips 
    ips.cbartool='ver2' 
    ips.scaling='linear'
    $opt1
    ips.zexpand=1 
    ips.mapname='$mapname'
    ips.mapframe='$mapframe'
    ips.fs=40
    ips.mapgridllt=5
    ips.mapgridlls=0
    make_me_bin_map,ips,'$infile',position=[.05,.2,.95,.95],p0lon=$p0lon , p0lat=$p0lat
    make_me_bin_std_hs,ips,labels,ras,decs,colors
    make_me_bin_overlay,ips,labels,ras,decs,colors
    ips.mapgridlls=0
    ips.mapgridllt=8
    altframe_gline,ips,-10,10,0,0,'galactic',gra,gdec
    make_me_bin_overline, ips, '', gra,gdec,240 
    ips.mapgridllt=14
EOF

i=0
while [ $i -lt $n ] ; do
    echo ${overlay[$i]}
    cat >> fuckme.txt <<EOF 
    read_overlay_line,'${overlay[$i]}.txt',ra,dec
    make_me_bin_overline, ips,'', ra, dec, 10
EOF
    i=`expr $i + 1`  
done 

cat >> fuckme.txt <<EOF
    make_colorbar_xy,ips,xtitle='$title',position=[.1,.07,.9,.12] 
    make_png_from_xz,'$outtag.png'
    exit
EOF

cat fuckme.txt | idl
rm fuckme.txt
rm $outtag.mask.txt

exit
exit status 0
