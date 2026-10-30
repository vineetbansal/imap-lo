;
; $Id: parse_me_bin_header.pro 7139 2010-06-16 01:13:58Z nathanas $
;
; function get_me_bin_header_size
; pro parse_me_bin_header
; pro parse_me_bin_extra
;
function get_me_bin_header_size,  $
	file                        ; IN: data file
	
	compile_opt HIDDEN, STRICTARR

	first='========================================================='

	openr,unit,file,/get_lun
	readu,unit,first
	close,unit

	len=stregex(first,'[0-9]+',/extract)
	; if we needed them...
	; parts=strsplit(first,':',/extract)
	; dims=strsplit(parts[1],'x',/extract)
	return,len
end

; This procedure parses the header produced by me_bin with the -h option
; The header is multiline, looking something like this:
;
;	# 20:10x25...
;	#  ...
;	#  h_min=2 h_max=416 h_title=Events
;	#  min_0=0 max_0=1 num_0=10 title_0=Phase
;	#  min_1=0 max_1=5 num_1=25 title_1=Spin
;	#  desc=Title
;	#  ...
;
; E.g. 20 is the number of #-lines in the header, followed by a 10x25 array
; The ... refers to other things on the line that IDL doesn't yet know or
; care about but which may eventually be placed within its ken.
;
; Note that C and IDL have different ideas of X and Y, so 0 here refers
; to the dimension of the array that increases with line number, and 1
; refers to the dimension that increases from left to right.
;
; The (input) string array of header lines is flattened so that we don't
; have to worry about which line is which.  You should check that your
; data isn't transposed, however, as that can be especially painful.
;
pro parse_me_bin_header,         $
	file_header,             $ ; IN: header lines
	limit0,number0,title0,   $ ; OUT: range of 0 data, size, title
	limit1,number1,title1,   $ ; OUT: range of 1 data, size, title
	dlimit,dtitle,desc         ; OUT: min and max of data, title, desc

	compile_opt HIDDEN, STRICTARR

	limit0=fltarr(2)
	limit1=fltarr(2)
	dlimit=uintarr(2)

	; file_header is originally multi-line
	all_hdr = strjoin(file_header, ' ')

	; grab the 0 items
	limit0[1] = eval_var_eq_value_pair(all_hdr,'max_0')
	limit0[0] = eval_var_eq_value_pair(all_hdr,'min_0')
	number0   = eval_var_eq_value_pair(all_hdr,'num_0')
	title0    = eval_var_eq_value_pair(all_hdr,'title_0')

	; grab the 1 items
	limit1[1] = eval_var_eq_value_pair(all_hdr,'max_1')
	limit1[0] = eval_var_eq_value_pair(all_hdr,'min_1')
	number1   = eval_var_eq_value_pair(all_hdr,'num_1')
	title1    = eval_var_eq_value_pair(all_hdr,'title_1')

	; grab the data items
	dlimit[1] = eval_var_eq_value_pair(all_hdr,'h_max')
	dlimit[0] = eval_var_eq_value_pair(all_hdr,'h_min')
	dtitle    = eval_var_eq_value_pair(all_hdr,'h_title')

	; grab the description
	desc      = eval_var_eq_value_pair(all_hdr,'desc')
end

;
; pull other things and park them in the ips structure
; note that none of these are used right away, so they
; can be overridden after the make_me_bin... call is done.
;
pro parse_me_bin_extra,          $
	ips,                     $ ; IN: common isoc plotting structure
	file_header                ; IN: header lines

	all_hdr = strjoin(file_header, ' ')
	old_mapframe = ips.mapframe
	ips.mapframe = eval_var_eq_value_pair(all_hdr,'skyframe')
	if (ips.mapframe eq '') then ips.mapframe=old_mapframe
	ips.mapdesc  = eval_var_eq_value_pair(all_hdr,'desc')
        ips.bartitle = eval_var_eq_value_pair(all_hdr,'h_title')
	; ...
end

;
; eof
;
