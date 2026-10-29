function dlegdtheta,theta,l,m,double=double
; Calculate derivative of P_lm(cos(theta)) with respect
; to theta. Based on algorithm by 
; Bosch, W., Phys. Chem. Earth, v25, No. 9-11, p655, 2000.
; test routine is in the comments below.
; IMPORTANT NOTES
;   1) This is different from the routine d2Legdx2 in this library
;      in that it is the derivative of Legendre function rather than
;      polynomial
;   2) This is ther derivative dP(cos(theta))/dtheta
;      NOT dP(x)/dx
;  INPUTS
;   l,m  -(scaler integers)  degree and order of legendre function
;         whose derivative is sought
;   theta - (array) angle in radians
;  Returns
;    dP(cos(theta))/dtheta
;  KEYWORDS
;    double - force double precision
;  History 
;    DeMajistre 3/2010
; ;;;;;;;;;;;;

if (abs(m) gt l) or (l le 0) then return,theta*0.

if m eq 0 then return,legendre(cos(theta),l,1,double=double)

term1=(m gt (-l))? (l+m)*(l-m+1d)*legendre(cos(theta),l,(m-1),double=double):0d
term2=(m lt l)?-legendre(cos(theta),l,(m+1),double=double):0d

return,-.5*(term1+term2)
; negative sign comes from (-1)^m in IDLs recurrence relation (noted in Bosch's paper).

end


function d2legdtheta2,theta,l,m,double=double
; Calculate second derivative of P_lm(cos(theta)) with respect
; to theta. Based on algorithm by 
; Bosch, W., Phys. Chem. Earth, v25, No. 9-11, p655, 2000.
; see the notes above for calling syntax
; ;;;;;;;;;;;;

if (abs(m) gt l) or (l le 0) then return,theta*0.

if m eq 0 then return,dlegdtheta(theta,l,1,double=double)
if m eq l then return,-l*dlegdtheta(theta,l,l-1,double=double)

; fooling with m limits is taken care of by the routine above.
term1=(l+m)*(l-m+1d)*dlegdtheta(theta,l,(m-1),double=double)
term2= -dlegdtheta(theta,l,(m+1),double=double)

return,-.5*(term1+term2)
; negative sign comes from (-1)^m in IDLs recurrence relation (noted in Bosch's paper).

end

; quick routine for testing the above routines
; Note that adif1 and adif2 get smaller as nth
; increases - strongly suggesting that errors in
; numerical derivative instead of the above routines
;
;pro test_legfunder,adif1,adif2,ll,mm,plot=plot,nth=nth
;
;if not keyword_set(nth)  then nth=180
;nl=10
;
;theta=dindgen(nth)*!pi/(nth-1.)
;
;if keyword_set(plot) then begin
;  psav=!p
;  !p.multi=[0,5,5]
;  str=''
;endif
;
;for l=0,nl do for m= -l,l do begin 
; Plm=legendre(cos(theta),l,m,/doub)
; dPlm0=deriv(theta,Plm)
; d2Plm0=deriv(theta,dPlm0)
; dPlm=dlegdtheta(theta,l,m,/doub)
; d2Plm=d2legdtheta2(theta,l,m,/doub)
; d1=total(abs(dplm0-dplm)/max(abs(dplm0)),/nan)/nth
; d2=total(abs(d2plm0-d2plm)/max(abs(d2plm0)),/nan)/nth
; if l eq 0 then begin
;   adif1=d1
;   adif2=d2
;   ll=0
;   mm=0
; endif else begin
;   adif1=[adif1,d1]
;   adif2=[adif2,d2]
;   ll=[ll,l]
;   mm=[mm,m]
; endelse
; if keyword_set(plot) then begin
;   plot,theta,dplm0, $
;      title='l='+string(l)+' m='+string(m),yr=max(abs([dplm0,d2plm0]))*[-1,1]
;   oplot,theta,d2plm0;,lin=2
;   oplot,theta,dplm,col=100
;   oplot,theta,d2plm,col=100;,lin=2
;   if !p.multi[0] eq 0 then read,str
; endif
;endfor
;if keyword_set(plot) then !p=psav
;return
;end
   

 
 
 





