;
; $Id: read_overlay_line.pro 6652 2010-03-25 12:35:11Z gbc $
;
; Procedures to read files of overlay information (a line to plot,
; like the ribbon)
;
; pro read_overlay_line
; pro dump_overlay_line
;
; The file is expected to begin with some arbitrary number of comments:
;
;   #
;   # comment lines begin with #
;   # followed by a table of 2 things:
;    ra  dec 
;    ra  dec 
;   # lines with less than 2 or more than 2 things are ignored
;   ...
;
; If the file isn't readable, the arrays will not have been defined.
;
pro read_overlay_line,          $
    file,			$ ; IN: file to be read
    ra,				$ ; OUT: array of ra values
    dec  			  ; OUT: array of dec values

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
;	if (nparts lt 2 or nparts gt 2) then continue
	if (nparts lt 2 ) then continue
	if (stregex(parts[0],'#.*',/boolean)) then continue
	; I suppose there's some clever way to assign stuff here
	n++;
    endrep until eof(unit)
    close, unit

    ; dimension the return arrays
    ra    = fltarr(n)
    dec   = fltarr(n)
    n = 0

    ; now read it all again
    openr, unit, file, error=doh
    if (doh ne 0) then return
    repeat begin
        readf, unit, line
	parts = strsplit(line, ' ', /extract)
        nparts = n_elements(parts)
;        if (nparts lt 2 or nparts gt 2) then continue
        if (nparts lt 2 ) then continue
	if (stregex(parts[0],'#.*',/boolean)) then continue

	; make the assignments
	ra[n]      = float(parts[0])
	dec[n]     = float(parts[1])

	n++;
    endrep until eof(unit)

    close, unit
    free_lun, unit
end

;
; This is for debugging, mostly
;
pro dump_overlay_line,          $
    file,			$ ; OUT: file to write
    ra,				$ ; IN: array of ra values
    dec			          ; IN: array of dec values

    n = n_elements(ra)
    if (n lt 1) then return
    label = replicate(' ',n)

    openw, unit, file, /get_lun, error=doh
    if (doh ne 0) then return

    printf, unit, '#'
    printf, unit, '# file written by dump_overlay_list'
    printf, unit, '#'

    ; as a nicety, the columns could be lined up.
    for i=0,n-1 do begin
	printf, unit, label[i] + $
	    string(ra[i]) + string(dec[i]) 
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
