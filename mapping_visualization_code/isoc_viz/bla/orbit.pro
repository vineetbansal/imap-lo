pro orbitCartoon,loa=loa

; loa is the longitude of apogee

if not keyword_set(loa) then loa=180.0+75.0

fallsol = (8.0*30.0+21.0)*365.25/360.0 ; Fall Solstice

dayofmag = fallsol + 365.25*loa/360.0

if dayofmag gt 365.25 then dayofmag -= 365.25

set_plot,'ps'
device, file = 'orbit.eps',/encaps, /color, xsize=20, ysize= 20

loadct, 38

!p.thick=2
!x.thick=2
!y.thick=2

plot,[-1.5,1.5],[-1.5,1.5], /nodata, xstyle=1+4, ystyle=1+4

loadct,0
makeShadeRegion,10,60,color=150
makeShadeRegion,255,290,color=150

loadct,38
makeCircle
makeSun, color=190

scale=0.1/10.0

makeMag, 0.0, color=70, scale=scale
makeOrbit, 0.0, color=230, scale=scale,dayofmag=dayofmag
makeEarth, 0.0

;doy=60.0
;makeMag, doy, color=70, scale=scale
;makeOrbit, doy, color=230, scale=scale
;makeEarth, doy


doy=91.5
makeMag, doy, color=70, scale=scale
makeOrbit, doy, color=230, scale=scale,dayofmag=dayofmag
makeEarth, doy

doy=183.
makeMag, doy, color=70, scale=scale
makeOrbit, doy, color=230, scale=scale,dayofmag=dayofmag
makeEarth, doy

;doy = 3.0*91.5-4.0 + 45.0
;makeMag, doy, color=70, scale=scale
;makeOrbit, doy, color=230, scale=scale
;makeEarth, doy
;makeLabel, 0.95, doy-7.,charsize=1.0, label='Start Science', charthick=1.3

doy=183.0+91.5
makeMag, doy, color=70, scale=scale
makeOrbit, doy, color=230, scale=scale,dayofmag=dayofmag
makeEarth, doy

makeIntVector
makeMonths

device,/close

return
end

; =========

pro makeLabel, r,  doy, label=label, charsize=charsize, color=color, charthick=charthick

x = r * cos(2.0 * doy * !pi/ 365.25)
y = r * sin(2.0 *doy * !pi/ 365.25)

xyouts, x, y, label, charsize=charsize, charthick=charthick

return
end

; =========

pro makeCircle, color=color

N = 500
r = 1.0
phi = 2.0*!pi*findgen(N)/(N-1.0)
x = r * cos(phi)
y = r * sin(phi)

oplot, x, y, color=color

return
end

; =========

pro makeSun, color=color

N = 500
r = 0.03
phi = 2.0*!pi*findgen(N)/(N-1.0)
x = r * cos(phi)
y = r * sin(phi)

oplot, x, y, color=color, thick=40

return
end

; =========

pro makeEarth, doy, color=color

N = 500
r = 0.01
phi = 2.0*!pi*findgen(N)/(N-1.0)
r1 = 1.0


x = r1*cos(2.0* doy/365.25 *!pi) + r * cos(phi)
y = r1*sin(2.0* doy/365.25 *!pi) + r * sin(phi)

oplot, x, y, color=color, thick=10

return
end

; =======

function rmag, phi

; r = p/(1+ eps * cos(theta))
; rmin = p/(1.0+eps)
; rmax = p/(1.0-eps)
; x = rmin/rmax = (1-e)/(1+e)  => x + ex = 1-e => (1+x)e = 1-x 

rmax = 20.0
rmin = 10.0
x = rmin/rmax
e = (1.0-x)/(1.0+x)
p = rmin * ( 1.0 + e )

F = 15.0
T = 70.0

r = p/(1.0+e*cos(phi))

ph1 = phi
if ph1 gt !pi then ph1 -= (2.0*!pi )

r1=F/abs(sin(ph1))^0.8

; y = r sin(phi)
; dy/dphi = r cos(phi) + e sphi^2 p/(1+e cphi)^2
dydp = r * cos(ph1) + e*(sin(ph1))^2*p/(1.0+e*cos(ph1))^2

if (dydp lt 0.0) then   r = r1 $
else if (r gt r1 ) then r = r1

if (r gt T ) then r = T

return, r
end

; =========

pro makeMag, doy, color=color, scale=scale

if not keyword_set(scale) then scale = 0.05/10.0

N = 500
phi = 2.0*!pi*findgen(N)/(N-1.0)
x = phi
y = phi

r1 = 1.0
xp = r1*cos(2.0* doy/365.25* !pi)  
yp = r1*sin(2.0* doy/365.25 *!pi) 

for i=0, N-1 do begin
   phiH = phi[i]
   r = rmag(phiH)
   x1 = scale * r * cos(phiH)
   y1 = scale * r * sin(phiH)
   rot = !pi + 2.0*doy/365.25*!pi
   x[i] = xp + x1*cos(rot) - y1*sin(rot)
   y[i] = yp + x1*sin(rot) + y1*cos(rot)
end

oplot, x, y, color=color, thick=8
polyfill,x, y, color=color
; oplot, x, y, thick=3

return
end

; =========

function rorbit, theta

; r = p/(1+ eps * cos(theta))
; rmin = p/(1.0+eps)
; rmax = p/(1.0-eps)
; x = rmin/rmax = (1-e)/(1+e)  => x + ex = 1-e => (1+x)e = 1-x 

rmax = 50.0
rmin = 1.0+8000.0/6300.0
x = rmin/rmax
e = (1.0-x)/(1.0+x)
p = rmin * ( 1.0 + e )

r = p/(1.0+e*cos(theta))

return, r
end


; =======

pro makeOrbit, doy, color=color, scale=scale, dayofmag=dayofmag

if not keyword_set(scale) then scale = 0.05/10.0
if not keyword_set(dayofmag) then dayofmag = 180.0

N = 500
phi = 2.0*!pi*findgen(N)/(N-1.0)
x = phi
y = phi

r1 = 1.0
xp = r1*cos(2.0*doy/365.25* !pi)  
yp = r1*sin(2.0*doy/365.25 *!pi) 

rot = !pi + 2.0*dayofmag/365.25*!pi

for i=0, N-1 do begin
   phiH = phi[i]
   r = rorbit(phiH)
   x1 = scale * r * cos(phiH)
   y1 = scale * r * sin(phiH)
   x[i] = xp + x1*cos(rot) - y1*sin(rot)
   y[i] = yp + x1*sin(rot) + y1*cos(rot)
end

oplot, x, y, color=color, thick=8
polyfill,x, y, color=color
oplot, x, y, thick=4

return
end

; ======

pro makeIntVector, dayofint=dayofint, label=label, $
                   thick=thick, charsize=charsize, color=color, $
                   charthick=charthick

if not keyword_set(charsize) then charsize=1.5
if not keyword_set(charthick) then charthick=4
if not keyword_set(dayofint) then begin
   fallsol = (8.0*30.0+21.0)*365.25/360.0 ; Fall Solstice
   dayofint = fallsol + 365.25*75.0/360.0 - 0.5*365.25
end
if not keyword_set(label) then label='Int. Flow'

r1 = 1.8
x1 = r1 * cos(2.0*dayofint * !pi/365.25)
y1 = r1 * sin(2.0* dayofint * !pi/365.25)

r2 = 1.6
x2 = r2 * cos(2.0*dayofint * !pi/365.25)
y2 = r2 * sin(2.0*dayofint * !pi/365.25)

arrow,x1,y1,x2,y2,thick=12,hsize=300,/data,color=color
xyouts,x1+0.05,y1+0.05,label, charsize=charsize, charthick=charthick

return
end

; =======

pro makeTick, doy, ticksize=ticksize, label=label, thick=thick, $
              charsize=charsize, charthick=charthick

if not keyword_set(ticksize) then ticksize=0.1

r1 = 1. + ticksize/2.0
x1 = r1 * cos(2.0*doy * !pi/365.25)
y1 = r1 * sin(2.0* doy * !pi/365.25)

r2 = 1. - ticksize/2.0
x2 = r2 * cos(2.0*doy * !pi/365.25)
y2 = r2 * sin(2.0*doy * !pi/365.25)

oplot,[x1,x2],[y1,y2], thick=thick
if keyword_set(label) then $
   xyouts,x1+0.15,y1-0.2,label, charsize=charsize,charthick=charthick

return
end

; ======

pro makeMonths

makeTick, 0.0, ticksize=0.15, thick=3.5, label='Jan. 1', charsize=1.4, $
          charthick=6
makeTick, 91.5, ticksize=0.15, thick=3.5, label='Apr. 1', charsize=1.4, $
          charthick=6
makeTick, 183., ticksize=0.15, thick=3.5, label='Jul. 1', charsize=1.4, $
          charthick=6
makeTick, 183.+91.5, ticksize=0.15, thick=3.5, label='Oct. 1', charsize=1.4, $
          charthick=6

for i=0,11 do begin
   doy = i*30.5
   if ((i mod 3) eq 0) then makeTick, doy, ticksize=0.15, thick=4 $
                       else $
                            makeTick, doy, ticksize=0.08, thick=4
end

return
end

; ======

pro makeShadeRegion, day0, day1, color=color

N = 100
r = 1.0

day0 = day0 * 2.0*!pi/365.25
day1 = day1 * 2.0*!pi/365.25

phi = day0 + (day1-day0)*findgen(N)/(N-1.0)
x = r * cos(phi)
y = r * sin(phi)
x=[0,x,0]
y=[0,y,0]

polyfill, x, y, color=color
oplot,x,y,thick=1.3

return
end

; =========
