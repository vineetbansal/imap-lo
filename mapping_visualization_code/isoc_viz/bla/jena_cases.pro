pro setup,icase
common alpha, chi, gamma,beta,n0,sigma,r1,m, u,RTS, uTS, L

case icase of
    1: begin                    ; nose strong shock
        chi = 0.2
        u = 450.0d5
        RTS = 100.0
        n0 = 0.08
        uTS = 0.0
        L = 30.0 
    end
    2: begin                    ; nose weak shock
        chi = 0.2
        u = 450.0d5
        RTS = 100.0
        n0 = 0.08
        uTS = 0.0
        L = 30.0
    end
    3: begin                    ; tail strong shock
        chi = 0.2
        u = 450.0d5
        RTS = 175.0
        n0 = 0.05
        uTS = 20.0d5
        L = 30.0
    end
    4: begin                    ; tail weak shock
        chi = 0.2
        u = 450.0d5
        RTS = 175.0
        n0 = 0.05
        uTS = 100.0d5
        L = 30.0
    end
    5: begin                    ; polar region strong shock
        chi = 0.05
        u = 750.0d5
        RTS = 150.0
        n0 = 0.07
        uTS = 10.0d5
        L = 30.0
    end
    6: begin                    ; polar region weak shock
        chi = 0.05
        u = 750.0d5
        RTS = 150.0
        n0 = 0.07
        uTS = 50.0d5
        L = 30.0
    end
endcase
gamma = 6.75
beta = 1.5d-7
r1 = 1.5e13
sigma = 1.5d-15
m = 1.6d-24
end

; ======

function jCIR, E
; Applies for inside the heliosphere
; E in keV

common alpha, chi, gamma,beta,n0,sigma,r1,m, u, RTS, uTS, L

Rmax = RTS
Rmin = 4.0
uE = u
En = 1000*E*1.6e-12
vp = sqrt(2*En/m)
w = abs(uE + vp)/u
if (w lt 1.0) then H = 0.0 else H = chi*w^(-gamma) 
j = 3.0d0/(4.0*3.14159)*beta*n0^2*sigma*(r1/u^2)^2*(En/m^2)* $
  alog(Rmax/Rmin)*w^(-1.5)*H
j = j * (1.6e-12*1000)
if j lt 0.0 then j = 0.0
return, j
end

; ======

function jTS, E
; Applies for outside the heliosphere
; E in keV

common alpha, chi, gamma,beta,n0,sigma,r1,m, u, RTS, uTS, L

Rmax = RTS
uE = uTS
En = 1000*E*1.6e-12
vp = sqrt(2.0*En/m)
w = abs(uE + vp)/u
if (w lt 1.0) then H = 1.0 else H = chi*w^(-gamma) 
j = 3.0d0/(4.0*3.14159)*beta*n0^2*sigma*(r1/u^2)^2*(En/m^2)* $
  L/Rmax*w^(-1.5)*H
j = j * (1.6e-12*1000)
if j lt 0.0 then j = 0.0
return, j
end

; =====

function jSeg, E, Rmax, Rmin, uE, uin
; Applies for inside the heliosphere
; E in keV

common alpha, chi, gamma,beta,n0,sigma,r1,m, u, RTS, uTS, L

En = 1000*E*1.6e-12
vp = sqrt(2*En/m)
w = abs(uE + vp)/u
if (w lt 1) then H = 1.0 else H = chi*w^(-gamma) 
j = 3.0d0/(4.0*3.14159)*beta*n0^2*sigma*(r1/uin^2)^2*(En/m^2)* $
  alog(Rmax/Rmin)*w^(-1.5)*H
j = j * (1.6e-12*1000)
if j lt 0.0 then j = 0.0
return, j
end
