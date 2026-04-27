pro read_fcov,fname,fcov
; read in an fcov file
; INPUTS:
;   fname - fulle covariance filename
; OUTPUTS
;   fcov - structure with FCOV information read in
; DeMajistre 10/10
;

str=''
openr,lu,fname,/get

;header count line
readf,lu,str
cnts=fix(STRSPLIT(strmid(Str,1),':', /EXTRACT))
headver=cnts[0]
nhead=cnts[1]
ncom= cnts[2]
nfil= cnts[3]
ndat= cnts[4]
repn= cnts[5]
dim = cnts[6]
nel = cnts[7]

;timestamp
readf,lu,str
readf,lu,str
timestamp=strmid(Str,1)

;agent
readf,lu,str
readf,lu,str
agent=strmid(Str,1)

;element counts
elcnts=intarr(ndat)
readf,lu,str
readf,lu,str
readf,lu,str
reads,strmid(str,1),elcnts

;files
readf,lu,str
if nfil gt 0 then begin
  files=strarr(nfil)
  for ic=0,nfil-1 do begin
    readf,lu,str
    files[ic]=strmid(str,1)
  endfor
endif

;comments
readf,lu,str
if nfil gt 0 then begin
  comments=strarr(ncom)
  for ic=0,ncom-1 do begin
    readf,lu,str
    comments[ic]=strmid(str,1)
  endfor
endif

; now the covariances
hasdata=where(elcnts gt 0)
packsize=elcnts[hasdata[0]]
nfull=n_elements(hasdata)

covpack=fltarr(packsize,nfull)
readf,lu,covpack
free_lun,lu

; full matrices
covmat=fltarr(dim,dim,nfull)

case packsize of
  ((dim)*(dim+1))/2: begin  ;this is full matrix
     i=0
     for ic=0,dim-1 do begin 
         covmat[ic:*,ic,*]=reform(covpack[i:i+(dim-ic)-1,*],dim-ic,1,nfull)
         i=i+(dim-ic)
     endfor
     for ic=0,dim-1 do covmat[ic,ic:*,*]=covmat[ic:*,ic,*]
  end

  dim: for ic=0,dim-1 do covmat[ic,ic,*]=covpack[ic,*] ;diagonal
endcase


;variances
var=fltarr(dim,nfull)
for ic=0,dim-1 do var[ic,*]=covmat[ic,ic,*]

fcov={fname:fname,timestamp:timestamp,agent:agent,elcnts:elcnts, $
      files:files,comments:comments,covpack:covpack,covmat:covmat,var:var}
      
return
end
