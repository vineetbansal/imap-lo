;
; $Id: font_sizing.pro 2800 2008-09-16 16:07:10Z gbc $
;
; pro font_sizing_factor
; pro font_sizing_delta
; function safe_x_size
;
; These procedures reduce/increase the font by some amount.
;
; fonts vary by machine, but this works on a few machines
; X:   8, 10, 11, 12, 14, 17, 18, 20, 24, 25, 34
;
function safe_x_size,            $
	ask                        ; IN: requested X size
	if (ask lt  8)               then return, 8
	if (ask eq  9)               then return, 10
	if (ask eq 13)               then return, 12
	if (ask eq 15)               then return, 14
	if (ask eq 16)               then return, 17
	if (ask eq 19)               then return, 20
	if (ask eq 21)               then return, 20
	if (ask eq 22)               then return, 24
	if (ask eq 23)               then return, 24
	if (ask gt 25 and ask lt 30) then return, 25
	if (ask gt 30 and ask lt 34) then return, 34
	if (ask gt 34)               then return, 34
	return, ask
end

pro font_sizing_factor,          $
	ips,                     $ ; IN: common isoc plotting structure
	factor                     ; IN: common isoc plotting structure
	compile_opt HIDDEN, STRICTARR
	ps = ips.fs * factor
	cs = [ps,fix(ps*1.5)]
	if (ps lt 10) then                                      $
		xz=string(safe_x_size(ps),/print,format='(I1)') $
	else                                                    $
		xz=string(safe_x_size(ps),/print,format='(I2)')
	case !d.name of
	  'PS': device,font_size=ps
	  'X': device,set_font='*schoolbook-medium-r-normal--'+xz+'-*'
	  'Z': device,set_character_size=cs
	endcase
end

pro font_sizing_delta,           $
	ips,                     $ ; IN: common isoc plotting structure
	delta                      ; IN: common isoc plotting structure
	compile_opt HIDDEN, STRICTARR
	ps = ips.fs + delta
	cs = [ps,fix(ps*1.5)]
	if (ps lt 10) then                                      $
		xz=string(safe_x_size(ps),/print,format='(I1)') $
	else                                                    $
		xz=string(safe_x_size(ps),/print,format='(I2)')
	case !d.name of
	  'PS': device,font_size=ps
	  'X': device,set_font='*schoolbook-medium-r-normal--'+xz+'-*'
	  'Z': device,set_character_size=cs
	endcase
end

;
; eof
;
