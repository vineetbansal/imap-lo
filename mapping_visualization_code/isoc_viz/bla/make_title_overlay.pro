;
; $Id: make_title_overlay.pro 3185 2008-10-09 19:29:12Z gbc $
;
; pro make_title_overlay_empty
; pro make_title_overlay_normal
; pro make_title_overlay_device
;
; A general procedure to drop titles onto a plot.
; The number of labels dominates; x and y are relative to the unit
; plot area defined by position.  No position means entire plot area.
;
pro make_title_overlay_empty,    $
	ips,                     $ ; IN: common isoc plotting structure
	label,                   $ ; IN: array of labels
	xarr,                    $ ; IN: array of x values
	yarr,                    $ ; IN: array of y values
	sized=sized,             $ ; IN: array of size deltas
	color=color,             $ ; IN; array of color indices 0..4
	position=position,       $ ; IN: location, cf. plot position
	align=align                ; IN: alignment of labels

	if (not keyword_set(position)) then begin
	    position=[0,0,1,1]
	endif

	;
	; make an empty plot to set up the plot
	;
	plot,[0,1],[0,1],/nodata,/noerase,xstyle=5,ystyle=5,position=position

	n = n_elements(label)
	if (not keyword_set(align)) then align=replicate(0.0,n)
	if (not keyword_set(color)) then color=replicate(0,n)
	if (not keyword_set(sized)) then sized=replicate(0,n)

	for i=0,n-1 do begin
	    ; smaller/larger text size
	    font_sizing_delta,ips,sized[i]
	    x = xarr[i]
	    y = yarr[i]
	    if (color[i] lt 5) then clr=ips.fg[color[i]] else clr=(color[i]-5)
	    xyouts, x, y, label[i], color=clr, align=align[i]
	    ; restore text size
	    font_sizing_delta,ips,0
	endfor
end

;
; A variant that uses normal coordiates--which doesn't screw up coord space.
;
pro make_title_overlay_normal,   $
	ips,                     $ ; IN: common isoc plotting structure
	label,                   $ ; IN: array of labels
	xarr,                    $ ; IN: array of x values
	yarr,                    $ ; IN: array of y values
	sized=sized,             $ ; IN: array of size deltas
	color=color,             $ ; IN; array of color indices 0..4
	align=align                ; IN: alignment of labels
    
	n = n_elements(label)
	if (not keyword_set(align)) then align=replicate(0.0,n)
	if (not keyword_set(color)) then color=replicate(0,n)
	if (not keyword_set(sized)) then sized=replicate(0,n)
	for i=0,n-1 do begin
	    ; smaller/larger text size
	    font_sizing_delta,ips,sized[i]
	    x = xarr[i]
	    y = yarr[i]
	    if (color[i] lt 5) then clr=ips.fg[color[i]] else clr=(color[i]-5)
	    xyouts, x, y, label[i], color=clr, align=align[i], /normal
	    ; restore text size
	    font_sizing_delta,ips,0
	endfor
end

;
; A variant that uses device coordiates
;
pro make_title_overlay_device,   $
	ips,                     $ ; IN: common isoc plotting structure
	label,                   $ ; IN: array of labels
	xarr,                    $ ; IN: array of x values
	yarr,                    $ ; IN: array of y values
	sized=sized,             $ ; IN: array of size deltas
	color=color,             $ ; IN; array of color indices 0..4
	align=align                ; IN: alignment of labels
    
	n = n_elements(label)
	if (not keyword_set(align)) then align=replicate(0.0,n)
	if (not keyword_set(color)) then color=replicate(0,n)
	if (not keyword_set(sized)) then sized=replicate(0,n)
	for i=0,n-1 do begin
	    ; smaller/larger text size
	    font_sizing_delta,ips,sized[i]
	    x = xarr[i]
	    y = yarr[i]
	    if (color[i] lt 5) then clr=ips.fg[color[i]] else clr=(color[i]-5)
	    xyouts, x, y, label[i], color=clr, align=align[i], /device
	    ; restore text size
	    font_sizing_delta,ips,0
	endfor
end

;
; eof
;
