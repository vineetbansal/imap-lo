#
# $Id: Makefile.am 10390 2013-08-26 15:01:22Z DeMajistre $
#
SUBDIRS = . test

EXTRA_DIST = readme.txt

if HAVE_IDL
SAVE_ALL    = all_isoc_modules.sav \
	      test_isoc_modules.sav \
	      core_isoc_modules.sav
else
SAVE_ALL    =
endif

#
# this could be $(pkgdatadir) but that's probably overkill
#
idldir           = $(pkgdatadir)/idl

#
# Core modules (resolve_core_modules.pro)
#
IDL_CORE_PROS    = \
		   setup_plot_device.pro \
		   loadaltct.pro \
		   make_jpeg_from_x.pro \
		   color_scaling.pro \
		   colorbar_ticks.pro \
		   make_colorbar.pro \
		   make_colorbar_orig.pro \
		   make_colorbar2.pro \
		   kwproc.pro \
		   font_sizing.pro \
		   make_me_bin_plot.pro \
		   make_me_bin_map.pro \
		   make_me_bin_map_orig.pro \
		   make_me_bin_map_image.pro  \
		   make_me_bin_map_patch.pro \
		   make_me_bin_map_contour.pro \
		   make_me_bin_overlay.pro \
		   make_title_overlay.pro \
		   read_overlay_list.pro \
		   read_overlay_line.pro \
		   extra_axes.pro \
		   spin_lookup.pro \
		   read_ascii_data_array.pro \
		   parse_me_bin_header.pro \
		   parse_variable_header.pro \
		   eval_var_eq_value_pair.pro \
		   symbols.pro \
		   legend.pro \
		   plot_variable.pro \
		   plot_histogram.pro \
		   read_fcov.pro

#
# Non-Core modules (resolve_isoc_modules.pro)
#
IDL_ISOC_PROS    = \
                   setup_trend_plot_devices.pro \
                   new_label_date.pro \
		   kappa_dist.pro \
		   puid_dist.pro \
		   puiu_dist.pro \
		   pui_tail.pro \
		   charge_exchange_H.pro \
	           write_ena_dist.pro \
		   bin_angle_list.pro \
		   orbit.pro \
		   read_me_bin_map.pro \
		   dump_me_bin_map.pro \
		   compare_me_bin_maps.pro \
		   compare_fc_files.pro \
		   real_spher_harm.pro \
		   sph2cart.pro \
		   linemask.pro \
		   rangemask.pro \
		   mask_smooth.pro \
		   nn_ra.pro \
		   imdisp.pro \
		   error_message.pro \
		   decomposedcolor.pro \
		   pickcolorname.pro \
		   fsc_color.pro \
		   colorbar_dfanning.pro \
	   	   normal_eqn_retrieve.pro \
		   real_sh_laplacian.pro \
		   dlegdtheta.pro \
		   sweepmapper.pro


#
# Test modules (resolve_test_modules.pro)
#
IDL_TEST_PROS   = \
		   orbit_plotter.pro \
		   stringer.pro \
		   bin_hi_refresh.pro \
		   bin_lo_refresh.pro \
		   bin_outer_map.pro

#
# Anything else -- dangling threads, development modules, ...
#
IDL_OTHER_PROS   = \
		   newplot.pro \
		   histogram2.pro \
		   genPlot.pro \
		   cbar_work.pro

IDL_PROS = $(IDL_CORE_PROS) $(IDL_ISOC_PROS) $(IDL_TEST_PROS) $(IDL_OTHER_PROS)

dist_idl_DATA    = resolve_isoc_modules.pro \
		   resolve_test_modules.pro \
		   resolve_core_modules.pro \
		   $(IDL_PROS)
dist_bin_SCRIPTS = idl_quiet.sh idl_devel.sh idl_saver.sh \
		   idl_txt2png.sh idl_map2png.sh nn_ra.sh \
		   map_overlay.sh idl_map2zpng.sh compare_mb_files.sh

#
# this is handled as a hook so that it is created and installed after
# all the *.pro files (otherwise we can't create it [correctly])
#
if HAVE_IDL
all:	$(SAVE_ALL)

IDLENV = IDL_PATH=$(srcdir):$$IDL_PATH

all_isoc_modules.sav: $(srcdir)/resolve_isoc_modules.pro $(IDL_PROS)
	$(srcdir)/idl_saver.sh isoc $(srcdir) $@ |\
	$(IDLENV) $(IDL) -quiet 2>all_isoc_resolve.errs

core_isoc_modules.sav: $(srcdir)/resolve_core_modules.pro $(IDL_PROS)
	$(srcdir)/idl_saver.sh core $(srcdir) $@ |\
	$(IDLENV) $(IDL) -quiet 2>core_isoc_resolve.errs

test_isoc_modules.sav: $(srcdir)/resolve_test_modules.pro $(IDL_PROS)
	$(srcdir)/idl_saver.sh test $(srcdir) $@ |\
	$(IDLENV) $(IDL) -quiet 2>test_isoc_resolve.errs

install-data-hook: $(SAVE_ALL)
	for p in $(SAVE_ALL) ; do \
	$(INSTALL_DATA) "$$p" "$(DESTDIR)$(idldir)/$$p" ; done

uninstall-hook:
	for p in $(SAVE_ALL) ; do \
	rm -f $(DESTDIR)$(idldir)/$$p ; done
else
endif

CLEANFILES = $(SAVE_ALL) *.errs

#
# eof
#
