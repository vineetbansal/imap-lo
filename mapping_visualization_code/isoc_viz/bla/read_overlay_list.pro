;
; $Id$
;
; Procedures to read files of overlay information
;
; pro read_overlay_list
; pro dump_overlay_list
;
; A general procedure to read a list of things for overlay onto a plot
; The file is expected to begin with some arbitrary number of comments:
;
;   #
;   # comment lines begin with #
;   # followed by a table of 3 or 4 things:
;   label  ra  dec [color index]
;   label  ra  dec [color index]
;   # lines with less than 3 or more than 4 things are ignored
;   ...
;
; if defclr is set, it is used when the 4th column is missing
; if ignore is set, the defclr is used regardless of the 4th column
; if the same label is repeated, the series is assumed to be a line
; that terminates with either a different label/color, the end of
; the file, or a # - comment.  (I.e. concatenation of these files is
; allowed.
;
; none of the data is interpreted, so some subsequent routine may be
; needed to clean it up for use....
;
; use "nolabel" for an unlabelled item
; use underscores (_) in place of spaces in labels
;
; If the file isn't readable, the arrays will not have been defined.
;
pro read_overlay_list,          $
    file,			$ ; IN: file to be read
    label,			$ ; OUT: array of labels
    ra,				$ ; OUT: array of ra values
    dec,			$ ; OUT: array of dec values
    color,			$ ; OUT; array of color indices
    defclr=defclr,              $ ; IN: default or specified color
    ignore=ignore		  ; IN: ignore input color column

    if (not keyword_set(defclr)) then defclr=0
    if (not keyword_set(ignore)) then ignore=0

    openr, unit, file, /get_lun, error=doh
    if (doh ne 0) then return

    ; read it once to get dimentions
    n = 0;
    line=strarr(1)
    label = [' ']
    repeat begin
	readf, unit, line
	parts = strsplit(line, ' ', /extract)
	nparts = n_elements(parts)
	if (nparts lt 3 or nparts gt 4) then continue
	if (stregex(parts[0],'#.*',/boolean)) then continue
	; I suppose there's some clever way to assign stuff here
	n++;
    endrep until eof(unit)
    close, unit

    ; dimension the return arrays
    label = strarr(n)
    ra    = fltarr(n)
    dec   = fltarr(n)
    color = intarr(n)
    n = 0

    ; now read it all again
    openr, unit, file, error=doh
    if (doh ne 0) then return
    repeat begin
	readf, unit, line
	parts = strsplit(line, ' ', /extract)
	nparts = n_elements(parts)
	if (nparts lt 3 or nparts gt 4) then continue
	if (stregex(parts[0],'#.*',/boolean)) then continue

	; make the assignments
	label[n]   = parts[0]
	ra[n]      = float(parts[1])
	dec[n]     = float(parts[2])
	if (nparts eq 4 and ignore eq 0) then begin
	  color[n] = fix(parts[3])
	endif else begin
	  color[n] = defclr
	endelse
	if (label[n] eq 'nolabel') then label[n] = ''

	n++;
    endrep until eof(unit)

    close, unit
    free_lun, unit
end

;
; This is for debugging, mostly
;
pro dump_overlay_list,          $
    file,			$ ; OUT: file to write
    label,			$ ; IN: array of labels
    ra,				$ ; IN: array of ra values
    dec,			$ ; IN: array of dec values
    color 			  ; IN; array of color indices

    n = n_elements(label)
    if (n lt 1) then return

    openw, unit, file, /get_lun, error=doh
    printf, unit, '#'
    printf, unit, '# file written by dump_overlay_list'
    printf, unit, '#'

    ; as a nicety, the columns could be lined up.
    for i=0,n-1 do begin
	printf, unit, label[i] + $
	    string(ra[i]) + string(dec[i]) + string(color[i])
    endfor

    printf, unit, '#'
    printf, unit, '# eof'
    printf, unit, '#'

    close, unit
    free_lun, unit
end

;
; eof
;
