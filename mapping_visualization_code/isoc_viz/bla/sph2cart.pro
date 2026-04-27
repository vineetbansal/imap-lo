pro sph2cart,spvec,cvec,radians=radians
;convert vectors specified in sperical coordinates to
;cartesian coordinates
;INPUTS
;  spvec - vector specified as [azimuthal angle,polar angle,radius],[3,n]
; OUTPUTS
;  cvec - cartsian vector
; angles specified in degrees unless /radians present

if not keyword_set(radians) then scale=!dtor else scale=1d

cvec=spvec
cvec[0,*]=spvec[2,*]*cos(scale*spvec[0,*])*sin(scale*spvec[1,*])
cvec[1,*]=spvec[2,*]*sin(scale*spvec[0,*])*sin(scale*spvec[1,*])
cvec[2,*]=spvec[2,*]*cos(scale*spvec[1,*])

return
end
