;
; $Id: bin_outer_map.pro 18280 2024-04-29 16:52:25Z ibexops $
;
; nas 9/2/08
; 
; pro bin_outer_map
;
; This procedure produces the datafiles in bin format
;
; Needs stringer.pro compiled
; 
pro bin_outer_map,            $
           ie     ,           $ ; IN energy step
           file   ,           $ ; IN filename (refresh file)
           flx_mul = flx_mul, $ ;OPT_IN flx multiplier                         
           flx_log = flx_log, $ ;OPT_IN set keyword to use log scale [base10]
           flx_nam = flx_nam, $ ;OPT_IN flx name                         
           flx_min = flx_min, $ ;OPT_IN flx min
           flx_max = flx_max, $ ;OPT_IN flx max
           desc    = desc      ;OPT_IN description

day = 24*60*60
if not keyword_set(flx_mul) then flx_mul = 1.0
if not keyword_set(flx_nam) then flx_nam = "ENA/(cm!U2!N s sr keV)"
if not keyword_set(desc)    then desc    = "unknown model heliosphere"

openr,unit,file,/get_lun
a = 'a'
nhead=1
readf,unit,nhead
; print,'nhead=',nhead
for i=0, nhead-1 do begin
    readf,unit,a
end

nen = 1  & readf,unit,nen
dth = 1  & readf,unit,dth
dph = 1  & readf,unit,dph
nth = 30 & readf,unit,nth
nph = 60 & readf,unit,nph
readf,unit,a

v = 1.0
egrid = fltarr(nen)
for i=0,nen-1 do begin
    readf,unit,v
    egrid[i] = v
end

flx = fltarr(nth, nph)
flx[*,*] = 0.0

for i=0,nth-1 do begin
    for j=0,nph-1 do begin
        readf,unit,a
        for k=0,nen-1 do begin
            readf,unit,v
            if k eq ie then begin

                if not keyword_set(flx_log) $
                  then flx[nth-i-1,j]=v*flx_mul 
                
                if keyword_set(flx_log) and (v gt 0.0) then $
                  flx[nth-i-1,j] = $
                  alog10(v)*flx_mul
                
            end
        end
    end
end

close,unit

openw,unit,'out_flx_bin.txt',/get_lun

nlat = nth
nlon = nph
dx = floor(alog10(nlat))+1
dy = floor(alog10(nlon))+1
sx = stringer(nlat,dx)
sy = stringer(nlon,dy)
se = stringer(ie, 1)
printf, unit, "# 8:",sx,"x",sy,":",se,":outer_map"
printf, unit, "# energy = ",egrid[ie]
printf, unit, "# "

if not keyword_set(flx_max) then mx = max(flx) else mx = flx_max
if not keyword_set(flx_min) then mn = min(flx) else mn = flx_min
if (mx gt 0.0) then dx = floor(alog10(mx))+1 else dx = 1
if (mn gt 0.0) then dn = floor(alog10(mn))+1 else dn = 1

for i=0,nlat-1 do begin
    for j=0,nlon-1 do begin
        if (flx[i,j] gt mx) then flx[i,j]=mx
        if (flx[i,j] lt mn) then flx[i,j]=mn
    end
end

printf, unit, "# h_min=",stringer(mn,dn), " h_max=",$
  stringer(mx,dx)," h_title='",flx_nam,"'"
printf, unit, "# min_0=-90 max_0=90 num_0=",sx," title_0='Lat (deg)'"
printf, unit, "# min_1=0 max_1=360 num_1=",sy," title_1='Long (deg)'"
printf, unit, "# desc='",desc,"'"
printf, unit, "# "

for i=0,nlat-1 do begin
    for j=0, nlon-1 do begin
        printf, unit, format='(f15.4,$)',flx[i,j]
    end
    printf, unit, format='(%"\n",$)'
end

close, unit

return
end
