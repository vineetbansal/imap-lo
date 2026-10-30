;
; $Id: make_colorbar.pro 3924 2009-01-14 16:26:16Z gbc $
;
; pro make_colorbar_xy
;
; This routine is now a switch for the various colorbar routines
;
; These procedures generate colorbars in either x or y.
; One of xtitle or ytitle is required so we know which one.
;
pro make_colorbar_xy,            $
	ips,                     $ ; IN: common isoc plotting structure
	position=position,       $ ; IN: location, cf. plot position
	xtitle=xtitle,           $ 
	ytitle=ytitle,           $
        nticks=nticks,           $
        scaleformat=scaleformat,  $
        title_switch=title_switch,  $
        scale_switch=scale_switch     
       
	compile_opt HIDDEN, STRICTARR

	if (not keyword_set(xtitle) and not keyword_set(ytitle)) then begin
		print, 'One of xtitle or ytitle must be set'
		return
        endif

        case ips.cbartool of
            'orig': make_colorbar_xy_orig,ips, $
                      position=position,xtitle=xtitle,ytitle=ytitle
            'ver2': make_colorbar_xy_ver2,ips, $
                      position=position,xtitle=xtitle,ytitle=ytitle, $
                      nticks=nticks,scaleformat=scaleformat,  $
                      title_switch=title_switch,  $
                      scale_switch=scale_switch  
            else:   print,'no support in make_colorbar_xy for'+ips.cbartool
        endcase

end

;
; eof
;
