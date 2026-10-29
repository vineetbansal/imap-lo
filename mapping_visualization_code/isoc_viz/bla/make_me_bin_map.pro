;
; $Id: make_me_bin_map.pro 6598 2010-03-18 10:46:40Z nathanISOC $
;
; pro make_me_bin_map
; pro make_me_bin_map_grid
;
; a switch here among the different flavors
;
pro make_me_bin_map,             $
	ips,                     $ ; IN: common isoc plotting structure
	datafile,                $ ; IN: name of the data file
	position=position,       $ ; IN: plotting window (!{xy}.window)
	p0lon=lon0,              $ ; IN: longitude at center of plot
	p0lat=lat0,              $ ; IN: latitude at center of plot
	rota=rot0                  ; IN: rotation of the plot

	; clipping is not a good idea for these plots
	!p.noclip=1
	case ips.maptool of
	  'orig':  make_me_bin_map_orig,ips,datafile,  $
	  		position=position,p0lon=lon0,p0lat=lat0
	  'patch': make_me_bin_map_patch,ips,datafile, $
	  		position=position,p0lon=lon0,p0lat=lat0,rota=rot0
	  'image': make_me_bin_map_image,ips,datafile, $
	  		position=position,p0lon=lon0,p0lat=lat0,rota=rot0
	  'nopatch': make_me_bin_map_patch,ips,datafile,/noverlay, $
			position=position,p0lon=lon0,p0lat=lat0,rota=rot0
	  'noimage': make_me_bin_map_image,ips,datafile,/noverlay, $
			position=position,p0lon=lon0,p0lat=lat0,rota=rot0
	  'contour': make_me_bin_map_contour,ips,datafile, $
	  		position=position,p0lon=lon0,p0lat=lat0,rota=rot0
	  'contover': make_me_bin_map_contour,ips,datafile, $
	  		position=position,p0lon=lon0,p0lat=lat0,rota=rot0, $
			/noerase
	  else:    print,'no support in make_me_bin_map for ' + ips.maptool
	endcase
	; grid is drawn based on ips.mapgrid
	; other plot overlays may follow...
	!p.noclip=ips.noclip
end

;
; overlay the grid
; the case ips.mapgrid lets us satisfy anyone....
;
pro make_me_bin_map_grid,ips
    !p.noclip=1
    font_sizing_delta,ips,ips.mapgridfsd
    case ips.mapgrid of
     0:
     1: map_grid,color=ips.fg[1],latdel=30,londel=30,label=1,   $
		clip_text=0,/horizon,glinethick=ips.mapgridllt, $
		glinestyle=ips.mapgridlls
     2: map_grid,color=ips.fg[1],latdel=30,londel=30,label=0,   $
		clip_text=0,/horizon,glinethick=ips.mapgridllt, $
		glinestyle=ips.mapgridlls
     3: map_grid,color=ips.fg[1],label=0,/no_grid,              $
		clip_text=0,/horizon
     4: map_grid, latdel=30, londel=30, $
       /LABEL,color=fsc_color(ips.fgcname),/horizon, $
       lats = [-90,-60,-30,0,30,60,90], $
       latnames=['-90','-60','-30','0','30','60',' '], $
       clip_text=0,glinethick=ips.mapgridllt,glinestyle=ips.mapgridlls     
    endcase
    font_sizing_delta,ips,0
    !p.noclip=ips.noclip
end

;
; eof
;
