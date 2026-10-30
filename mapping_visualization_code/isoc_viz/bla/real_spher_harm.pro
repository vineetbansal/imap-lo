function real_spher_harm,theta,phi,l,m,double=double,dtheta=dtheta,dphi=dphi
; Implements properly real domain sperical harmonics
; as described by 
; Blanco, Florez and Bermejo, Journal of Molecular Structure 
; (Theochem) 419 (1997) 19 – 27. 
; and summarized by Simon Brown at
; http://www.sjbrown.co.uk/2004/10/16/spherical-harmonic-basis/
; 
; This routine has the same calling sequence as IDLs SPHERE_HARM,
; but it's return is real instead of complex and does not use double
; keyword (results are always double).
; 
; In addition, first and second derivatives WRT theta and phi can be 
; calculated with dtheta and dphi keywords (provided the function DLEGDTHETA
; is available in the callers scope) 
; 
; INPUTS
;   theta - polar angle (radians)
;   phi - azimuthal angle (radians)
;   l,m - indices of desired harmonic
;       <theta and phi can be scalars or arrays, l and m should be scalar integers>
; KEYWORDS
;   dtheta - recognizes the following values
;           0 - calculate spherical harmonics as usual
;           1 - calculate derivative WRT theta
;           2 - calculate second derivative WRT theta
;   dphi - recognizes the following values
;           0 - calculate spherical harmonics as usual
;           1 - calculate derivative WRT phi
;           2 - calculate second derivative WRT phi
;           
; Returns
;   Real spherical harmonic
;   
; Author
;   DeMajistre (with error handling code from IDL library routine SPHERE_HARM)
; HISTORY
;   3/26/2010 - added derivative calculations (RD)
;;;;;;;;;;;;;;;;;
if not keyword_set(dtheta) then dtheta=0
if dtheta lt 0 or dtheta gt 2 then dtheta=0
if not keyword_set(dphi) then dphi=0
if dphi lt 0 or dphi gt 2 then dphi=0

; THIS STUFF TAKEN FROM LIBRARY ROUTINE
; error checking
        ON_ERROR, 2
        IF (N_PARAMS() NE 4) THEN MESSAGE, 'Incorrect number of arguments.'
        IF ((N_ELEMENTS(L) NE 1) OR (N_ELEMENTS(M) NE 1)) THEN $
                MESSAGE,'L and M must be scalars.'
        LL = LONG(L[0]) ; convert 1-element array to scalar
        M1 = LONG(M[0]) ; convert 1-element array to scalar
        IF (L LT 0) THEN MESSAGE, $
                'Argument L must be greater than or equal to zero.'

        MM = ABS(M1)
        IF (MM GT L) THEN MESSAGE, 'Argument M must be in the range [-L, L].'

        IF (SIZE(theta,/N_DIM) GT 0) AND (SIZE(phi,/N_DIM) GT 0) THEN $
                IF (N_ELEMENTS(theta) NE N_ELEMENTS(phi)) THEN MESSAGE, $
                'Theta or Phi must be scalar, or have the same number of values.'

case dtheta of
   0: P=legendre(cos(theta),LL,mm,/double)
   1: P=dlegdtheta(theta,LL,mm,/double)
   2: P=d2legdtheta2(theta,LL,mm,/double)
endcase

bigtheta=sqrt(((2d*l+1d)/(4.*!dpi)) *(factorial(l-mm)/factorial(l+mm)))*p

bigphi=(phi*0d)+1d  ;steal the structure of phi

if m1 gt 0 then bigphi=sqrt(2d)*cos(m1*phi)
if m1 lt 0 then bigphi=sqrt(2d)*sin(mm*phi)

if dphi gt 0 then $
   if dphi eq 1 then begin
       if m1 gt 0 then bigphi= -m1*sqrt(2d)*sin(m1*phi)
       if m1 lt 0 then bigphi=  mm*sqrt(2d)*cos(mm*phi)
   endif else bigphi= -bigphi*m1^2

return,bigtheta*bigphi
end

;;;;;;;;;;;;;;;;;;;;;;;;;
;; the following code fragment can be used to test this routine
;theta0=findgen(180)*!dtor
;phi0=findgen(360)*!dtor
;
;phi=phi0#(1.+fltarr(180))
;theta=(1.+fltarr(360))#theta0
;
;
;;;work with assocaiated legedre functions
;l= 5
;m= -4
;
;Y=real_spher_harm(theta,phi,l,m)
;dYdT=real_spher_harm(theta,phi,l,m,dtheta=1)
;d2YdT2=real_spher_harm(theta,phi,l,m,dtheta=2)
;dYdP=real_spher_harm(theta,phi,l,m,dphi=1)
;d2YdP2=real_spher_harm(theta,phi,l,m,dphi=2);
;
;dydT0=dydt
;d2YdT20=dydt
;for ic=0,n_elements(phi0)-1 do dydt0[ic,*]=deriv(theta0,Y[ic,*])
;for ic=0,n_elements(phi0)-1 do d2ydt20[ic,*]=deriv(theta0,dydt0[ic,*])
;dydP0=dydt
;d2YdP20=dydt
;for ic=0,n_elements(theta0)-1 do dydP0[*,ic]=deriv(phi0,Y[*,ic])
;for ic=0,n_elements(theta0)-1 do d2ydP20[*,ic]=deriv(phi0,dydP0[*,ic])
;
;color_plot,(dydt-dydt0)/max(dydt0)
;color_plot,(d2ydt2-d2ydt20)/max(d2ydt20)
;color_plot,(d2ydp2-d2ydp20)/max(d2ydp20)
;color_plot,(dydp-dydp0)/max(dydp0)
;;;;;;;;;;;;;;;




