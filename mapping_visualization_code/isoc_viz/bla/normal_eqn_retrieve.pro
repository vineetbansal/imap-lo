pro normal_eqn_retrieve,kern,data,sigdat,gam,conmat,ret,datamask=datamask
; constrained linear least squares retrieval.
; assumes model data=kern#m
; sigdat are 1 sigma uncertainties in data
; conmat is the sqaure constraint matrix
; datamask is an array containing the indices of the data points to use
; Author - DeMajistre

nd=n_elements(kern[*,0])
nm=n_elements(kern[0,*])

if not keyword_set(datamask) then datamask=lindgen(nd)
;scale problem for uncertainties

g=kern[datamask,*]
for ic=0l,nm-1 do g[*,ic]=kern[datamask,ic]/sigdat[datamask]
d=data[datamask]/sigdat[datamask]

alpha=invert(transpose(g)#g+gam*conmat)
gi=alpha#transpose(g)
cov=alpha

fit=Gi#d
sigfit=sqrt(cov(where(identity(nm))))

datafit=kern[datamask,*]#fit
rchi2=total(((datafit-data[datamask])^2/sigdat[datamask]^2))/ $
    n_elements(datamask)

ret={fit:fit,cov:cov,sigfit:sigfit,datafit:datafit,rchi2:rchi2,g:g, $
     Gi:gi,alpha:alpha,d:d,data:data,kern:kern,sigdat:sigdat, $
    gam:gam,conmat:conmat, $
    datamask:datamask}
return
end


