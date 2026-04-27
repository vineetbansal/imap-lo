;
; $Id: make_colorbar_orig.pro 2128 2008-06-10 16:13:34Z geoff $
;
; pro make_colorbar_xy_orig
;
; These procedures generate colorbars in either x or y.
; One of xtitle or ytitle is required so we know which one.
;
pro make_colorbar_xy_orig,            $
	ips,                     $ ; IN: common isoc plotting structure
	position=position,       $ ; IN: location, cf. plot position
	xtitle=xtitle,           $
	ytitle=ytitle           ;$
       
	compile_opt HIDDEN, STRICTARR

	if (not keyword_set(xtitle) and not keyword_set(ytitle)) then begin
		print, 'One of xtitle or ytitle must be set'
		return
	endif

	;
	; based on the data and color ranges,
	; figure out where best to place the tick marks.
	;
	ticks=get_colorbar_ticks(ips,names,values)

	;
	; make an empty plot to set up the plot
	;
	plot,[0,1],[0,1],/nodata,/noerase,xstyle=5,ystyle=5,position=position
	;
	; make and show the color bar
	;
	a = (1 + findgen(ips.ctop + 1)) # replicate(1.0,2)
	if (keyword_set(ytitle)) then a=transpose(a)
	case !d.name of
	  'PS':  make_me_bin_plot_overlay_ps,a,ips.ctop
	  'X':   make_me_bin_plot_overlay_xz,a,ips.ctop
	  'Z':   make_me_bin_plot_overlay_xz,a,ips.ctop
	  else:  print,'no support in make_colorbar_xy for ' + !d.name
	endcase

	if (keyword_set(xtitle)) then begin
	    axis,0,0,xax=0,xticklen=1.0,xminor=-1,   $
		xtickname=names,xtitle=xtitle,       $
		xticks=ticks,xtickv=values
	    axis,0,1,xax=1,xticklen=1.0,xminor=-1,   $
		xtickname=replicate(' ',9),          $
		xticks=2,xtickv=[0,1]                ; ends
	endif else begin
	    axis,1,0,yax=1,yticklen=1.0,yminor=-1,   $
		ytickname=names,ytitle=ytitle,       $
		yticks=ticks,ytickv=values
	    axis,0,0,yax=0,yticklen=1.0,yminor=-1,   $
		ytickname=replicate(' ',9),          $
		yticks=2,ytickv=[0,1]                ; ends
	endelse

end

;
; eof
;
