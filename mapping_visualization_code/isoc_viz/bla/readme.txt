#!/bin/sh
#
# $Id: readme.txt 3488 2008-11-06 21:20:51Z gbc $
#
# This file has some general usage notes about the ISOC collection
# of plotting routines.  Parts of it are formatted in shell script
# syntax so you can cut'n'paste, however, blindly doing this will
# not do anything useful.
#
cat - <<-EOF

Organization of idl routines


There are several groupings of IDL .pro files at the moment:

    production routines
	These are critical to the routine processing and you
	should never modify them unless your sure what you're
	doing.  They are collected and saved in

	    resolve_isoc_modules.pro
	    all_isoc_modules.sav

    core subset of production routines
    	This is a subset of the above, collected for general use.

	    resolve_core_modules.pro
	    core_isoc_modules.sav

    test routines
	This includes the production routines and addition things
	that are intended to become production routines after trial.
	(Note that initially, this was the only IDL directory for
	so some of the things here will eventually be moved elsewhere
	and this will probably go away.)
	They are collected and saved in

	    resolve_test_modules.pro
	    test_isoc_modules.sav

    other collections
	In addtion to the routines in this directory, there are (at
	least three) other groupings:

	    resolve_*_modules.pro
	    *_isoc_modules.sav

	which are maintained, built and installed from other directories:

	    pipe/hi/hk
	    pipe/lo/hk
	    pipe/sci/idl

    other things
	This includes the production and test routines (i.e. pretty
	much every .pro in this directory) these are installed into
	the default IDL path, i.e. $IDL_PATH which is
	$IBEX_ROOT/$IBEX_ARCH/share/isoc/idl

Note that a few IDL routines are mentioned in the resolve*pro files
so that they can be compiled into the .sav files for restoring a
known state.

The production plotting system is complicated by the fact that it
must also be reusable in the web-based toolbox.  So, some things
are slightly more complicated than you think is necessary so that
it will work in all environments.

There are two scripts useful in shell scripts:

    idl_quiet.sh
	which arranges for IDL to run quietly
    idl_devel.sh
	which locates the saved procedure files

and a third script

    idl_saver.sh
    	which builds the .sav files (see the Makefile)

Both support --help for further details.

In order to keep the number of arguments to be passed manageable,
there is a plotting structure that is usually the first argument.
Conventionally it's named ips, but you can call it what you like,
and if that's not sufficient, make and expand it into similar structures.


Usage

The IDL code is organized so that it can be used interactively with
X as the display device; but most of the time there is a shell script
that actually feeds the commands to run to IDL via the helper script

	idl_quiet.sh

which shovels all the commentary to a place where it can in principal
be examined when something goes wrong.  Most of the web-based processing
aims to produce one or more .png files for use on the website; it is
envisioned that eps can also be produced for products where that is a
good thing.  (E.g. figures that are likely to turn up in publication.)

For stability, all these scripts start by loading a saved IDL environment
(so that no accidental changes to .pro files in IDL_PATH creep in).

Thus:

	@resolve_isoc_modules
	; forward_function declarations as necessary
	ips={ isoc_plot }
	setup_x_device,ips
	; or
	setup_z_device,ips
	setup_zz_device,ips
	setup_zv_device,ips
	setup_eps_device,ips
	; ...

and then a few plotting commands.  This typically gets fed to IDL
with the & concatenation character to make a single string argument.
The ips is designed to retain the state of what you are doing, so you
should arrange the plot commands so that

	setup_x_device,ips
	; commands
	make_png_from_xz,'pretty-x'
	make_jpeg_from_x,'pretty-x'
	setup_z_device,ips
	make_png_from_xz,'pretty-z'

	setup_eps_device,ips
	device,filename='pretty.eps'
	; commands
	device,/close

give you more-or-less the same thing.  (It's a challenge sometimes,
but that's the plan.)

There are many samples in the $IBEX_ROOT/isoc/src/infra/idl/test
directory, which you can copy.


Web

Part of the insanity here is that the web server supports toolbox
processing which should allow any IBEX scientist to make variations
on some of these plots to the extent that this proves useful.  The
toolbox works by feeding the parameters into a script that arranges
for the script to run.

It is not expected that you need to know about this, but an overview
follows.  In principle, scripts developed according to the plan described
above should just work on the web, and none of the following is necessary.


Gory Web details

For web development, an idl directory in the work directory
(if found) will be added to the IDL_PATH.  If there is then
a file named  resolve_extras.pro  it will be invoked to load
develomental versions of IDL scripts.  The script idl_devel.sh
may be sourced to locate both all_isoc_modules.sav and such a
local resolver.  This makes it possible to tune idl code through
the web interface.  For example

	# cat $IBEX_WORK/$USER/idl/resolve_extras.pro
	pro resolve_extras
		resolve_routine,'make_me_bin_map',/either
		resolve_routine,'make_me_bin_plot',/either
	end

would allow local copies of the two procedures

	make_me_bin_map.pro
	make_me_bin_plot.pro

to override the versions loaded in the .sav file.  Similarly, a
bin script ($IBEX_WORK/$USER/bin) allows the override of things
in the standard paths.

A description of all the scriptage necessary to make all this work
is elsewhere (eventually).

EOF

#
# ok, stop reading now
#

# j.i.c.
exit 1

#
# really.
#

#
# The remainder of this file contains some random scraps of code
# jotted down some time ago.  It should all be deleted....
#



#
# general line plotting
#
idl -quiet <<-EOF
	@resolve_isoc_modules
	ips={ isoc_plot }
	setup_x_device,ips
	parse_variable_file,ips,'var-sample.txt',titles,data
EOF
#	... now you can plot

#
# note-to-self:  
# spawn,['ibex_time','-H','0','-X','+2d'],result,error,/noshell,/null_stdin
# returns an array with the two answers.
#

#
# a rosetta stone for binning things
#

me_bin -h Title -t 889992005.503,1440 -s matrix -m \
  -0 phase,0,1,25 -1 time,0,6,12 -d isw1.osbdba isw1.hide > bar.txt

#
# or just type this in if you are in X
#
idl -quiet <<-EOF
	@resolve_isoc_modules
	ips={ isoc_plot }
	setup_x_device,ips
	make_me_bin_plot,ips,'bar.txt'
	make_jpeg_from_x,'foolish'
	exit
EOF

#
# the ips variable is a structure that contains details of the plotting
# setup which gets passed along to the plotting routines so that some
# important details can be preserved across plots, independent of the
# plotting device.
#

# a batch file:
cat > foo.pro <<-EOF
	;
	; idl batch file
	;
	@resolve_isoc_modules
	ips={ isoc_plot }
	setup_zz_device,ips
	make_me_bin_plot,ips,'bar.txt','sqrt'
	make_png_from_xz,'sample-ss'
	exit
EOF
idl -quiet foo.pro

# using save/restore
idl -quiet <<-EOF
	@resolve_isoc_modules
	save,/routines,filename='all_isoc_modules.sav'
	exit
EOF

#
# allows a oneliner command execution:
#
idl -quiet -e "restore,'all_isoc_modules.sav' & \
	       ips={ isoc_plot } & \
               setup_zz_device,ips & \
	       make_me_bin_plot,'bar.txt','sqrt' & \
	       make_png_from_xz,'sample-sss' " \
       2>/dev/null


#
# genPlot.tar came from Katy with genPlot.pro
# plot_functions.tar came from Kris, but don't grok it yet.
#
# the subdirectory future is for stuff that isn't used, *YET*

# orbit.pro came from Nathan

#
# eof
#
