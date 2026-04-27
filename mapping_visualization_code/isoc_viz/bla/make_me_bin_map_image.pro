;
; $Id: make_me_bin_map_image.pro 5671 2009-10-13 18:38:38Z gbc $
;
; pro make_me_bin_map_image
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
pro make_me_bin_map_image,       $
	ips,                     $ ; IN: common isoc plotting structure
	datafile,                $ ; IN: name of the data file
	position=position,       $ ; IN: plotting window (!{xy}.window)
	p0lon=lon0,              $ ; IN: longitude at center of plot
	p0lat=lat0,              $ ; IN: latitude at center of plot
	rota=rot0,               $ ; IN: rotation of the plot
	noverlay=nova,           $ ; IN: nuke the data overlay
	fmap=fmap                  ; IN: if zero use original code

	compile_opt HIDDEN, STRICTARR

	if (not keyword_set(lon0)) then lon0=0.0
	if (not keyword_set(lat0)) then lat0=0.0
	if (not keyword_set(rot0)) then rot0=0.0 else rot0=0.0
	if (not keyword_set(fmap)) then fmap=ips.mapifmap

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
	map_set,lat0,lon0,rot0,name=ips.mapname,/isotropic, $
		/noborder,position=position,reverse=ips.inside
	;
	; map_image.pro:
	;
	; "Latitude and Longitude values "(in the array)"
	; "refer to the CENTER of each cell."
	; however the default of +/- 90 doesn't make sense
	;
	if (fmap eq 0) then begin
	  min = float(lim1[0]) + float(lim1[1]-lim1[0])/(2.0*n1)
	  max = min + 360.0 - 360.0/n1
	  typ = !d.name
	endif else begin
	  min = float(lim1[0]) + float(lim1[1]-lim1[0])/(2.0*n1)
	  max = float(lim1[1]) - float(lim1[1]-lim1[0])/(2.0*n1)
	  typ = 'f' + !d.name
	  latmin = float(lim0[0]) + float(lim0[1]-lim0[0])/(2.0*n0)
	  latmax = float(lim0[1]) - float(lim0[1]-lim0[0])/(2.0*n0)
	endelse
	;
	case typ of
	  'PS':  make_me_bin_map_image_overlay_ps,a,min,max,ips.ctop,ips.smm
	  'X':   make_me_bin_map_image_overlay_xz,a,min,max,ips.ctop,ips.smm
	  'Z':   make_me_bin_map_image_overlay_xz,a,min,max,ips.ctop,ips.smm
	  'fPS': make_me_bin_map_image_olatlon_ps,a,min,max,ips.ctop,ips.smm,$
		    latmin,latmax,ips.mapiblin
	  'fX':  make_me_bin_map_image_olatlon_xz,a,min,max,ips.ctop,ips.smm,$
		    latmin,latmax,ips.mapiblin
	  'fZ':  make_me_bin_map_image_olatlon_xz,a,min,max,ips.ctop,ips.smm,$
		    latmin,latmax,ips.mapiblin
	  else:  print,'no support in make_me_bin_map_image for ' + !d.name
	endcase

	if (ips.mapgrid ne 0) then make_me_bin_map_grid,ips
end

;
; x/z version drops it into the pixels
;
pro make_me_bin_map_image_overlay_xz,image,min,max,ctop,smm
	bimage=bytscl(image,top=ctop,min=smm[0],max=smm[1]) + 1

	awarp = map_image(bimage,x0,y0,compress=1, $
		missing=!p.background, $
		lonmin=min, lonmax=max)

	tv,awarp,x0,y0
end

;
; ps version scales the pixels
;
pro make_me_bin_map_image_overlay_ps,image,min,max,ctop,smm
	bimage=bytscl(image,top=ctop,min=smm[0],max=smm[1]) + 1

	awarp = map_image(bimage,x0,y0,xs,ys,compress=1, $
		missing=!p.background, $
		lonmin=min,lonmax=max)

	tv,awarp,x0,y0,xsize=xs,ysize=ys
end

;
; x/z version drops it into the pixels -- with latmin and latmax values
;
pro make_me_bin_map_image_olatlon_xz,image,min,max,ctop,smm,lmin,lmax,blin
	bimage=bytscl(image,top=ctop,min=smm[0],max=smm[1]) + 1

	awarp = map_image(bimage,x0,y0,compress=1, $
		missing=!p.background, bilinear=blin, $
		lonmin=min, lonmax=max, latmin=lmin, latmax=lmax)

	tv,awarp,x0,y0
end

;
; ps version scales the pixels -- with latmin and latmax values
;
pro make_me_bin_map_image_olatlon_ps,image,min,max,ctop,smm,lmin,lmax,blin
	bimage=bytscl(image,top=ctop,min=smm[0],max=smm[1]) + 1

	awarp = map_image(bimage,x0,y0,xs,ys,compress=1, $
		missing=!p.background, bilinear=blin, $
		lonmin=min,lonmax=max, latmin=lmin, latmax=lmax)

	tv,awarp,x0,y0,xsize=xs,ysize=ys
end

;
; eof
;
