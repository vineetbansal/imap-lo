;
; $Id: resolve_core_modules.pro 7546 2010-10-29 20:41:44Z DeMajistre $
;
; pro resolve_core_modules
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
.comp read_fcov

;
; above this line should be a duplicate of resolve_core_modules
; below this line should be additional routines in use
;

;
; above this line should be a duplicate of resolve_test_modules
; below this line should be additional routines under test
;

;
; eof
;
