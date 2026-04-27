#!/bin/sh
#
Id="idl_devel.sh" Xx=""
VERSION="$Id: idl_devel.sh 8280 2011-06-17 21:01:58Z DeMajistre $Xx"
#
# Script to hook locate saved modules, and maybe allow development overrides.
#
# This script isn't meant to be run standalone, but rather it is meant to
# be sourced or eval'd into other scripts.  However, it gets installed so
# it is easy to find, and if $verb is defined it says what it got.
#
# the basename has some issues when this is called as ". idl_devel.sh"
#ME=`basename $0`
ME=idl_devel.sh
#
# set defaults for internal variables
#
[ "$1" = "--help" ] && {
    xxx="\`"
    echo "Usage: $ME"
    echo sets restore and resolve variables for use with IDL:
    echo ''
    echo ' . $IBEX_ROOT/$IBEX_ARCH/bin/idl_devel.sh'
    echo ' # -- or -- '
    echo " eval ${xxx}verb=true idl_devel.sh$xxx"
    echo ''
    echo will define several variables to contain the full path to
    echo various IDL .sav files or the resolve_extras.pro procedure
    echo 'as they are found (in order) in the IDL_PATH variable.'
    echo ''
    echo 'The following variables/files are assigned/located:'
    echo ''
    echo ' $restore        all_isoc_modules.sav'
    echo ' $restore_core   core_isoc_modules.sav'
    echo ' $restore_hi     hi_isoc_modules.sav'
    echo ' $restore_lo     lo_isoc_modules.sav'
    echo ' $restore_sci    sci_isoc_modules.sav'
    echo ' $restore_apl    apl_modules.sav'
    echo ' $restore_bu     bu_modules.sav'
    echo ' $restore_lanl   lanl_modules.sav'
    echo ' $restore_lmco   lmco_modules.sav'
    echo ' $restore_mit    mit_modules.sav'
    echo ' $restore_swri   swri_modules.sav'
    echo ' $restore_um     um_modules.sav'
    echo ' $restore_unh    unh_modules.sav'
    echo ' $restore_test   test_isoc_modules.sav'
    echo ' $resolve        resolve_extras.pro'
    echo ''
    echo 'The resolve_extras.pro is intended as a developmental hook'
    echo 'to allow you to pretty much do anything if you need to....'
    echo ''
    echo 'Note that the resolve*modules.pro procedures corresponding'
    echo 'to each of these .sav files should already be in your IDL_PATH.'
    exit 0
}
[ "$1" = "--version" ] && {
    echo "$VERSION"
    exit 0
}

#
# make sure they are empty to start
#
restore=""
restore_core=""
restore_hi=""
restore_lo=""
restore_sci=""
restore_apl=""
restore_bu=""
restore_lanl=""
restore_lmco=""
restore_mit=""
restore_swri=""
restore_um=""
restore_unh=""
restore_test=""

resolve=""

#
# add the current directory to the search if srcdir is defined which
# is needed if testing but the .sav files are not yet installed.
#
[ -n "$srcdir" ] && idlpathprefix=".:" || idlpathprefix=""
set -- `echo $idlpathprefix$IDL_PATH | tr : ' '`

#
# walk through the IDL PATH looking for things--first one wins
#
while [ $# -gt 0 ]
do
    [ -z "$restore" ] && {
	try="$1/all_isoc_modules.sav"
	[ -f $try ] && restore=$try
    }
    [ -z "$restore_core" ] && {
	try="$1/core_isoc_modules.sav"
	[ -f $try ] && restore_core=$try
    }
    [ -z "$restore_hi" ] && {
	try="$1/hi_isoc_modules.sav"
	[ -f $try ] && restore_hi=$try
    }
    [ -z "$restore_lo" ] && {
	try="$1/lo_isoc_modules.sav"
	[ -f $try ] && restore_lo=$try
    }
    [ -z "$restore_sci" ] && {
	try="$1/sci_isoc_modules.sav"
	[ -f $try ] && restore_sci=$try
    }
    [ -z "$restore_apl" ] && {
	try="$1/apl_modules.sav"
	[ -f $try ] && restore_apl=$try
    }
    [ -z "$restore_bu" ] && {
	try="$1/bu_modules.sav"
	[ -f $try ] && restore_bu=$try
    }
    [ -z "$restore_lanl" ] && {
	try="$1/lanl_modules.sav"
	[ -f $try ] && restore_lanl=$try
    }
    [ -z "$restore_lmco" ] && {
	try="$1/lmco_modules.sav"
	[ -f $try ] && restore_lmco=$try
    }
    [ -z "$restore_mit" ] && {
	try="$1/mit_modules.sav"
	[ -f $try ] && restore_mit=$try
    }
    [ -z "$restore_swri" ] && {
	try="$1/swri_modules.sav"
	[ -f $try ] && restore_swri=$try
    }
    [ -z "$restore_um" ] && {
	try="$1/um_modules.sav"
	[ -f $try ] && restore_um=$try
    }
    [ -z "$restore_unh" ] && {
	try="$1/unh_modules.sav"
	[ -f $try ] && restore_unh=$try
    }
    [ -z "$restore_test" ] && {
	try="$1/test_isoc_modules.sav"
	[ -f $try ] && restore_test=$try
    }
    [ -z "$resolve" ] && {
	try="$1/resolve_extras.pro"
	[ -f $try ] && resolve=$try
    }
    shift
done

# error checking is the sourcer's responsibility
[ -n "$verb" ] && {
    echo resolve=$resolve
    echo restore=$restore
    echo restore_core=$restore_core
    echo restore_hi=$restore_hi
    echo restore_lo=$restore_lo
    echo restore_sci=$restore_sci
    echo restore_apl=$restore_apl
    echo restore_bu=$restore_bu
    echo restore_lanl=$restore_lanl
    echo restore_lmco=$restore_lmco
    echo restore_mit=$restore_mit
    echo restore_swri=$restore_swri
    echo restore_um=$restore_um
    echo restore_unh=$restore_unh
    echo restore_test=$restore_test
}

#
# eof
#
