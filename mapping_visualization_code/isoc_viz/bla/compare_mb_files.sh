#!/bin/sh
Id=compare_mb_files.sh Xx=
VERSION="$Id: compare_mb_files.sh 9656 2012-11-16 16:42:20Z DeMajistre $Xx"

ME=`basename $0 | cut -d. -f1`
MU=`basename $0`

#
# Compares two me_bin style files - this version uses
# the IDL routine "compare_me_bin_maps" - does not compare
# headers, and does not give false positives when there are
# differences smaller than the specified precision
#

thresh=1.e-5
verb=0
timeout=8

USAGE="Usage:  $MU file1 file2 options

Compares two me_bin style files - this version uses
the IDL routine compare_me_bin_maps - does not compare
headers, and does not give false positives when there are
differences smaller than the specified precision.

The metric for comparison is (taken from compare_me_bin_maps)
    abs((map1-map2)/((abs(map1)+ abs(map2))*.5))
    if (abs(map1)+abs(map2)) ==0, then we call this a match.

file1 and file2 should be me_bin style map files
(theoretically, text file with a bunch of numbers with
comment lines sigified by # should work)

options
	thresh=$thresh		comparison threshold
	verb=$verb			verbosity level
	timeout=$timeout	IDL timeout in seconds
	
"
# standard option handling
[ $# -lt 1 -o "$1" = "--help" ] && { echo "$USAGE" ; exit 0 ; }
[ "$1" = "--version" ] && { echo "$VERSION" ; exit 0 ; }
args="$@"
f1=$1 ; shift 1
f2=$1 ; shift 1
#
# Parse command line options...
#
while [ $# -gt 0 ] ; do eval "$1" ; shift ; done

[ $verb -gt 0 ] && {
  echo "--------"
  echo compare_mb_files.sh is comparing
  echo file1=$f1 
  echo file2=$f2
  echo thresh is $thresh
  echo timeout is $timeout s
  echo "--------"
}

[ -f $f1 ] || { echo File $f1 does not exist ; exit 10 ; }
[ -f $f2 ] || { echo File $f2 does not exist ; exit 10 ; }

cmd="\
  restore,'$IBEX_ROOT/$IBEX_ARCH/share/isoc/idl/all_isoc_modules.sav' &\
  stat=compare_me_bin_maps('$f1','$f2',thresh=$thresh) &\
  print,'IDL status is '+string(stat) & exit,status=stat"
idl_quiet.sh "$cmd" timeout=$timeout kilverb=false
stat=$?

[ $verb -gt 0 ] && {
  echo status is $stat
  echo return from idl is
  cat idl_quiet.sh.errs 
}

[ $stat -eq 0 ] && exit 0
exit 1

#
# eof
#

