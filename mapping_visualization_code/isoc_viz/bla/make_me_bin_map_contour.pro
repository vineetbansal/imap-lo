;
; $Id: make_me_bin_map_contour.pro 5674 2009-10-13 21:55:51Z gbc $
;
; pro make_me_bin_map_contour
;
; This code is derivative of map_patch/map_image see those for general
; comments.  We don't need to mess with the tv calls here, and there
; are many more options to be added....
;
; rotating the map doesn't work with inside/outside so it is disabled.
;
pro make_me_bin_map_contour,     $
	ips,                     $ ; IN: common isoc plotting structure
	datafile,                $ ; IN: name of the data file
	position=position,       $ ; IN: plotting window (!{xy}.window)
	p0lon=lon0,              $ ; IN: longitude at center of plot
	p0lat=lat0,              $ ; IN: latitude at center of plot
	rota=rot0,               $ ; IN: rotation of the plot
	nlevels=nlvl,            $ ; IN: number of (equal spaced) contours
	c_colors=c_colors,       $ ; IN: array of colors
	c_labels=c_labels,       $ ; IN: array of to label or not
	c_linestyle=c_linestyle, $ ; IN: array of to how to do it
	c_thick=c_thick,         $ ; IN: array of to how to do it
	noerase=noer		   ; IN: if set, presumes map_set called.

	compile_opt HIDDEN, STRICTARR


	if (not keyword_set(lon0)) then lon0=0.0
	if (not keyword_set(lat0)) then lat0=0.0
	if (not keyword_set(rot0)) then rot0=0.0 else rot0=0.0
	if (not keyword_set(nlvl)) then nlvl=5
	if (not keyword_set(noer)) then noer=0

	; these seem to work; c_charsize and c_charthick didn't
	if (n_elements(c_colors) eq 0) then c_colors=replicate(ips.fg[2],nlvl)
	if (n_elements(c_labels) eq 0) then c_labels=replicate(1,nlvl)
	if (n_elements(c_linestyle) eq 0) then c_linestyle=replicate(0,nlvl)
	if (n_elements(c_thick) eq 0) then c_thick=replicate(3,nlvl)

	; get the data and scale it
	ds=get_me_bin_header_size(datafile)
	data=read_ascii(datafile,delimiter=' ',header=hdr,data_start=ds)
	df=read_ascii_data_array(datafile,' ',ds,data)
	; which allows us to get the levels right
	a=color_scaling(ips,df)
	al=(0.5+findgen(nlvl))*(ips.smm[1]-ips.smm[0])/nlvl
	dlevels=color_invert(ips,al)

	;
	; get the magic numbers to set up geometry
	; and establish the spherical mapping
	;
	parse_me_bin_header,hdr,lim0,n0,t0,lim1,n1,t1,dl,desc
	parse_me_bin_extra,ips,hdr

	xxx=(0.5+findgen(n1))*(lim1[1]-lim1[0])/n1 + lim1[0] ; ra  values
	yyy=(0.5+findgen(n0))*(lim0[1]-lim0[0])/n0 + lim0[0] ; dec values

	; force the wrap
	mxx=fltarr(n1+2)
	mxx[1:n1] = xxx[0:n1-1]
	mxx[0]    = xxx[n1-1] - 360.0
	mxx[n1+1] = xxx[0] + 360

	; smooth and resample the data for less crappy lines
	msdf = fltarr(n1+2,n0)
	msdf[1:n1,*] = df[0:n1-1,*]
	msdf[0,*]    = df[n1-1,*]
	msdf[n1+1,*] = df[0,*]
	msdata = min_curve_surf(msdf,/double, $
	    xvalues=mxx,yvalues=yyy,nx=n1+2,ny=n0)
	if (ips.inside eq 1) then begin
	    mxx = reverse(mxx)
	    msdata = reverse(msdata,1)
	endif

	if (noer eq 0) then begin
	    ; print,'/noerase not set, noer eq zero'
	    map_set,lat0,lon0,rot0,name=ips.mapname,/isotropic,      $
		/noborder,position=position,reverse=ips.inside
	    contour,msdata,mxx,yyy,levels=dlevels,/overplot,         $
		c_labels=c_labels,c_colors=c_colors,                 $
		c_linestyle=c_linestyle,c_thick=c_thick
	    if (ips.mapgrid ne 0) then make_me_bin_map_grid,ips
	endif else begin
	    ; print,'/noerase set, noer ne zero'
	    map_set,lat0,lon0,rot0,name=ips.mapname,/isotropic, $
		/noborder,position=position,reverse=ips.inside,/noerase
	    contour,msdata,mxx,yyy,levels=dlevels,/overplot,         $
		c_labels=c_labels,c_colors=c_colors,                 $
		c_linestyle=c_linestyle,c_thick=c_thick
	endelse
end

;
; eof
;
