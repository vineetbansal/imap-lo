#!/bin/sh
#
Id="idl_quiet.sh" Xx=""
VERSION="$Id: idl_quiet.sh 16680 2021-12-11 15:43:00Z ibexops $Xx"
#
# Script to run idl quietly.
#
ME=`basename $0`
#
# set defaults for internal variables
#
[ -z "$1" -o "$1" = "--help" ] && {
	echo ""
	echo "Usage: $ME idl_command [more commands or option=value]"
	echo ""
	echo "Runs idl with all of its chatter dumped to $ME.errs."
	echo ""
	echo "Options include:"
	echo ""
	echo "timeout=N	    set this to zero to disable the timeout on IDL"
	echo "		    execution, or else some number of seconds"
	echo "kilverb=true        set this to false to silence the timeout msg"
	echo ""
	exit 0
}
[ "$1" = "--version" ] && {
	echo "$VERSION"
	exit 0
}

type -p idl 1>/dev/null || {
    #
    # set up idl environment (note IDL_PATH is setup by isoc.sh)
    #
    [ -f $IBEX_ROOT/tools/$IBEX_ARCH/bin/idl_setup.bash ] || {
        echo No idl setup found:
	echo '$IBEX_ROOT/tools/$IBEX_ARCH/bin/idl_setup.bash'
	exit 1
    }
    . $IBEX_ROOT/tools/$IBEX_ARCH/bin/idl_setup.bash
}
type -p idl 1>/dev/null || {
	echo No idl to execute
	exit 2
}

#
# Nearly everything is an IDL command here,
# but allow a few optional equates to drift in...
#
timeout=8
kilverb=true
allcmds="$1" shift
while [ $# -gt 0 ]
do
    case $1 in
    timeout=*)
	eval $1
	;;
    kilverb=*)
	eval $1
	;;
    *)
	allcmds="$allcmds & $1"
	;;
    esac
    shift
done
#
# impose a standard sane timeout, and other checking
#
[ "$timeout" -lt 0 -o "$timeout" -gt 6400 ] && timeout=8
[ "$kilverb" = 'true' -o "$kilverb" = 'false' ] || kilverb=true

#
# for debugging it is useful to know what the command was and for
# convenience, reformat it for easy cut'n'paste to a new idl sesssion.
#
echo "#!/bin/sh"                >$ME.errs
echo "#"                       >>$ME.errs
echo "# ${timeout}s to run:"   >>$ME.errs
echo "#"                       >>$ME.errs
echo "# IDL_PATH=$IDL_PATH \\" >>$ME.errs
echo "# idl -quiet -e \\"      >>$ME.errs
echo "#     \" $allcmds \""    >>$ME.errs
echo ""                        >>$ME.errs
echo "idl <<EOF"               >>$ME.errs
echo "$allcmds" | tr '&' \\012 >>$ME.errs
echo "EOF"                     >>$ME.errs
echo "exit"                    >>$ME.errs
#
# Replace sleep in subshell with timeout utility.
#
# type is difficult to use for an alias because it surrounds the IDL
# path string with mismatched quotes - backtick and single quote
idl_path=$(type -p idl)
[ -z "$idl_path" ] && idl_path=$IDL_DIR/bin/idl
timeout $timeout $idl_path -quiet -e "$allcmds"      2>>$ME.errs 1>&2
status=$?
[ "$status" -eq 124 ] && {
  echo "###";
  echo "### TIMEOUT after $timeout seconds" ;
  echo "###";
  echo "### You probably asked IDL to do something that it";
  echo "### couldn't do in a reasonable amount of time." ;
  echo "###" ;
  echo "";
}
#
echo "exit status $status"     >>$ME.errs

exit $status

#
# eof
#
