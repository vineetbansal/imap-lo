#!/bin/sh
#
Id="nn_ra.sh" Xx=""
VERSION="$Id$Xx"

# perform nearest neighbor filling
# ENTER 
# 1 the flux map
# 2 the exp  map
# 3 Output tag
# 4 fill - flux val for hole fills
# 5 maxangle - maximum angle in deg to use for 
#              nearest neighbor assignment 
#              default = 10 deg
ME=`basename $0`
USAGE="Usage: $ME fluxmap.txt expmap.txt output_tag fill [maxangle]

which generates a new flux map, output_tag.fxnn.txt,
which has nearest neighboring in longitude.
The script also creates associate pngs
and output_tag.mask.txt for the mask that 
was used. Nearest neghboring is performed only where
the exposure= 0.   

fluxmap.txt -- the fluxmap
expmap.txt  -- the exposure map
output_tag  -- tag for all created output
fill        -- flux value of any holes in the map. 
maxangle    -- maximum angle (in deg; default is 10deg) 
               for nearest neghboring. 
"

fluxfile=${1-'--help'}
expfile=${2-'fexp.txt'}
outtag=${3-"Output"}
fill=${4-0}
maxang=${5-10.0}

[ "$fluxfile" = "--help" ] && { echo "$USAGE"; exit 0; }
[ "$fluxfile" = "--version" ] && { echo "$VERSION"; exit 0; }
[ -s $fluxfile ] || { echo "$USAGE" ; exit 1; }

idlt=${outtag}.sh.tmp

[ -f $infile ] || { echo Need an input file, da; exit; }

idl <<EOF
     restore,'$IBEX_ROOT/$IBEX_ARCH/share/isoc/idl/all_isoc_modules.sav'
  
; read in flux, variance and ribbon
    read_me_bin_map,'$fluxfile',flux,lat,lon,n0=n0,n1=n1
    read_me_bin_map,'$expfile',exp,lat1,lon1,n0=n0,n1=n1
    dump_me_bin_map,'$outtag.flux.txt',flux,lat,lon,n0=n0,n1=n1

; mask from exp = 0
    zero=exp*0
    mask=zero
    mask[where(zero eq 0)]=1
    mask[where(exp eq 0)]=0

    phi=1.0d0*lon*!dtor
    theta=1.0d0*(90.0d0-lat)*!dtor
    mangle = 1.0d0*$maxang*!dtor
    nn_ra,flux,mask,phi,theta,mangle,flux_nn,fill=$fill

; dump map files
    dump_me_bin_map,'$outtag.fxnn.txt',flux_nn,lat,lon,n0=nn0,n1=nn1
    dump_me_bin_map,'$outtag.mask.txt',mask,lat,lon,n0=nn0,n1=nn1
EOF

idl_map2png.sh ${outtag}.fxnn.txt $idlt
idl_map2png.sh ${outtag}.mask.txt $idlt

exit
exit status 0
