;
; $Id: read_ascii_data_array.pro 2214 2008-06-14 02:39:12Z gbc $
;
; function read_ascii_data_array
;
; read_ascii() returns an anonymous structure and you are just supposed
; to guess what the tag names are.  Here we crib the code from read_ascii()
; and switch into the right answer, returning the data array.
;
function read_ascii_data_array,   $
	datafile,                 $ ; IN: input data file
	delimiter,                $ ; IN: the delimiter
	data_start,               $ ; IN: the number of header lines to skip
	data                        ; IN: the data structure

	compile_opt HIDDEN, STRICTARR

	fieldCountUse=ra_guess_columns(datafile,data_start,'',delimiter)
	digits_str=strtrim(string(strlen(strtrim(string(fieldCountUse),2))),2)
	fstr = '(i' + digits_str + '.' + digits_str + ')'
	fieldNamesUse = 'field' + STRING(INDGEN(fieldCountUse)+1, format=fstr)

	; try to return the data array

	if ( fieldNamesUse[0] eq 'field1' ) then begin
		return,data.field1
	endif
	if ( fieldNamesUse[0] eq 'field01' ) then begin
		return,data.field01
	endif
	if ( fieldNamesUse[0] eq 'field001' ) then begin
		return,data.field001
	endif
	if ( fieldNamesUse[0] eq 'field0001' ) then begin
		return,data.field0001
	endif
	if ( fieldNamesUse[0] eq 'field00001' ) then begin
		return,data.field00001
	endif
	if ( fieldNamesUse[0] eq 'field000001' ) then begin
		return,data.field000001
	endif
	if ( fieldNamesUse[0] eq 'field0000001' ) then begin
		return,data.field0000001
	endif

	; if you get here, game over anyway, but pass back something
	
	return,data
end
;
; end of file
;
