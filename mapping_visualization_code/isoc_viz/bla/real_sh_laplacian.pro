function real_sh_laplacian,theta,phi,l,m,double=double
; calculate laplacian (angular component) of a given spherical harmonic
; INPUTS
;   theta - polar angle (radians)
;   phi - azimuthal angle (radians)
;   l,m - indices of desired harmonic
;       <theta and phi can be scalars or arrays, l and m should be scalar integers>
; RETURNS
;   angular laplacian of the given spherical harmonic  
;;;;;;;;;;;;;;;;;

DYdT=real_spher_harm(theta,phi,l,m,double=double,dtheta=1)
D2YDT2=real_spher_harm(theta,phi,l,m,double=double,dtheta=2)
D2YDP2=real_spher_harm(theta,phi,l,m,double=double,dphi=2)
sth=sin(theta)
cth=cos(theta)

return,(cth*DYDT+sth*D2YDT2)/sth+D2YDP2/(sth^2)
end
