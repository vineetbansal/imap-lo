;
; $Id: setup_plot_device.pro 9998 2013-03-13 21:58:19Z DeMajistre $
;
; pro isoc_plot__define
; pro set_ips_defaults
; pro setup_region_position
; pro setup_x_device
; pro setup_eps_device
; pro setup_zv_device
; pro setup_z_device
; pro setup_zz_device
; pro setup_zzz_device
; pro setup_zvar_device
; pro setup_null_device
; pro setup_map_name
; pro setup_colormap
; pro setup_colormap_lo_color
; pro setup_colormap_hi_color
; pro setup_colormap_hl_color
; pro revise_fg_colors
; function bright_fg
; pro report_plot_geometry
;
; The intent here is to collect a standard set of configurations
; for more predictable output.  At the moment, there are no arguments.
;
; These should also take the plotting device back to a known state,
; which is what this next routine is about.
;

;
; A place to hold device dependent information, but in a canonical way.
; This procedure just exists to define the structure format.  It is a
; bug in IDL that such things cannot be defined outside of procedures.
;
; Items marked with a (*) are not (yet) used, I think.
;
pro isoc_plot__define
	ign = { isoc_plot,            $
		dn:'',                $ ; a copy of !p.name
		bg:byte(0),           $ ; 1 background color (!p.background)
		fg:bytarr(5),         $ ; 5 foreground colors
		ctop:0,               $ ; num of intensities - 1 (249)
		scaling:'',           $ ; type of mapping z <-> colors
		scaleopt:'',          $ ; some options for this mapping
		ct:0,                 $ ; color table index
		zmm:fltarr(2),        $ ; min and max of data (original)
		smm:fltarr(2),        $ ; min and max of data (scaled)
		position:fltarr(4),   $ ; cf !p.position, plot only (*)
		region:fltarr(4),     $ ; cf !p.region, plot + surrounds (*)
		fs:0,                 $ ; base font_size in points
		xs:0,                 $ ; a copy of !d.x_size (*)
		ys:0,                 $ ; a copy of !d.y_size (*)
		xstyle:0,             $ ; a copy of !x.style
		ystyle:0,             $ ; a copy of !y.style
		noclip:0,             $ ; a copy of !p.noclip
		maptool:'',           $ ; either patch/image/orig
		mapname:'',           $ ; from map_proj_info,proj_names=n
		inside:0,             $ ; or 1 for celestial sphere
		mapframe:'',          $ ; SPICE coordinate frame
		mapgrid:0,            $ ; set nonzero to have a grid
		mapdesc:'',           $ ; text description/title of map
                bartitle:'',          $ ; title for bottom colorbar
                psym:0,               $ ; symbols to plot with
                symsize:2,            $ ; size of symbols            
                xlog:0,               $ ; log scaling in x
                ylog:0,               $ ; log scaling in y
                xrange:fltarr(2),     $ ; range to use (x)
                yrange:fltarr(2),     $ ; range to use (y)
                linestyle:0,          $ ; linestyle to use
                thick:9.0,            $ ; thickness of lines
                xthick:6.0,           $ ; x thickness
                ythick:6.0,           $ ; y thickness
                nolegend:0,           $ ; set to 1 to kill the legend          
                oplot:0,              $ ; if overplot data
		pltname:'',           $ ; a filename for the output plot
		unused:'',            $ ; add new stuff before this line
		cbartool:'',          $ ; either ver2/orig
		zrange:fltarr(2),     $ ; range to use in colors
		zlocol:bytarr(1,3),   $ ; replacement lo-limit color
		zhicol:bytarr(1,3),   $ ; replacement hi-limit color
		slocol:bytarr(1,3),   $ ; saved (original) lo colors
		shicol:bytarr(1,3),   $ ; saved (original) hi colors
		ctsilent:0,           $ ; silent kw on colortable load
		zexpand:0,            $ ; allow expansion of colorbar
		ctstrch:bytarr(2),    $ ; resample colors between limits
		mapgridfsd:0,         $ ; map grid font size delta
		mapgridllt:0,         $ ; map grid gridline thickness
		mapgridlls:0,         $ ; map grid gridline style
		mapoffsetx:0,         $ ; an offset for labels
		mapoffsety:0,         $ ; an offset for labels
		mapifmap:0,           $ ; control a map_image default
		mapiblin:0,           $ ; control a map_image default
                fgcname:'',           $ ; foreground color for some options (ips.mapgrid=4)         
		eos:''                $ ; add new stuff before this line
              }

end

;
; This routine sets default values for everything once,
; so you can override things if you want to.  Note you
; can reset state by clearing the device name p.dn
;
function set_ips_defaults,ips
	if (n_params() eq 0) then ips={isoc_plot}
	if ( ips.dn eq '' ) then begin
		if (!d.name eq 'PS') then begin
			; ps
			ips.bg=255
			ips.fg=[0,254,253,252,251]
		endif else begin
			; x z ...
			ips.bg=0
			ips.fg=[255,254,253,252,251]
		endelse
		ips.ctop=249
		ips.scaling='linear'
		if (ips.ct eq 0) then ips.ct=39
		ips.zmm=[0.0,1.0]
		ips.position=[0,0,0,0]
		ips.region=[0,0,0,0]
                if (ips.fs eq 0) then ips.fs=12
                ips.xs=!d.x_size
		ips.ys=!d.y_size
		ips.xstyle=!x.style
		ips.ystyle=!y.style
		ips.noclip=!p.noclip
		ips.maptool='image'
		setup_map_name,ips
		ips.inside=1
		ips.mapframe='J2000'
		ips.mapgrid=1
		ips.mapdesc=''
                ips.xrange=[0.0,0.0]
                ips.yrange=[0.0,0.0]
                ips.thick=6.0
                ips.xthick=4.0
                ips.ythick=4.0
                ips.oplot=0
		ips.pltname=''
		ips.unused=''
                ips.cbartool='ver2' ; ips.cbartool='orig'
                ips.zrange=[-999.9,-999.9]
		ips.ctsilent=1
		ips.zexpand=1 ; --> 1 after first round publications
		if (ips.ctstrch[0] ge ips.ctstrch[1]) then ips.ctstrch=[0,0]
		ips.mapgridfsd=-2
		ips.mapgridllt=1
		ips.mapgridlls=1
		ips.mapoffsetx=3
		ips.mapoffsety=3
		ips.mapifmap=1 ; --> 1 after first round publications
		ips.mapiblin=0
                ips.fgcname='yellow'
		ips.eos='end-of-structure'
	endif
	ips.dn=!d.name
	return,ips
end

;
; This procedure sets some standard device parameters for a x session.
;
pro setup_x_device,ips,xsize=xsize,ysize=ysize
	if (n_params() eq 0) then ips={isoc_plot}

	set_plot,'x'
	ips=set_ips_defaults(ips)
	;
	; arrange for backing store and true colors
	;
	if (not keyword_set(xsize)) then xsize=840
	if (not keyword_set(ysize)) then ysize=525
	; window,0,retain=2
	window,0,retain=2,xsize=xsize,ysize=ysize
	device,true=24
	device,decomposed=0

	;
	; choose a better looking font (from hardware)
	;
	!p.font=0
	fs=string(ips.fs,/print,format='(I2)')
	if (ips.fs lt 10) then fs=string(ips.fs,/print,format='(I1)')
	device,set_font='*schoolbook-medium-r-normal--'+fs+'-*'

	; loadct and other things
	setup_colormap,ips

	; good to go
end

;
; This procedure sets up a standard postscript configuration
; If you want to print it as is, just insert showpage a the end.
;
pro setup_eps_device,ips
	if (n_params() eq 0) then ips={isoc_plot}

	set_plot,'ps'
	ips=set_ips_defaults(ips)
	; choose a better looking font (from hardware)
	!p.font=0
	device,/schoolbook
	device,font_size=ips.fs
	device,/color,bits=8
	device,/encapsulated

	; loadct and other things
	setup_colormap,ips

	; device,filename='foo.eps'
	; ...
	; device,/close
end


;
; This procedure sets up a standard postscript configuration
; If you want to print it as is, just insert showpage a the end.
;
pro setup_ps_device,ips
	if (n_params() eq 0) then ips={isoc_plot}

	set_plot,'ps'
	ips=set_ips_defaults(ips)
	; choose a better looking font (from hardware)
	!p.font=0
	device,/schoolbook
	device,font_size=ips.fs
	device,/color,bits=8

	; loadct and other things
	setup_colormap,ips

	; device,filename='foo.eps'
	; ...
	; device,/close
end


;
; This uses the z buffer as a (no screen required) plotting device
; For the moment, the default is 640 x 480 changeable with set_resolution
;
pro setup_z_device_common,ips
	if (n_params() eq 0) then ips={isoc_plot}

	ips=set_ips_defaults(ips)
	; choose a better looking font (TrueType)
	; it's not clear whether the /tt_font is or isn't required
	!p.font=1
	device,set_font="Times",/tt_font
	device,set_character_size=[ips.fs,fix(ips.fs*1.5)]
	
	; loadct and other things
	setup_colormap,ips

	; good to go
end
;
;
;
pro setup_zv_device,ips
	if (n_params() eq 0) then ips={isoc_plot}
	set_plot,'z'
	device,set_resolution=[640,853]
	setup_z_device_common,ips
end
;
; Default [640,480] z buffer
;
pro setup_z_device,ips
	if (n_params() eq 0) then ips={isoc_plot}
	set_plot,'z'
	; device,set_resolution=[640,480]
	setup_z_device_common,ips
end
;
; A 50% larger version
;
pro setup_zz_device,ips
	if (n_params() eq 0) then ips={isoc_plot}
	set_plot,'z'
	device,set_resolution=[960,720]
	setup_z_device_common,ips
end
;
; A 100% larger version
;
pro setup_zzz_device,ips
	if (n_params() eq 0) then ips={isoc_plot}
	set_plot,'z'
	device,set_resolution=[1280,960]
	setup_z_device_common,ips
end
;
; A variable size device
; The default here is 8.5in x 5.5in @ 300dpi
;
pro setup_zvar_device,ips,xsize=xsize,ysize=ysize
	if (n_params() eq 0) then ips={isoc_plot}
	if (not keyword_set(xsize)) then xsize=2550
	if (not keyword_set(ysize)) then ysize=1650
	set_plot,'z'
	device,set_resolution=[xsize,ysize]
	setup_z_device_common,ips
end

;
; This makes no output in case you want to just calculate safely.
;
pro setup_null_device,ips
	if (n_params() eq 0) then ips={isoc_plot}
	set_plot,'null'
	ips=set_ips_defaults(ips)
end

;
; This makes sure the mapname is one of the allowed ones:
; otherwise it gets set to HammerAitoff
;
pro setup_map_name,ips,newname
	if (n_params() gt 1) then ips.mapname=newname
	case ips.mapname of
	  'Aitoff':
	  'Hammer':               ips.mapname='HammerAitoff'
	  'HammerAitoff':
	  'Cylindrical':
	  'MillerCylindrical':
	  'Robinson':
	  'Mollweide':
	  'Azimuthal':            ips.mapname='AzimuthalEquidistant'
	  'Sinusoidal':
	  else:                   ips.mapname='HammerAitoff'
	endcase
end

;
; Start with the usual rainbow + white table, then diddle
; the 4 reserved foreground colors into shades of gray.
;
; NOTE: this colormap is pretty poor and should be fixed.
;    0   27  52  57    102  146    191    235    250
;R   0 ->88->     0 ......... 0 -> 255 .. 255 .. 255
;G   0 .......... 0 -> 255 ....... 255 ->   0 .... 0
;B   0  ->  255 ...... 255 -> 0 ........... 0 .... 0
;
; Colormaps 27 and 33 have also been mentioned as possibilities.
;
; FIXME: should respect ctop
;
pro setup_colormap,ips
	; Use IDL tables for ct>=0, custom tables otherwise.
	; if (ips.ct ge 0) then loadct,ips.ct,/silent else loadaltct,ips,/silent
	; loadct,ips.ct,/silent
	loadaltct,ips
	v = bytarr(5,3)
	tvlct,v,251,/get
	; diddle the colors 251,252,253,254, but not 255
	v[0,0] =  50 & v[0,1] =  50 & v[0,2] =  50
	v[1,0] = 100 & v[1,1] = 100 & v[1,2] = 100
	v[2,0] = 150 & v[2,1] = 150 & v[2,2] = 150
	v[3,0] = 200 & v[3,1] = 200 & v[3,2] = 200
	; NB v[4,*] is unmolested, and then install them:
	tvlct,v,251
	; save the colors at 1 and 250
	; and set gray defaults
	x = bytarr(256,3)
	tvlct,x,0,/get
	ips.zlocol = [  25,  25,  25 ]
	ips.slocol = x[1,*]
	ips.zhicol = [ 225, 225, 225 ]
	ips.shicol = x[250,*]
end

;
; limit-related didling of the colormap
; FIXME: should respect ctop
;
pro setup_colormap_hl_color,ips
    tvlct,ips.slocol,1
    tvlct,ips.shicol,250
end
pro setup_colormap_lo_color,ips
    tvlct,ips.zlocol,1
end
pro setup_colormap_hi_color,ips
    tvlct,ips.zhicol,250
end

;
; Enough rope to hang yourself--overwrite all fg colors
; FIXME: should respect ctop
;
pro revise_fg_colors,newcolors
        ; newcolors = bytarr(5,3)
        if (n_elements(newcolors) ne 15) then return;
        tvlct,v,251,/get
        ; diddle the colors 251,252,253,254, but not 255
	newcolors[4,0] = v[4,0]
	newcolors[4,1] = v[4,1]
	newcolors[4,2] = v[4,2]
        ; copying v[4,*]; and then install them:
        tvlct,newcolors,251
end

;
; Some strong color possibilities ripped from w3school;
; there are plenty more at /usr/share/netpbm/rgb.txt
;   BlueViolet      8A2BE2      138  40 226
;   SpringGreen     00FF7F        0 255 127
;   Crimson         DC143C      220  20  60
;   DarkGoldenRod   B8860B      184 134  11
;   LightSeaGreen   2CB2AA       44 178 170
;   Maroon          800000      128   0   0
;   DarkOrange      FF8C00      255 140   0
;   DeepPink        FF1493      255  20 141
;   Olive           8C8000      140 128   0
;   Plum            DDACDD      221 172 221
;   Brown           A52A2A      165  42  42
;   Teal            008060        0 128  96
;
; FIXME: should respect ctop
;
function bright_fg,offset
	c = bytarr(5,3)
	v = bytarr(13,3)
	v[ 0,0] = 138 & v[ 0,1] =  40 & v[ 0,2] = 226
	v[ 1,0] =   0 & v[ 1,1] = 255 & v[ 1,2] = 127
	v[ 2,0] = 220 & v[ 2,1] =  20 & v[ 2,2] =  60
	v[ 3,0] = 184 & v[ 3,1] = 134 & v[ 3,2] =  11
	v[ 4,0] =  44 & v[ 4,1] = 178 & v[ 4,2] = 170
	v[ 5,0] = 128 & v[ 5,1] =   0 & v[ 5,2] =   0
	v[ 6,0] = 255 & v[ 6,1] = 140 & v[ 6,2] =   0
	v[ 7,0] = 255 & v[ 7,1] =  20 & v[ 7,2] = 141
	v[ 8,0] = 140 & v[ 8,1] = 128 & v[ 8,2] =   0
	v[ 9,0] = 221 & v[ 9,1] = 172 & v[ 9,2] = 221
	v[10,0] = 165 & v[10,1] =  42 & v[10,2] =  42
	v[11,0] =   0 & v[11,1] = 128 & v[11,2] =  96
	v[12,0] =   0 & v[12,1] =   0 & v[12,2] =   0
	if (offset lt 0) then offset = 0
	if (offset gt 8) then offset = 8
	for j=0,4 do begin
	  for i=0,2 do begin
	    c[j,i] = v[offset+j,i]
	  endfor
	endfor
	return,c
end

;
; A procedure to dump out some details about the current plot geometry.
; The format is in flux, and the report is only to a file.
; The intent is that the file could be sourced by a shell, perl, ....
;
pro report_plot_geometry,ips,file
	openw,unit,file,/get_lun
	printf,unit,'# IDL report_plot_geometry Version 0'
	printf,unit,'# device:'
	;
	printf,unit,'d_x_size=',     strtrim(!d.x_size,2)
	printf,unit,'d_y_size=',     strtrim(!d.y_size,2)
	printf,unit,'d_x_vsize=',    strtrim(!d.x_vsize,2)
	printf,unit,'d_y_vsize=',    strtrim(!d.y_vsize,2)
	;
	printf,unit,'# x_axis:'
	printf,unit,'x_range_0=',    strtrim(!x.range[0],2)
	printf,unit,'x_range_1=',    strtrim(!x.range[1],2)
	printf,unit,'x_crange_0=',   strtrim(!x.crange[0],2)
	printf,unit,'x_crange_1=',   strtrim(!x.crange[1],2)
	printf,unit,'x_window_0=',   strtrim(!x.window[0],2)
	printf,unit,'x_window_1=',   strtrim(!x.window[1],2)
	printf,unit,'x_region_0=',   strtrim(!x.region[0],2)
	printf,unit,'x_region_1=',   strtrim(!x.region[1],2)
	printf,unit,'x_inter=',      strtrim(!x.s[0],2)
	printf,unit,'x_slope=',      strtrim(!x.s[1],2)
	;
	printf,unit,'# y_axis:'
	printf,unit,'y_range_0=',    strtrim(!y.range[0],2)
	printf,unit,'y_range_1=',    strtrim(!y.range[1],2)
	printf,unit,'y_crange_0=',   strtrim(!y.crange[0],2)
	printf,unit,'y_crange_1=',   strtrim(!y.crange[1],2)
	printf,unit,'y_region_0=',   strtrim(!y.region[0],2)
	printf,unit,'y_region_1=',   strtrim(!y.region[1],2)
	printf,unit,'y_window_0=',   strtrim(!y.window[0],2)
	printf,unit,'y_window_1=',   strtrim(!y.window[1],2)
	printf,unit,'y_inter=',      strtrim(!y.s[0],2)
	printf,unit,'y_slope=',      strtrim(!y.s[1],2)
	;
	printf,unit,'# eof'
	;
	; dumps everything:
	;
	; help,!d,/structure,output=device_help
	; printf,unit,device_help
	; printf,unit,!d
	; help,!x,/structure,output=x_axis_help
	; printf,unit,x_axis_help
	; printf,unit,!x
	; help,!y,/structure,output=y_axis_help
	; printf,unit,y_axis_help
	; printf,unit,!y
	close,unit
end

;
; eof
;
