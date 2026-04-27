pro rangemask,lon,lat,ranges,rmask
; builds simple geometric mask
;INPUTS
;  lon[nlon] - longitude grid for mask - MUST BE IN RANGE -180 to 180
;  lat[nlat] - latitude grid for mask
;  ranges[4,nrange] - corners of geographic ranges to mask off. Each corner set 
;                     in the order [min_lon,min_lat,max_lon,max_lat]
;                     e.g., to mask off 0-50 deg longitude and -10 to 10 deg latitude
;                     and 70-80 longitude and 20-30 latitude, use
;                     ranges=[[0.,-10.,50.,10.],[70.,20.,80.,30.]]
;                     NOTE- MUST BE SPECIFIED -180 to 180
;OUTPUTS
;  rmask - mask returned, set to 1 where outside of ranges, 0 on the inside
;
; bookkeeping

nlon=n_elements(lon)
nlat=n_elements(lat)
nr=n_elements(ranges[0,*])

rmask=intarr(nlon,nlat)+1
longr=lon#(fltarr(nlat)+1.)
latgr=(fltarr(nlon)+1.)#lat

for ic=0,nr-1 do begin
   ii=where(longr ge ranges[0,ic] and longr le ranges[2,ic] and $
               latgr ge ranges[1,ic] and latgr le ranges[3,ic]) 
   if ii[0] ge 0 then rmask[ii]=0.
endfor

return
end

