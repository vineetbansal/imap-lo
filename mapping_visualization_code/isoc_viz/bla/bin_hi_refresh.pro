;
; $Id: 
;
; nas 9/2/08
; 
; pro bin_hi_refresh
;
; This procedure produces the datafiles in bin format
;
; Needs stringer.pro compiled
; 
pro bin_hi_refresh,           $
           ie     ,           $ ; IN energy step
           file   ,           $ ; IN filename (refresh file)
           nlat   ,           $ ; IN number of lat bins
           nlon   ,           $ ; IN number of lon bins
           nrefresh=nrefresh, $ ;OPT_IN max number of refresh cycles to load
           flx_mul = flx_mul, $ ;OPT_IN flx multiplier                         
           dbl_mul = dbl_mul, $ ;OPT_IN dbl multiplier                       
           trp_mul = trp_mul, $ ;OPT_IN trp multiplier 
           flx_log = flx_log, $ ;OPT_IN set keyword to use log scale [base10]
           dbl_log = dbl_log, $ ;OPT_IN set keyword to use log scale [base10]
           trp_log = trp_log, $ ;OPT_IN set keyword to use log scale [base10]
           flx_nam = flx_nam, $ ;OPT_IN flx name                         
           dbl_nam = dbl_nam, $ ;OPT_IN dbl name
           trp_nam = trp_nam, $ ;OPT_IN trp name
           flx_min = flx_min, $ ;OPT_IN flx min
           flx_max = flx_max, $ ;OPT_IN flx max
           dbl_min = dbl_min, $ ;OPT_IN dbl min
           dbl_max = dbl_max, $ ;OPT_IN dbl max
           trp_min = trp_min, $ ;OPT_IN trp min
           trp_max = trp_max, $ ;OPT_IN trp max
           desc    = desc      ;OPT_IN description

day = 24*60*60
if not keyword_set(flx_mul) then flx_mul = 1.0
if not keyword_set(flx_nam) then flx_nam = "ENA/(cm!U2!N s sr keV)"
if not keyword_set(dbl_mul) then dbl_mul = day
if not keyword_set(dbl_nam) then dbl_nam = "dbls/day"
if not keyword_set(trp_mul) then trp_mul = day
if not keyword_set(trp_nam) then trp_nam = "trps/day"
if not keyword_set(desc)    then desc    = "unknown model heliosphere"
if not keyword_set(nrefresh) then nrefresh = 1000000000l

flx = fltarr(nlat, nlon)
dbl = fltarr(nlat, nlon)
trp = fltarr(nlat, nlon)
nnn = lonarr(nlat, nlon)

flx[*,*] = 0.
dbl[*,*] = 0.
trp[*,*] = 0.
nnn[*,*] = 0

openr,unit,file,/get_lun

i0 = 1
i1 = 1
rs = fltarr(9)

a = 'a'
readf,unit,a
readf,unit,a

nref_read = 0

while not eof(unit) do begin
    readf,unit,a
    
    if nref_read ge nrefresh then goto, escape1

    for j=0,5 do begin
        for i=0,59 do begin

            readf,unit,i0,rs,i1

            if (rs[6] lt 0.0) then rs[6] = 0.0
            if (rs[7] lt 0.0) then rs[7] = 0.0
            if (rs[8] lt 0.0) then rs[8] = 0.0

            if (i0 eq ie) then begin

                colat = rs[4]*180.0/!pi
                lon = rs[5]*180.0/!pi
                if (lon lt 0.0) then lon = lon + 360.0
                
                ix = nlat - 1 -  floor((nlat-1)*colat/180.0 + 0.5) 
                iy = floor(nlon*lon/360.0 + 0.5)
                if (iy eq nlon) then iy = 0
;                print, ix, iy



                if not keyword_set(flx_log) $
                  then flx[ix, iy] = flx[ix, iy] $
                  + rs[6]*flx_mul $ 
                else begin
                    if (rs[6] gt 0.0) then  $
                      flx[ix, iy] = flx[ix, iy] + $
                      rs[6]*flx_mul 
                end

                if not keyword_set(dbl_log) $
                  then dbl[ix, iy] = dbl[ix, iy] + $
                  rs[7]*dbl_mul  $
                else begin
                    if (rs[7] gt 0.0) then  $
                      dbl[ix, iy] = dbl[ix, iy] + $
                      alog10(rs[7])*dbl_mul 
                end

                if not keyword_set(trp_log) $
                  then trp[ix, iy] = trp[ix, iy] + $
                  rs[8]*trp_mul  $
                else begin
                    if (rs[8] gt 0.0) then  trp[ix, iy] = $
                      trp[ix, iy] + alog10(rs[8])*trp_mul 
                end

                nnn[ix, iy] = nnn[ix, iy] + 1
            end                 ; end if for i0 = ie
        end                     ; end i=0, 59
    end                         ; end j=0, 5    

    nref_read++

end                             ; end while file open

escape1:

close,unit

for i=0,nlat-1 do begin
    for j=0,nlon-1 do begin
        if (nnn[i,j] gt 0) then begin
            flx[i,j] = flx[i,j]/nnn[i,j]
            dbl[i,j] = dbl[i,j]/nnn[i,j]
            trp[i,j] = trp[i,j]/nnn[i,j]
        end
    end
end

openw,unit,'flx_bin.txt',/get_lun

dx = floor(alog10(nlat))+1
dy = floor(alog10(nlon))+1
sx = stringer(nlat,dx)
sy = stringer(nlon,dy)
se = stringer(ie, 1)
printf, unit, "# 8:",sx,"x",sy,":",se,":Hi"
printf, unit, "# "
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

; == dbls

openw,unit,'dbl_bin.txt',/get_lun

printf, unit, "# 8:",sx,"x",sy,":",se,":Hi"
printf, unit, "# "
printf, unit, "# "

if not keyword_set(dbl_max) then mx = max(dbl) else mx = dbl_max
if not keyword_set(dbl_min) then mn = min(dbl) else mn = dbl_min
if (mx gt 0.0) then dx = floor(alog10(mx))+1 else dx = 1
if (mn gt 0.0) then dn = floor(alog10(mn))+1 else dn = 1

for i=0,nlat-1 do begin
    for j=0,nlon-1 do begin
        if (dbl[i,j] gt mx) then dbl[i,j]=mx
        if (dbl[i,j] lt mn) then dbl[i,j]=mn
    end
end

printf, unit, "# h_min=",stringer(mn,dn), " h_max=",$
  stringer(mx,dx)," h_title='",dbl_nam,"'"
printf, unit, "# min_0=-90 max_0=90 num_0=",sx," title_0='Lat (deg)'"
printf, unit, "# min_1=0 max_1=360 num_1=",sy," title_1='Long (deg)'"
printf, unit, "# desc='",desc,"'"
printf, unit, "# "

for i=0,nlat-1 do begin
    for j=0, nlon-1 do begin
        printf, unit, format='(f15.4,$)',dbl[i,j]
    end
    printf, unit, format='(%"\n",$)'
end

close, unit

; == triples

openw,unit,'trp_bin.txt',/get_lun

printf, unit, "# 8:",sx,"x",sy,":",se,":Hi"
printf, unit, "# "
printf, unit, "# "

if not keyword_set(trp_max) then mx = max(trp) else mx = trp_max
if not keyword_set(trp_min) then mn = min(trp) else mn = trp_min
if (mx gt 0.0) then dx = floor(alog10(mx))+1 else dx = 1
if (mn gt 0.0) then dn = floor(alog10(mn))+1 else dn = 1

for i=0,nlat-1 do begin
    for j=0,nlon-1 do begin
        if (trp[i,j] gt mx) then trp[i,j]=mx
        if (trp[i,j] lt mn) then trp[i,j]=mn
    end
end

printf, unit, "# h_min=",stringer(mn,dn), " h_max=",$
  stringer(mx,dx)," h_title='",trp_nam,"'"
printf, unit, "# min_0=-90 max_0=90 num_0=",sx," title_0='Lat (deg)'"
printf, unit, "# min_1=0 max_1=360 num_1=",sy," title_1='Long (deg)'"
printf, unit, "# desc='",desc,"'"
printf, unit, "# "

for i=0,nlat-1 do begin
    for j=0, nlon-1 do begin
        printf, unit, format='(f15.4,$)',trp[i,j]
    end
    printf, unit, format='(%"\n",$)'
end

close, unit

return
end
