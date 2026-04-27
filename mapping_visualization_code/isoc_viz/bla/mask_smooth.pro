pro mask_smooth,y,sigy,mask,phi,theta,dang,smap
; smooth values of y(phi,theta) with uncertainty sigy(phi,theta)
; inside the masked region
;
; INPUTS
;   y[nph,nth]    - data to be fit
;   sigy[nph,nth] - uncertainty in y
;   mask[nph,nth] - mask for y: set to 1 where data is to be used, 0 to exclude
;   phi[nph]      - azimuthal angle grid .. in rad
;   theta[nth]    - polar angle grid .. in rad
;   dang in rad   - exp(-ang/dang) for weighting
; OUTPUTS
;  smap - structure with smoothin results
; Author
;   Schwadrion 3/10
; HISTORY
;;;;;;;;;;;;;;;;;;

nth=n_elements(theta)
nph=n_elements(phi)

phig=phi#(fltarr(nth)+1.)
thetag=(fltarr(nph)+1.)#theta

ii=where(mask eq 1)
if ii[0] lt 0 then begin
  print,'masked_smooth: no used points in mask'
  return
endif
nii=n_elements(ii)

smoot = y
smvar = (sigy)^2

yv=y[ii]
sigyv=sigy[ii]
phv=phig[ii]
thv=thetag[ii]

jj=where(mask eq 0)
njj=n_elements(jj)

ym=y[jj]
sigym=sigy[jj]
phm=phig[jj]
thm=thetag[jj]

for im=0,njj-1 do begin
; main loop over parts of map
    sum=0.0
    sumvar = 0.0
    sumwt=0.0

    vtheta = thm[im]
    vphi   = phm[im]
    x0 = sin(vtheta)*cos(vphi)
    y0 = sin(vtheta)*sin(vphi)
    z0 = cos(vtheta)
    for iv=0,nii-1 do begin
; now loop on the good grid
        vtheta = thv[iv]
        vphi = phv[iv]
        x1 = sin(vtheta)*cos(vphi)
        y1 = sin(vtheta)*sin(vphi)
        z1 = cos(vtheta)
        ang = acos(x1*x0+y1*y0+z1*z0)
        
        wt = (yv[iv]/(sigyv[iv]+1.0e-15) )^2
        earg = -1.0*ang/dang
        if (earg gt -50.0) then wt *= exp(earg) else wt = 0.0
        
        sum += yv[iv] * wt
        sumvar += sigyv[iv]^2 * wt
        sumwt += wt

    end
    smoot[jj[im]] = sum/(sumwt+1.0e-15)
    smvar[jj[im]] = sumvar/(sumwt+1.0e-15)
end

smap={fit:smoot,fitvar:smvar}

return
end





