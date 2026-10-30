;
; $Id: make_me_bin_plot.pro 5158 2009-07-31 21:36:32Z gbc $
;
; pro make_me_bin_plot
;
; This procedure generates a 2-d histogram plot from something
; binned up by me_bin.  It pulls information from the header in
; the file.
;
; Note that C and IDL have different ideas of X and Y, so 0 here refers
; to the dimension of the array that increases with line number, and 1
; refers to the dimension that increases from left to right.
;
pro make_me_bin_plot,            $
	ips,                     $ ; IN: common isoc plotting structure
	datafile,                $ ; IN: name of the data file
	position=position,       $ ; IN: plotting window (!{xy}.window)
	xstyle=xstyle,           $ ; IN: style override
	ystyle=ystyle,           $ ; IN: style override
	notitle=notitle            ; IN: whether to use the title
	compile_opt HIDDEN, STRICTARR

	; get the data and scale it
	ds=get_me_bin_header_size(datafile)
	data=read_ascii(datafile,delimiter=' ',header=hdr,data_start=ds)
	df=read_ascii_data_array(datafile,' ',ds,data)
	a=color_scaling(ips,df)

	;
	; get the magic numbers to set up geometry
	;
	parse_me_bin_header,hdr,lim0,n0,t0,lim1,n1,t1,dl,desc
	xxx=(0.5+findgen(n1))*(lim1[1]-lim1[0])/n1 + lim1[0]
	yyy=(0.5+findgen(n0))*(lim0[1]-lim0[0])/n0 + lim0[0]
	if (not keyword_set(notitle)) then notitle=0
	if (notitle eq 1) then desc=''

	;
	; make an empty plot to set up the plot
	; note that because of the overlay, we do not want rounding.
	;
	if (not keyword_set(xstyle)) then xstyle=1
	if (not keyword_set(ystyle)) then ystyle=1
	!x.style=xstyle
	!y.style=ystyle
	contour,a,xxx,yyy,                 $
		/nodata,position=position, $
		xrange=[lim1[0],lim1[1]],  $
		yrange=[lim0[0],lim0[1]]

	case !d.name of
	  'PS':  make_me_bin_plot_overlay_ps,a,ips.ctop,ips.smm
	  'X':   make_me_bin_plot_overlay_xz,a,ips.ctop,ips.smm
	  'Z':   make_me_bin_plot_overlay_xz,a,ips.ctop,ips.smm
	  else:  print,'no support in make_me_bin_plot for ' + !d.name
	endcase

	;
	; redraw the labels so ticks are on top of the image
	;
	contour,a,xxx,yyy,xtitle=t1,ytitle=t0,title=desc, $
		/nodata,/noerase,position=position, $
		xrange=[lim1[0],lim1[1]],  $
		yrange=[lim0[0],lim0[1]]
	; restore whatever rounding choice was in effect
	!x.style=ips.xstyle
	!y.style=ips.ystyle
end

;
; this makes a display-sized image and overlays it in the x window
;
pro make_me_bin_plot_overlay_xz,image,ctop,smm
	; get window geometry
	px = !x.window * !d.x_vsize
	py = !y.window * !d.y_vsize
	; Desired size of image in pixels.
	sx = px[1] - px[0] + 1
	sy = py[1] - py[0] + 1
	; make a new (size) image
	cimage=congrid(image, sx, sy)
	; which we can just drop into the plot after scaling
	bimage=bytscl(cimage,top=ctop,min=smm[0],max=smm[1]) + 1
	tv, bimage, px[0], py[0]
end

;
; this scales the image and overlays it on the ps plot
;
pro make_me_bin_plot_overlay_ps,image,ctop,smm
	; the image gets stretched to these sizes
	xs=!x.window(1) - !x.window(0)
	ys=!y.window(1) - !y.window(0)
	bimage=bytscl(image,top=ctop,min=smm[0],max=smm[1]) + 1
	tv, bimage, !x.window(0), !y.window(0), xsize=xs, ysize=ys, /norm
end

;
; eof
;
