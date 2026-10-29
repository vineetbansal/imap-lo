pro kwproc,kwstring,kwstruct
; Simple parse of string with keyword=value syntax. keyword=value
; pairs. If no value is present a value of '1' is assigned
; INPUT
;   kwstring - string to be parsed - should be a set of semicoln (";") 
;              separated keyword=value statements. All values 
;               are considered to be strings.
; OUTPUT
;   kwstruct - structure array, one element/pair, with the following 
;              definition kwstruct0={keyword:'',value:''}. Note 
;              that all keywords are forced to lowercase
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

kwstruct0={keyword:'',value:''}

len=strlen(kwstring)

if len le 0 then begin
    kwstruct=kwstruct0
    return  ; empty string
endif

str=kwstring
finished=0

repeat begin
   ip1=strpos(str,';')
   if ip1 eq -1 then begin
        ip1=strlen(str)
        finished=1
   endif
   pairstr=strmid(str,0,ip1)
   eq1p=strpos(pairstr,'=')
   kw=kwstruct0
   if eq1p eq -1 then begin
      kw.keyword=strlowcase(pairstr)
      kw.value='1'
   endif else begin
      kw.keyword=strlowcase(strmid(pairstr,0,eq1p))
      kw.value=strmid(pairstr,eq1p+1)
   endelse
   if size(kwstruct,/type) ne 8 then begin ;first time through
      kwstruct=kw
   endif else kwstruct=[kwstruct,kw]
   str=strmid(str,ip1+1)
endrep until finished ne 0

return
end


