;
; $Id: setup_plot_device.pro 2918 2008-09-26 00:14:03Z nathanISOC $
;
; pro trend_plot__define
; pro set_tps_defaults
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
; These are for trending plots specifically
;
pro trend_plot__define
	ipn = { trend_plot,            $
		dn:'',                $ ; a copy of !p.name
		bg:byte(0),           $ ; 1 background color (!p.background)
		fg:bytarr(5),         $ ; 5 foreground colors
		ctop:0,               $ ; num of intensities - 1 (249)
		scaling:'',           $ ; type of mapping z <-> colors
		scaleopt:'',          $ ; some options for this mapping
		ct:0,                 $ ; color table index
                black:0,              $ ;   colors, black
                purple:24,            $ ;   purple
                blue:56,              $ ;   etc..
                lightblue:100,        $ ;   ..
                green:150,            $ ;   ..
                yellow:190,           $ ;   ..
                orange:200,           $ ;   ..
                red:248,              $ ;   ..
                white:255,            $ ;   ..
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
		eos:''                $ ; add new stuff before this line
	}
end

;
; This routine sets default values for everything once,
; so you can override things if you want to.  Note you
; can reset state by clearing the device name p.dn
;
function set_tps_defaults,tps
	if (n_params() eq 0) then tps={trend_plot}
	if ( tps.dn eq '' ) then begin
		if (!d.name eq 'PS') then begin
			; ps
			tps.bg=255
			tps.fg=[0,254,253,252,251]
                        tps.thick=6.0
                        tps.xthick=4.0
                        tps.ythick=4.0
                        if (tps.fs eq 0) then tps.fs=12
                    endif else begin
			; x z ...
			tps.bg=0
			tps.fg=[255,254,253,252,251]
                        tps.thick=1.0
                        tps.xthick=1.0
                        tps.ythick=1.0
                        tps.fs=10
		endelse
                tps.symsize=2
		tps.ctop=249
		tps.scaling='linear'
		tps.ct=39
                tps.black=0
                tps.purple=24
                tps.blue=56
                tps.lightblue=100
                tps.green=150
                tps.yellow=190
                tps.orange=200
                tps.red=248
                tps.white=255
		tps.zmm=[0.0,1.0]
		tps.position=[0,0,0,0]
		tps.region=[0,0,0,0]
                tps.xs=!d.x_size
		tps.ys=!d.y_size
		tps.xstyle=!x.style
		tps.ystyle=!y.style
		tps.noclip=!p.noclip
		tps.maptool='image'
		setup_map_name,tps
		tps.inside=1
		tps.mapframe='J2000'
		tps.mapgrid=1
		tps.mapdesc=''
                tps.xrange=[0.0,0.0]
                tps.yrange=[0.0,0.0]
                tps.oplot=0
	endif
	tps.dn=!d.name
	return,tps
end

; =====

;
; Default [640,480] z buffer
;
pro setup_trend_z_device,tps
if (n_params() eq 0) then tps={trend_plot}
set_plot,'z'
                                ; device,set_resolution=[640,480]
setup_trend_z_device_common,tps
end

;
; This uses the z buffer as a (no screen required) plotting device
; For the moment, the default is 640 x 480 changeable with set_resolution
;
pro setup_trend_z_device_common,tps
	if (n_params() eq 0) then tps={trend_plot}

	tps=set_tps_defaults(tps)
	; choose a better looking font (TrueType)
	!p.font=1
	device,set_font="Times"
	device,set_character_size=[tps.fs,fix(tps.fs*1.5)]
	
	; usual rainbow + white table
	; loadct,tps.ct,/silent
	setup_trend_colormap,tps

	; good to go
end

;
; Start with the usual rainbow + white table, then diddle
; the 4 reserved foreground colors into shades of gray.
;
pro setup_trend_colormap,tps
	; usual rainbow + white table
	loadct,tps.ct,/silent
;	v = bytarr(5,3)
;	tvlct,v,251,/get
	; diddle the colors 251,252,253,254
;	v[0,0] =  50 & v[0,1] =  50 & v[0,2] =  50
;	v[1,0] = 100 & v[1,1] = 100 & v[1,2] = 100
;	v[2,0] = 150 & v[2,1] = 150 & v[2,2] = 150
;	v[3,0] = 200 & v[3,1] = 200 & v[3,2] = 200
	; and then install them
;	tvlct,v,251
end

;
; This procedure sets up a standard postscript configuration
; If you want to print it as is, just insert showpage a the end.
;
pro setup_trend_eps_device,tps
	if (n_params() eq 0) then tps={trend_plot}

	set_plot,'ps'
	tps=set_tps_defaults(tps)
	; choose a better looking font (from hardware)
	!p.font=0
	device,/schoolbook
	device,font_size=tps.fs
	device,/color,bits=8
	device,/encapsulated

	; usual rainbow + white table
	; loadct,ips.ct,/silent
	setup_trend_colormap,tps

	; device,filename='foo.eps'
	; ...
	; device,/close
end



