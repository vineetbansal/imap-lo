;
; $Id: resolve_test_modules.pro 5675 2009-10-13 22:11:23Z gbc $
;
; pro resolve_test_modules
;
; See readme.txt for the purpose of this file.
; Changes to this file and the Makefile.am must be made in parallel.
;

.comp setup_plot_device
.comp loadaltct
.comp make_jpeg_from_x

.comp color_scaling
.comp colorbar_ticks
.comp make_colorbar
.comp make_colorbar_orig
.comp make_colorbar2
.comp kwproc
.comp font_sizing

.comp make_me_bin_plot
.comp make_me_bin_map
.comp make_me_bin_map_orig
.comp make_me_bin_map_image
.comp make_me_bin_map_patch
.comp make_me_bin_map_contour

.comp make_me_bin_overlay
.comp make_title_overlay
.comp read_overlay_list
.comp read_overlay_line
.comp extra_axes
.comp spin_lookup

.comp read_ascii_data_array

.comp parse_me_bin_header
.comp eval_var_eq_value_pair
.comp parse_variable_header

.comp congrid
.comp read_ascii

.comp symbols
.comp legend
.comp plot_variable
.comp plot_histogram

;
; above this line should be a duplicate of resolve_core_modules
; below this line should be additional routines in use
;

.comp setup_trend_plot_devices

.comp kappa_dist
.comp puid_dist
.comp puiu_dist
.comp pui_tail
.comp charge_exchange_H
.comp write_ena_dist

.comp bin_angle_list
.comp orbit
.comp new_label_date

;
; above this line should be a duplicate of resolve_isoc_modules
; below this line should be additional routines under test
;

.comp orbit_plotter

.comp stringer
.comp bin_hi_refresh
.comp bin_lo_refresh
.comp bin_outer_map

;
; eof
;
