#!/bin/sh
#
Id="idl_devel.sh" Xx=""
VERSION="$Id: idl_saver.sh 3488 2008-11-06 21:20:51Z gbc $Xx"
#
# Script to help generate a .sav
#
# This used to be in the makefile, but this is more convenient.
#
ME=`basename $0`
#
# set defaults for internal variables
#
[ "$1" = "--help" ] && {
    echo "Usage: $ME target srcdir savename [srcname]"
    exit 0
}
[ "$1" = "--version" ] && {
    echo "$VERSION"
    exit 0
}

target=$1
srcdir=$2
savename=$3
srcname=$4

#
# the hidden stuff was necessary with some verson of the procedures
# to force IDL to resolve things properly, it's not clear if it is
# required any more....
#
case $target in
isoc)
    echo "@$srcdir/resolve_isoc_modules"
    echo "__hidden_ips = { isoc_plot }"
    echo "__hidden_data = [0,1]"
    echo "__hidden_junk = color_scaling(__hidden_ips,__hidden_data)"
    echo "save,/routines,filename='$savename'"
    echo exit
    ;;
core)
    echo "@$srcdir/resolve_core_modules"
    echo "save,/routines,filename='$savename'"
    echo exit
    ;;
hi)
    echo "@$srcdir/resolve_hi_modules"
    echo "save,/routines,filename='$savename'"
    echo exit
    ;;
lo)
    echo "@$srcdir/resolve_lo_modules"
    echo "save,/routines,filename='$savename'"
    echo exit
    ;;
sci)
    echo "@$srcdir/resolve_sci_modules"
    echo "save,/routines,filename='$savename'"
    echo exit
    ;;
test)
    echo "@$srcdir/resolve_test_modules"
    echo "save,/routines,filename='$savename'"
    echo exit
    ;;
*)
    echo "@$srcdir/$srcname"
    echo "save,/routines,filename='$savename'"
    echo exit
    ;;
esac



#
# eof
#
