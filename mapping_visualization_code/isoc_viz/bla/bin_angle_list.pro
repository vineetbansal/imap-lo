;
; $Id: 
;
; nas 9/16/08
; 
; pro bin_angle_list
;
; This procedure produces reads a list of angles and bins them into maps
;
; 

pro bin_angle_list,           $
           datafile   ,       $          ; IN filename (refresh file)
           nlat   ,           $          ; IN number of lat bins
           nlon   ,           $          ; IN number of lon bins
           average=average,   $          ; IN average instead of accumulate         
           missing_value=missing_value   ; IN : keyword equal to a value used for
                                         ;      missing values
 
if (not keyword_set(title)) then title='title'

get_variable_header_size,datafile,ds,nvars
data=read_ascii(datafile,delimiter=' ',header=hdr,data_start=ds, $
                       missing_value=missing_value)
df=read_ascii_data_array(datafile,' ',ds,data)
parse_variable_header,hdr,ds,nvars,titles,desc,title=title

nrows = n_elements(df[0,*])

maps = fltarr(nvars-2, nlat, nlon)
amap = fltarr(nlat,nlon)
nnn = lonarr(nlat, nlon)

maps[*,*,*] = 0.
nnn[*,*] = 0

rs = fltarr(nvars)

for i=0l,nrows-1 do begin
    rs = df[*,i]
    for j=2,nvars-1 do begin
        if (rs[j] lt 0.0) then rs[j] = 0.0
    end
    colat = rs[0]
    lon = rs[1]
    if (lon lt 0.0) then lon += 360.0
                
    ix = nlat - 1 -  floor((nlat-1)*colat/180.0 + 0.5) 
    iy = floor(nlon*lon/360.0 + 0.5)
    if (iy eq nlon) then iy = 0
    
    maps[*,ix,iy] = maps[*,ix,iy] + rs[2:(nvars-1)]

    nnn[ix, iy] = nnn[ix, iy] + 1
end                             ; end while file open

if keyword_set(average) then begin
    for i=0,nlat-1 do begin
        for j=0,nlon-1 do begin
            if (nnn[i,j] gt 0) then $
              maps[*,i,j] /= (1.0*nnn[i,j])
        end
    end
end

for i=0,nvars-3 do begin 
    openw,unit,'map_var'+string(i,format='(i0)')+'_bin.txt',/get_lun

    dx = floor(alog10(nlat))+1
    dy = floor(alog10(nlon))+1
    sx = stringer(nlat,dx)
    sy = stringer(nlon,dy)
    printf, unit, "# 8:",sx,"x",sy
    printf, unit, "# "
    printf, unit, "# "

    amap[*,*] = maps[i,*,*]

    mn = min(amap)
    mx = max(amap)
    if (mx gt 0.0) then dx = floor(alog10(mx))+1 else dx = 1
    if (mn gt 0.0) then dn = floor(alog10(mn))+1 else dn = 1

    printf, unit, "# h_min=",stringer(mn,dn), " h_max=",$
      stringer(mx,dx)," h_title='",titles[i+2],"'"
    printf, unit, "# min_0=-90 max_0=90 num_0=",sx," title_0='Lat (deg)'"
    printf, unit, "# min_1=0 max_1=360 num_1=",sy," title_1='Long (deg)'"
    printf, unit, "# desc='",desc,"'"
    printf, unit, "# "

    
    for j=0,nlat-1 do begin
        for k=0, nlon-1 do begin
            printf, unit, format='(f15.4,$)',maps[i,j,k]
        end
        printf, unit, format='(%"\n",$)'
    end

    close, unit
end

return
end
