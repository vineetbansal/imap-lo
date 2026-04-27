function compare_me_bin_maps,f1,f2,threshold=threshold
; Compare two me_bin style maps and conclude wheather they are the same
; (or not). If they are the same, return 0, if not, return 1.
;  No header comparison is made. The metric for comparison is
;    abs((map1-map2)/((abs(map1)+ abs(map2))*.5))
;  if (abs(map1)+abs(map2)) ==0, then we call this a match.
;  otherwise we look to see whether the maximum value of the metric exceeds the
;  given threshold
;INPUTS
;  f1,f2 - input me_bin style file names
;RETURNS 0 if files match, 1 if not
;KEYWORDS
;  threshold - threshold for calling it a match. 
;
; HISTORY
;  original 9/17/2010, DeMajistre 

if not keyword_set(threshold) then threshold=1.e-5

fi1=file_info(f1)
fi2=file_info(f2)
if fi1.read ne 1 then print,f1+'Cannot be read'
if fi2.read ne 1 then print,f2+'Cannot be read'
if fi1.read+fi2.read ne 2 then return,1


read_me_bin_map,f1,m1,x1,y1
read_me_bin_map,f2,m2,x2,y2

ret=0
; map check
avg_m=(abs(m1)+abs(m2))*.5
ii=where(avg_m gt 0)
if ii[0] ge 0 then begin
  mapmax=max( abs(m1[ii]-m2[ii])/avg_m[ii]   )
  if mapmax gt threshold then ret=1
endif

v1=[x1,y1]
v2=[x2,y2]
avg_v=(abs(v1)+abs(v2))*.5
jj=where(avg_v gt 0)
if jj[0] ge 0 then begin
  vmax=max( abs(v1[jj]-v2[jj])/avg_v[jj]   )
  if vmax gt threshold then ret=1
endif

return,ret
end

