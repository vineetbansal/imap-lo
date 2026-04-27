;
; $Id: make_me_bin_map_patch.pro 5458 2009-09-16 14:19:04Z gbc $
;
; pro make_me_bin_map_patch
;
; This procedure wraps 2-d histogram data around a sphere.
; The data is assumed to come from me_bin so that information
; describing the data can be pulled from the header in the file.
;
; We'll follow IDL's usage of lat and lon for the spherical coordinates,
; although in practice the units might be ra(-1),dec(-0) or ...
;
; Note that C and IDL have different ideas of X and Y, so 0 here refers
; to the dimension of the array that increases with line number, and 1
; refers to the dimension that increases from left to right.
;
; Note the IDL longitude runs -180..180 rather than 0..360 and is
; hard-wired to the outside-looking-in view (i.e. as is the case
; working with continents on the earth).
;
; map_patch is used when the image has fewer pixels than the device
; map_image is used when the device has fewer pixels than the image
;
; the trigrid() routine within map patch is prone to segfaults.
;
; rotating the map doesn't work with inside/outside so it is disabled.
;
pro make_me_bin_map_patch,       $
	ips,                     $ ; IN: common isoc plotting structure
	datafile,                $ ; IN: name of the data file
	position=position,       $ ; IN: plotting window (!{xy}.window)
	p0lon=lon0,              $ ; IN: longitude at center of plot
	p0lat=lat0,              $ ; IN: latitude at center of plot
	rota=rot0,               $ ; IN: rotation of the plot
	noverlay=nova		   ; IN: nuke the data overlay

	compile_opt HIDDEN, STRICTARR

	if (not keyword_set(lon0)) then lon0=0.0
	if (not keyword_set(lat0)) then lat0=0.0
	if (not keyword_set(rot0)) then rot0=0.0 else rot0=0.0

	; get the data and scale it
	ds=get_me_bin_header_size(datafile)
	data=read_ascii(datafile,delimiter=' ',header=hdr,data_start=ds)
	df=read_ascii_data_array(datafile,' ',ds,data)
	a=color_scaling(ips,df)
	if (keyword_set(nova)) then a[where(a ne 0)] = 0

	;
	; get the magic numbers to set up geometry
	; and establish the spherical mapping
	;
	parse_me_bin_header,hdr,lim0,n0,t0,lim1,n1,t1,dl,desc
	parse_me_bin_extra,ips,hdr
	if (ips.inside eq 1) then lng0 = -lon0 else lng0 = lon0
	map_set,lat0,lng0,rot0,name=ips.mapname,/isotropic, $
		/noborder,position=position;reverse=ips.inside
	;
	; the underlying map_patch routine can't handle the
	; map_set reverse option, so we flip it explicitly in
	; lon which we need to provide (rather than xxx) since
	; map_patch.pro makes the wrong deductions without it.
	;
	xxx=(0.5+findgen(n1))*(lim1[1]-lim1[0])/n1 + lim1[0]   ; ra  values
	branch = where(xxx gt 180)
	xxx[branch] = xxx[branch] - 360
	if (ips.inside eq 1) then xxx = reverse(xxx)
	yyy=(0.5+findgen(n0))*(lim0[1]-lim0[0])/n0 + lim0[0]   ; dec values
	;
	lat = replicate(1.0, n1) # yyy  ; spray dec value around each lat line
	lon = xxx # replicate(1.0, n0)  ; spray ra  value around each lon line
	;
	case !d.name of
	  'PS':  make_me_bin_map_patch_overlay_ps,a,lon,lat,ips.ctop,ips.smm
	  'X':   make_me_bin_map_patch_overlay_xz,a,lon,lat,ips.ctop,ips.smm
	  'Z':   make_me_bin_map_patch_overlay_xz,a,lon,lat,ips.ctop,ips.smm
	  else:  print,'no support in make_me_bin_map_patch for ' + !d.name
	endcase
	;
	; ... and do it implicitly from here on
	;
	if (ips.inside eq 1) then $
	    map_set,lat0,lon0,rot0,name=ips.mapname,/isotropic, $
		/noborder,position=position,reverse=ips.inside,/noerase

	if (ips.mapgrid ne 0) then make_me_bin_map_grid,ips
end

;
; x/z version drops it into the pixels
;
pro make_me_bin_map_patch_overlay_xz,image,lon,lat,ctop,smm
	bimage=bytscl(image,top=ctop,min=smm[0],max=smm[1]) + 1

	awarp = map_patch(bimage,lon,lat, $
		/triangulate, $
		missing=!p.background, $
		xstart=x0,ystart=y0)

	tv,awarp,x0,y0
end

;
; ps version scales the pixels
;
pro make_me_bin_map_patch_overlay_ps,image,lon,lat,ctop,smm
	bimage=bytscl(image,top=ctop,min=smm[0],max=smm[1]) + 1

	awarp = map_patch(bimage,lon,lat, $
		/triangulate, $
		missing=!p.background, $
		xstart=x0,ystart=y0,xsize=xs,ysize=ys)

	tv,awarp,x0,y0,xsize=xs,ysize=ys
end

;
; eof
;
