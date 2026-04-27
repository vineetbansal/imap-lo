pro nn_ra,y,mask,phi,theta,max_ang,y_nabr,fill=fill
; fill nearest neighbor values in ra of map y(phi,theta) with mask
; mask(phi,theta). Go to a given pixel. If mask = 0 then reach left and
; right in RA until you find a neighbor. The first closest neighbor
; gets is used for the pixel.
;
; INPUTS
;   y[nph,nth]    - map to be filled
;   mask[nph,nth]  - mask for y
;   phi[nph]      - azimuthal angle grid .. in rad
;   theta[nth]    - polar angle grid .. in rad
;   max_ang       - max fill angle  in rad
; OPTIONAL ARGS
;   fill          - flux to fill any holes
; OUTPUTS
;  y_nabr[nph,nth]
; Author
;   Schwadron 3/10
; HISTORY
;;;;;;;;;;;;;;;;;;

if not keyword_set(fill) then fill=0.0

nth=n_elements(theta)
nph=n_elements(phi)

phig=phi#(dblarr(nth)+1.)
thetag=(dblarr(nph)+1.)#theta

ii=where(mask eq 1)
if ii[0] lt 0 then begin
  print,'nn_ra: no used points in mask'
  return
endif
nii=n_elements(ii)

y_nabr = y

yv=y[ii]
phv=phig[ii]
thv=thetag[ii]

jj=where(mask eq 0)
njj=n_elements(jj)

y_nabr[jj]=fill

ym=y[jj]
phm=phig[jj]
thm=thetag[jj]

for im=0l,njj-1 do begin
; main loop over parts of map that are masked
    th   = thm[im]
    ph   = phm[im]

    x0 = cos(ph)
    y0 = sin(ph)

    ii_nn = where(thv eq th) 
    n_nn = n_elements(ii_nn)
    
    y_nn=yv[ii_nn]
    ph_nn=phv[ii_nn]
    th_nn=thv[ii_nn]

;    print, ph_nn/!dtor
;    print, th_nn/!dtor

    min_ang=1000.0
    set=0
    
    for in=0l,n_nn-1 do begin
; now loop on the potential neighbors otside the mask at one lat
        thn = th_nn[in]
        phn   = ph_nn[in]

        xn = cos(phn)
        yn = sin(phn)

        ang = acos(xn*x0+yn*y0)

        if ((ang le min_ang) and (ang le max_ang)) then begin
            inab = in
            min_ang = ang
            set = 1
        end
    end

    if (set eq 1) then y_nabr[jj[im]] = y_nn[inab]
end

return
end





