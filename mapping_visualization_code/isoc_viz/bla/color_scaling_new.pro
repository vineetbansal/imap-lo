;
; $Id: color_scaling_new.pro 4666 2009-05-18 13:52:04Z gbc $
;
; function color_scaling
; function color_invert
;
; This function rescales a data array in some standard way.
;
; The main scaling choice is controlled by ips.scaling,
; and there is provision for expansion/contraction of the
; range through a (TBD) ips.scaleopt setting
;
; It is implicitly assumed in this version that the data
; is non-negative.  For the log scaling, the min of the
; plot is half of the smallest datum.
;
function color_scaling,          $
	ips,                     $ ; IN: common isoc plotting structure
	data                       ; IN: data array
	compile_opt HIDDEN, STRICTARR

	loex = 0.0
	lofl = 0
	hiex = 0.0
	hifl = 0
	ips.zmm[0] = min(data)
	ips.zmm[1] = max(data)

	setup_colormap_hl_color,ips
	if (ips.zrange[0] ne ips.zrange[1] and $
	    ips.zrange[0] ne -999.9) then begin
	    lo=where(data le ips.zrange[0])
	    if (lo[0] ne -1) then data[lo] = ips.zrange[0] else lofl = 1
	    ips.zmm[0] = ips.zrange[0]
	    setup_colormap_lo_color,ips
	endif
	if (ips.zrange[0] ne ips.zrange[1] and $
	    ips.zrange[1] ne -999.9) then begin
	    hi=where(data ge ips.zrange[1])
	    if (hi[0] ne -1) then data[hi] = ips.zrange[1] else hifl = 1
	    ips.zmm[1] = ips.zrange[1]
	    setup_colormap_hi_color,ips
	endif

	new=data
	case ips.scaling of
	  'log':  begin
		     good=where(data gt 0)
		     bads=where(data le 0)
		     if (good[0] ne -1) then new[good] = alog10(data[good])
		     if (bads[0] ne -1) then begin
			new[bads] = alog10(ips.zmm[1])
			gtzeromin = min(new) - alog10(2)
			new[bads] = gtzeromin
		     endif
		     if (ips.zmm[0] le 0) then ips.zmm[0] = gtzeromin
	             if (lofl ne 0) then loex = alog10(ips.zmm[0])
	             if (hifl ne 0) then hiex = alog10(ips.zmm[1])
	          end
	  'sqrt': begin
		     good=where(data gt 0)
		     bads=where(data le 0)
		     if (good[0] ne -1) then new[good] = sqrt(data[good])
		     if (bads[0] ne -1) then new[bads] = 0
		     if (ips.zmm[0] le 0) then ips.zmm[0] = 0
	             if (lofl ne 0) then loex = sqrt(ips.zmm[0])
	             if (hifl ne 0) then hiex = sqrt(ips.zmm[1])
	          end
	  'linear':begin
	             if (lofl ne 0) then loex = (ips.zmm[0])
	             if (hifl ne 0) then hiex = (ips.zmm[1])
		  end
	  else:   begin
	             if (lofl ne 0) then loex = (ips.zmm[0])
	             if (hifl ne 0) then hiex = (ips.zmm[1])
		  end
	endcase

	ips.smm[0] = min(new)
	ips.smm[1] = max(new)
	if (lofl ne 0) then ips.smm[0] = loex
	if (hifl ne 0) then ips.smm[1] = hiex

	return,new
end

;
; this function inverts the preceding arrangements
;
function color_invert,           $
	ips,                     $ ; IN: common isoc plotting structure
	data                       ; IN: data array

	case ips.scaling of
	  'log':     z = 10^(data)
	  'sqrt':    z = data*data
	  'linear':  z = data
	  else:      z = data
	endcase
	return,z
end
;
; eof
;
