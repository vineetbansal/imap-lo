pro linemask,glon,glat,linlon,linlat,dang, mask
; build a mask for the grid defined by glon and glat,
; where the mask is set to zero a given angular distance from
; a locus of points
; INPUTS
;    glon[nlon] - longitude grid (deg)
;    glat[nlat] - latitude grid (deg)
;    linlon[npt] - longitude of mask locus
;    linlat[npt] - latitude of mask locus
;    dang - angular distance for exclusion
; OUTPUTS
;    mask[nlon,nlat] - mask array set to 1 everywhere outside
;    the masked region, 0 inside
; AUTHOR
;  DeMajistre
; HISTORY
;
;;;;;;;;;;;;;;;;;;;;;;;

dangrad=dang*!dtor

nth=n_elements(glon)
nph=n_elements(glat)
nln=n_elements(linlon)

mask=fltarr(nth,nph)+1.

; build cartesian unit vectors for grid
thetag=(glon)#(fltarr(nph)+1.)
phig=(fltarr(nth)+1)#(90.-glat)
rg=fltarr(nth,nph)+1.
spvec=transpose([[reform(thetag,nth*nph)],[reform(phig,nth*nph)],[reform(rg,nth*nph)]])
sph2cart,spvec,cvecg

; cartesian vectors for mask locus
thetam=linlon
phim=90.-linlat
rm=fltarr(nln)+1.
spvec=transpose([[thetam],[phim],[rm]])
sph2cart,spvec,cvecm

; take care of starting point
dist0=acos(cvecm[*,0]#cvecg)
ii=where(dist0 le dangrad)
if ii[0] ge 0 then mask[ii]=0

;loop over sequential point pairs
; transform into system where X axis is first point and Z axis
; perp. to the point pair. mask points dang away from XY plane
; and between the point pair 

for ic=1,nln-1 do begin
   adist=acos(total(cvecm[*,ic-1]*cvecm[*,ic])) ;anglular distance between points
   Xax=cvecm[*,ic-1]
   Zax=crossp(Xax,cvecm[*,ic])
   Zax=Zax/sqrt(total(zax^2))
   Yax=crossp(Zax,Xax)
   Rmat=transpose([[Xax],[Yax],[Zax]])
   nuvecs=Rmat#cvecg
   nulat=!pi*.5-acos(nuvecs[2,*])
   nulon=atan(nuvecs[1,*],nuvecs[0,*])
   ii=where(abs(nulat) le dangrad and nulon ge 0 and nulon le adist)
   if ii[0] ge 0 then mask[ii]=0
   dist1=acos(cvecm[*,ic]#cvecg) ;the following takes care of sharp angles
   jj=where(dist1 le dangrad)
   if jj[0] ge 0 then mask[jj]=0
endfor

return
end
;
;  ..linemask2 ..
;
pro linemask2,glon,glat,linlon,linlat,dang, mask
; build a mask for the grid defined by glon and glat,
; where the mask is set to zero a given angular distance from
; a locus of points
; INPUTS
;    glon[nlon] - longitude grid (deg)
;    glat[nlat] - latitude grid (deg)
;    linlon[npt] - longitude of mask locus
;    linlat[npt] - latitude of mask locus
;    dang[npt]   - delta angle for exclusion in lon
; OUTPUTS
;    mask[nlon,nlat] - mask array set to 1 everywhere outside
;    the masked region, 0 inside
; AUTHOR
;  DeMajistre
; HISTORY
;
;;;;;;;;;;;;;;;;;;;;;;;

nth=n_elements(glon)
nph=n_elements(glat)
nln=n_elements(linlon)

dangrad=dang*!dtor

mask=fltarr(nth,nph)+1.

; build cartesian unit vectors for grid
thetag=(glon)#(fltarr(nph)+1.)
phig=(fltarr(nth)+1)#(90.-glat)
rg=fltarr(nth,nph)+1.
spvec=transpose([[reform(thetag,nth*nph)],[reform(phig,nth*nph)],[reform(rg,nth*nph)]])
sph2cart,spvec,cvecg

; cartesian vectors for mask locus
thetam=linlon
phim=90.-linlat
rm=fltarr(nln)+1.
spvec=transpose([[thetam],[phim],[rm]])
sph2cart,spvec,cvecm

; take care of starting point
dist0=acos(cvecm[*,0]#cvecg)
ii=where(dist0 le dangrad[0])
if ii[0] ge 0 then mask[ii]=0

;loop over sequential point pairs
; transform into system where X axis is first point and Z axis
; perp. to the point pair. mask points dang away from XY plane
; and between the point pair 

for ic=1,nln-1 do begin
   adist=acos(total(cvecm[*,ic-1]*cvecm[*,ic])) ;anglular distance between points
   Xax=cvecm[*,ic-1]
   Zax=crossp(Xax,cvecm[*,ic])
   Zax=Zax/sqrt(total(zax^2))
   Yax=crossp(Zax,Xax)
   Rmat=transpose([[Xax],[Yax],[Zax]])
   nuvecs=Rmat#cvecg
   nulat=!pi*.5-acos(nuvecs[2,*])
   nulon=atan(nuvecs[1,*],nuvecs[0,*])
   ii=where(abs(nulat) le dangrad and nulon ge 0 and nulon le adist)
   if ii[0] ge 0 then mask[ii]=0
   dist1=acos(cvecm[*,ic]#cvecg) ;the following takes care of sharp angles
   jj=where(dist1 le dangrad[ic])
   if jj[0] ge 0 then mask[jj]=0
endfor

return
end

