pro usersym_circle,size=size

if not keyword_set(size) then size=1.0 
; for use with ips.psym=8
; Make a vector of 16 points, A[i] = 2pi/16:  
a = findgen(17) * (!PI*2/16.)  
; Define the symbol to be a unit circle with 16 points,   
; and set the filled flag:  
usersym, size*cos(a), size*sin(a), /fill 

return
end

;  make me an up triangle (filled or not)

pro usersym_triangle_up,size=size,fill=fill,thick=thick

if not keyword_set(size) then size=0.3
if not keyword_set(thick) then thick=6

X=[0,-4,4,0,0]*size
Y=([6,0,0,6,6]-3)*size

if not keyword_set(fill) then $
  USERSYM,X,Y,thick=thick $
else $
  USERSYM,X,Y,/fill

return
end

;  make me a down triangle (filled or not)

pro usersym_triangle_dn,size=size,fill=fill,thick=thick

if not keyword_set(size) then size=0.3
if not keyword_set(thick) then thick=6

X=[0,-4,4,0,0]*size
Y=([-6,0,0,-6,-6]+3)*size

if not keyword_set(fill) then $
  USERSYM,X,Y,thick=thick $
else $
  USERSYM,X,Y,/fill

return
end




