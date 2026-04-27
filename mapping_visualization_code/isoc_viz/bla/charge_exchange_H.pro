;
; $Id:
;
; function charge_exchange_H(energy)
;
; Provides the charge-exchange cross-section in cm^2 as a function of
; energy in keV
;

function charge_exchange_H, energy 

a1 = 4.15d0
a2 = 0.531d0
a3 = 67.3d0
out = ((a1 - a2*alog(energy))^2) *(1.0-exp(-a3/energy))^4.5
out *= 1.0d-16

return, out
end

;
; eof
;
