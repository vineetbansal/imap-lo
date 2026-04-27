;
; $Id: 
;
; pro write_ena_dist.pro
;
; This procedure takes in a downstream ion dist, then uses a
; cross-section and a los length to produce and write an ena dist file
; 

pro write_ena_dist,             $
	spda,                   $ ; IN: rad spd array [cm/s] in observer frame
	dist,                   $ ; IN: dist array in s^3/cm^6  
        losl=losl,              $ ; OPT_IN:  los length in AU
        nxch=nxch,              $ ; OPT_IN:  charge-exchange neutral density
        desc=desc,              $ ; OPT_IN:  description                        
        earr=earr,              $ ; OPT_OUT: energy in keV
	jena=jena,              $ ; OPT_OUT: ENA/(cm^2 s sr keV)
        file=file                 ; OPT_OUT: filename prefix for output

if not keyword_set(losl) then losl = 40.0
if not keyword_set(nxch) then nxch = 0.1
if not keyword_set(file) then file='ena_dist'
if not keyword_set(desc) then desc='unknown distribution'

n = n_elements(spda)
jena=spda

mp = 1.67d-24    ; g
keV = 1.6022d-9 ; erg or erg/keV

earr = spda
nwrite=0

for i=0, n-1 do begin
    vr = spda(i)
    energy = 0.5*mp*vr^2/keV ; now in keV
    earr[i] = energy
    jena[i] = -1.0
    if (vr lt 0.0) then begin
        frac = nxch*losl*1.5e13*charge_exchange_H(energy)
        jena[i] = frac*(2.0*(energy*keV)/mp^2)*dist[i]*keV 
        nwrite += 1
    end
end

jena1 = dblarr(nwrite)
earr1 = dblarr(nwrite)

openw,unit,file+'_config.txt',/get_lun
printf,unit,nwrite
nw = 0
for i=0,n-1 do begin
    if (jena[i] ge 0.0) then begin
        printf, unit, earr[i], jena[i]
        jena1[nw] = jena[i]
        earr1[nw] = earr[i]
        nw += 1
    end
end
close,unit

openw,unit,file+'_var_bin.txt',/get_lun
dx = floor(alog10(nwrite))+1
sx = stringer(nwrite,dx)
printf, unit, "# 7:0x2"
printf, unit, "# "
printf, unit, "# "
printf, unit, "# title0='Energy (keV)'"
printf, unit, "# title1='J!DENA!N (ENA cm!U-2!N s!U-1!N sr!U-1!N keV!U-1!N)'"

jmx = max(jena1) 
jmn = min(jena1)
emx = max(earr1)
emn = min(earr1)

if (jmx gt 0.0) then jdx = floor(alog10(jmx))+1 else jdx = 1
if (jmn gt 0.0) then jdn = floor(alog10(jmn))+1 else jdn = 1
if (emx gt 0.0) then edx = floor(alog10(emx))+1 else edx = 1
if (emn gt 0.0) then edn = floor(alog10(emn))+1 else edn = 1

printf, unit, "# desc='",desc,"'"
printf, unit, "# "

for i=0,nwrite-1 do begin
    printf,unit, earr1[i], jena1[i]
end
close,unit

return
end

;
; eof
;
