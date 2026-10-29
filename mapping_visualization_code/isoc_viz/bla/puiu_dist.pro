;
; $Id: 
;
; pro puiu_dist.pro
;
; This procedure generates a pui distribution inside the termination
;
; This uses the approximation that the pickup ion dist is
; 
;   [beta*nh/(8 pi u^4)] * [r1^2/(r*w^1.5)] * exp(-lambda/(r*w^1.5)) 
; 
; in the upstream region. Here, w = v/u where u is the solar wind speed.
; beta is the ionization rate at 1 AU. nH is the neutral density of
; interstellar H that makes it into the heliosphere. lambda is the
; distance (in AU) at which the ionization cutoff starts. 
; 
; where v is speed and w is v/u
; rs is the compression ratio

pro puiu_dist,                   $
	beta=beta,              $ ; OPT_IN: ionization rate [1/s] at 1 AU
	lamb=lamb,              $ ; OPT_IN: Ionization cut-off in AU
	uswu=uswu,              $ ; OPT_IN: upwind solar wind spd [cm/s] 
        dens=dens,              $ ; OPT_IN: neutral int density [cm^-3]
        rads=rads,              $ ; OPT_IN: radial distance 
        spda=spda,              $ ; OPT_IN: spda .. rad spdarray [cm/s] in fixed frame
        dist=dist                 ; OPT_OUT: distribution function [s^3/cm^6]

if not keyword_set(beta) then beta = 6.6e-7
if not keyword_set(lamb) then lamb = 3.0
if not keyword_set(uswu) then uswu = 300.0e5
if not keyword_set(dens) then dens = 0.1
if not keyword_set(rads) then rats = 100.0
if not keyword_set(spda) then begin
    n = 1000
    spda = 0.0- 2.0*urad*dindgen(n)/(n-1.0)
end
 
n = n_elements(spda)
dist = dblarr(n)
    
kB = 1.38d-16
mp  = 1.67d-24

for i=0, n-1 do begin
    vru = abs(spda[i] - uswu)
    w = vru/uswu
    if (w gt 1.0) then $
      dist[i] = 0.0 $
    else begin
        if (w gt 0.0001) then $
          dist[i] = (beta*dens*1.5e13/(8.0*!dpi*usw^4)) * $
          ( 1.0 / (rads * w^1.5 ) ) *exp(-lambd/(rads*w^1.5)) $
        else $
          dist[i] = 0.0
    end
end

return
end

;
; eof
;
