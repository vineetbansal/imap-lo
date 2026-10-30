;
; $Id: color_scaling.pro 5158 2009-07-31 21:36:32Z gbc $
;
; function color_scaling
; function color_invert
;
; This function rescales a data array in some standard way.
;
; The main scaling choice is controlled by ips.scaling,
; and range truncation is controlled by ips.zrange
; (supplying the extremes desired) and ips.zexpand
; which allows the zmm/smm to expand if data isn't truncated.
;
function color_scaling,          $
	ips,                     $ ; IN: common isoc plotting structure
	data                       ; IN: data array
	compile_opt HIDDEN, STRICTARR

	setup_colormap_hl_color,ips	    ; restore saved hi/lo colors
	if (ips.zrange[0] ne ips.zrange[1] and $
	    ips.zrange[0] ne -999.9) then begin
	    lr = 1
	    lo=where(data le ips.zrange[0])
	    if (lo[0] ne -1) then data[lo] = ips.zrange[0]
	    setup_colormap_lo_color,ips	    ; jam ips.zlocol into lowest
	    ips.zmm[0] = min(data)
	    if (ips.zexpand ne 0 and ips.zrange[0] lt ips.zmm[0]) then $
		ips.zmm[0] = ips.zrange[0]
	endif else begin
	    lr = 0
	    ips.zmm[0] = min(data)
	endelse
	if (ips.zrange[0] ne ips.zrange[1] and $
	    ips.zrange[1] ne -999.9) then begin
	    hr = 1
	    hi=where(data ge ips.zrange[1])
	    if (hi[0] ne -1) then data[hi] = ips.zrange[1]
	    setup_colormap_hi_color,ips	    ; jam ips.zhicol into highest
	    ips.zmm[1] = max(data)
	    if (ips.zexpand ne 0 and ips.zrange[1] gt ips.zmm[1]) then $
		ips.zmm[1] = ips.zrange[1]
	endif else begin
	    hr = 0
	    ips.zmm[1] = max(data)
	endelse

	new=data
	case ips.scaling of
	  'log':  begin
		     good=where(data gt 0)
		     bads=where(data le 0)
		     if (good[0] ne -1) then new[good] = alog10(data[good])
		     if (bads[0] ne -1) then begin
			new[bads] = alog10(ips.zmm[1])
			gsmin = min(new)
			new[bads] = gsmin
		     endif else begin
			gsmin = min(new)
		     endelse
		     gsmax = max(new)
		     if (lr eq 1 and ips.zrange[0] gt 0) then $
			ips.smm[0] = alog10(ips.zrange[0]) else $
			ips.smm[0] = gsmin
		     if (hr eq 1 and ips.zrange[1] gt 0) then $
			ips.smm[1] = alog10(ips.zrange[1]) else $
			ips.smm[1] = gsmax
	          end
	  'sqrt': begin
		     good=where(data gt 0)
		     bads=where(data le 0)
		     if (good[0] ne -1) then new[good] = sqrt(data[good])
		     if (bads[0] ne -1) then begin
			 new[bads] = sqrt(ips.zmm[1])
			 gsmin = min(new)
			 new[bads] = gsmin
		     endif else begin
			gsmin = min(new)
		     endelse
		     gsmax = max(new)
		     if (lr eq 1 and ips.zrange[0] gt 0) then $
			ips.smm[0] = sqrt(ips.zrange[0]) else $
			ips.smm[0] = gsmin
		     if (hr eq 1 and ips.zrange[1] gt 0) then $
			ips.smm[1] = sqrt(ips.zrange[1]) else $
			ips.smm[1] = gsmax
	          end
	  ; 'linear':
	  else:   begin
		     ; all good, no bads
		     gsmin = min(new)
		     gsmax = max(new)
		     if (lr eq 1) then $
			ips.smm[0] = ips.zrange[0] else $
			ips.smm[0] = gsmin
		     if (hr eq 1) then $
			ips.smm[1] = ips.zrange[1] else $
			ips.smm[1] = gsmax
		  end
	endcase

	if (ips.zexpand eq 0) then begin
	    ips.smm[0] = gsmin
	    ips.smm[1] = gsmax
	endif

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
