;
; $Id: 
;
; pro make_kappa_dist.pro
;
; This procedure generates a kappa distribution given on input
; a value for kappa, density [cm-3], a value for the
; temperature[K], a radial bulk velocity [cm/s], and an array for
; radial speeds [cm/s] in the frame of an observer. On output, this
; returns an array with the distribution in s^3/cm^6
;

pro kappa_dist,                 $
	kapp=kapp,              $ ; OPT_IN: kappa value
	temp=temp,              $ ; OPT_IN: temperature [K]
	urad=urad,              $ ; OPT_IN: solar wind spd [cm/s] in radial dir
        dens=dens,              $ ; OPT_IN: solar wind density [#/cm^3]
        atmu=atmu,              $ ; OPT_IN: atomic mass unit                  
        spda=spda,              $ ; OPT_IN: spda .. spdarray [cm/s]
        dist=dist                 ; OPT_OUT: distribution function [s^3/cm^6]

if not keyword_set(kapp) then kapp = 1.8
if not keyword_set(temp) then temp = 1.0e5
if not keyword_set(urad) then urad = 200.0e5
if not keyword_set(dens) then dens = 1.0
if not keyword_set(atmu) then atmu = 1.0
if not keyword_set(spda) then begin
    n = 1000
    spda = 0.0 - 2.0*urad*dindgen(n)/(n-1.0)
end
 
n = n_elements(spda)
dist = dblarr(n)
    
kB = 1.38d-16
mp  = 1.67d-24

omega = sqrt(2.0*kB*temp/(atmu*mp)*(kapp-1.5)/kapp)
   
for i=0, n-1 do begin
    vr = spda[i] - urad
    dist[i] = (dens/(!dpi^1.5*kapp^1.5*omega^3)) * $
      ( Gamma(kapp+1.0)/Gamma(kapp-0.5) ) 
    arg = 1.0 + (vr^2/(kapp*omega*omega))
    if arg lt 1000000.0 then $
      dist[i] = dist[i]*(1.0/arg^(1.0+kapp)) $
    else $
      dist[i] = 0.0
end

return
end

;
; eof
;
