function compare_fc_files,f1,f2,m1,m2,threshold=threshold
; Compare two flux_calculate style files and conclude wheather 
; they are the same (or not). If they are the same, return 0, 
;  if not, return 1. Can be used for any file with columns
;  of numbers with comment character '#'.
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
;  original 9/22/2010, DeMajistre 

if not keyword_set(threshold) then threshold=1.e-5

fi1=file_info(f1)
fi2=file_info(f2)
if fi1.read ne 1 then print,f1+'Cannot be read'
if fi2.read ne 1 then print,f2+'Cannot be read'
if fi1.read+fi2.read ne 2 then return,1


s1=read_ascii(f1,comment='#')
s2=read_ascii(f2,comment='#')

m1=s1.field1
m2=s2.field1

ret=0
; map check
avg_m=(abs(m1)+abs(m2))*.5
ii=where(avg_m gt 0)
if ii[0] ge 0 then begin
  mapmax=max( abs(m1[ii]-m2[ii])/avg_m[ii]   )
  if mapmax gt threshold then ret=1
endif

return,ret
end

