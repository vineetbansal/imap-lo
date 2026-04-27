; $Id: sweepmapper.pro 18282 2024-04-29 16:54:07Z ibexops $
;
; these routines are used to remap the good times files
; based on the SweepTable.


function get_stepmap,st,t0,t1
; extract the correct step mapping

ii=where(t0 ge st.t0 and t1 gt st.t0 and t0 le st.t1 and t1 le st.t1)
ii=ii[0]
if ii lt 0 then return,-1

return,st[ii].swmap
end

function step_remap,gtrec,stmap
;do the remap
rec=gtrec
outrec=gtrec*0+1 ;start by turning everything on
outmask=gtrec*0  ;to track the channels we've fooled with

for ic=0,n_elements(stmap)-1 do begin
  if stmap[ic] gt 0 then begin
    outrec[stmap[ic]-1]=(outrec[stmap[ic]-1] and gtrec[stmap[ic]-1])
    outmask[stmap[ic]-1]=1
  endif
endfor
rec=outrec and outmask
return,rec
end

pro set_sensor,snum,nc,sensor
; for convenience - set sensor characteristics 

case snum of
  0: begin
     nc=6
     sensor='Hi'
     end
  1: begin
     nc=8
     sensor='Lo'
     end
  else: begin
     nc=0
     sensor=''
     end
endcase
return
end

pro read_sweeptab,swfile,snum,st
; read in sweep table
; INPUTS
;  swfile - sweeptable filename
;  snum - 0 for hi, 1 for lo
; OUTPUTS
;  st - structure with sweep table records
;;;;;;;;;;;
set_sensor,snum,nc,sensor
if nc eq 0 then begin
  print,'Bad sensor number'
  return
endif

sw0={t0:0d,t1:0d,swmap:intarr(nc)}
sw=sw0
isw=0
t0=0d & t1=0d & hilo='' & swc=intarr(nc)
in=''
openr,lu,swfile,/get
while not eof(lu) do begin 
  readf,lu,in & pp=strpos(in,sensor) 
  if strmid(in,0,1) ne '#' and pp ge 0 then begin 
    sw=[sw,sw[0]] 
    isw++ 
    reads,strmid(in,0,pp),t0,t1 
    reads,strmid(in,pp+2),swc
    sw[isw].t0=t0
    sw[isw].t1=t1
    sw[isw].swmap=swc
  endif 
endwhile  
free_lun,lu
if isw gt 0 then st=sw[1:*]
return
end

pro sweepmapper,gtin,swfile,snum,gtout,status,trim=trim
; restep a good times file
; INPUTS
;  gtin - name of file to restep
;  swfile - sweep file
;  snum - 0 for hi, 1 for lo
; OUTPUTS
;  gtout - output good times
;  status - return zero if things are OK
; KEYWORDS
;  trim - if set, don't repeat comments
; ;;;;;;;;;;;
status=1
set_sensor,snum,nc,sensor
if nc eq 0 then begin
  print,'Bad sensor number'
  return
endif

read_sweeptab,swfile,snum,st
if size(st,/type) ne 8 then begin
  print,'read_sweeptab: bad sweeptable file: '+swfile
  return
endif

orb=0 & t0=0d & t1=0d & a0=0 & a1=0 & gtrec=intarr(nc)
prec=0
in=''
openr,lu,gtin,/get
openw,lo,gtout,/get
while not eof(lu) do begin 
  readf,lu,in
  pp=strpos(in,sensor) 
  if strmid(in,0,1) eq '#' then begin
     if not keyword_set(trim) then printf,lo,in 
  endif else begin
    if pp ge 0 then begin
      reads,strmid(in,0,pp),orb,t0,t1,a0,a1 
      reads,strmid(in,pp+2),gtrec
      prec++
      stmap=get_stepmap(st,t0,t1)
      newgt=gtrec
      if stmap[0] lt 0 then err++ else newgt=step_remap(gtrec,stmap)
      printf,lo,strmid(in,0,pp+2),string(newgt,form='(i1)')
    endif
  endelse 
endwhile  
free_lun,lu
free_lun,lo
if prec gt 0 then status=0
return
end
