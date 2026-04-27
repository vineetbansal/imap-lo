pro smooth_mask,y,sigy,mask,phi,theta
; 
; go to places where mask = 0 and smooth with nearest neighbors.
; where there is data. Also smooth the uncertainty
; 
;   y[nph,nth] - data to be fit
;   sigy[nph,nth] - uncertainty in y
;   mask[nph,nth] - mask for y: set to 1 where data is to be used, 0 to exclude
;   phi[nph] - azimuthal angle grid
;   theta[nth] - polar angle grid
;
; Author
;   schwadron 11/09
; HISTORY
;;;;;;;;;;;;;;;;;;

nth=n_elements(theta)
nph=n_elements(phi)

for i=0,nth-1 do begin
for j=0,nph-1 do begin

    if (mask[i,j] eq 0) then begin
        sumy=0.0
        sumsig = 0.0
        nsum = 0
        for ii = -1,1 do begin
            for jj = -1,1 do begin
                in = i+ii & jn = j+jj
                
                if ((ii ne 0) or (jj ne 0)) then begin
                    
                    neighbor(in,jn,nth,nph)
                    if (mask[in, jn] gt 0) then begin 
                        sumy += y[in,jn]
                        sumsig += (sigy[in,jn])^2
                        nsum += 1
                    end
                    
                end
            end
        end
    
        if (nsum gt 0) then begin
            mask[i,j] = 1
            y[i,j] = sumy/nsum
            sigy[i,j] = sqrt(sumsig/nsum)
        end
   
end
end

return
end


;
; lim center     (i,j)
;     neighbor  (in,jn)
;     number of cells (nth,nph)
;      
; find cell neighbors using loopback
; i < 0 ==> in = nth-1, j = j+ pi/2
; i > nth-1 ==> similar criterion
pro neighbor(in,jn,nth,nph)

if (in lt 0) then begin
    in = 0 
    jn = jn + nph/2
end

if (in gt nth-1) then begin
    in = nth-1
    jn = jn + nph/2
end


if (jn gt nph-1) then begin
 jn = jn - nph
end

if (jn lt 0) then begin
 jn = jn + nph
end

return
end




ncoef=(nl+1)^2

phig=phi#(fltarr(nth)+1.)
thetag=(fltarr(nph)+1.)#theta
ii=where(mask eq 1)
if ii[0] lt 0 then begin
  print,'masked_sh_fit: no used points in mask'
  return
endif
nii=n_elements(ii)

;values input into fitting routine
yv=y[ii]
sigyv=sigy[ii]
phv=phig[ii]
thv=thetag[ii]
shfitfun_setup,thv,phv,nl,l,m
; set up normal equations
Amat=dblarr(nii,ncoef)
Amatfull=dblarr(n_elements(y),ncoef)
for ic=0,ncoef-1 do Amat[*,ic]=real_spher_harm(thv,phv,l[ic],m[ic])
for ic=0,ncoef-1 do  $
  Amatfull[*,ic]=real_spher_harm(reform(thetag,nth*nph),reform(phig,nth*nph),l[ic],m[ic])


;SVDFIT stuff
x=indgen(n_elements(ii)) ;fool svdfit into 2 dimensional fit
afit=svdfit(x,yv,n_elements(l),chisq=chisq,func='shfitfun', $
   measure=sigyv,sigma=sigma,SING_VALUES=sing_values, SINGULAR=singular, $
   STATUS=status,VARIANCE=variance, YFIT=yfit)

rchisq=chisq/float(nii-ncoef)
fity=y*0.
fity[ii]=yfit

fityfull=reform(amatfull#afit,nph,nth)

shfit={y:y,sigy:sigy,mask:mask,phi:phi,theta:theta,nl:nl, $
       afit:afit,asig:sigma,rchisq:rchisq,fity:fity,fityfull:fityfull, $
       status:status}

return
end





