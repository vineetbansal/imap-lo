;
; $Id: make_me_bin_overlay.pro 18281 2024-04-29 16:53:31Z ibexops $
;
; pro make_me_bin_overlay
; pro make_me_bin_overline
; pro transform_ra_dec_arrays
; pro branch_cut_ra
; pro make_me_bin_std_hs
; pro altframe_gline
;
; A general procedure to drop a labelled bullet w/label onto a plot.
;
pro make_me_bin_overlay,         $
	ips,                     $ ; IN: common isoc plotting structure
	label,                   $ ; IN: array of labels
	ra,                      $ ; IN: array of ra values
	dec,                     $ ; IN: array of dec values
	color                      ; IN; array of color indices 0..4

	; smaller text size
	font_sizing_delta,ips,ips.mapgridfsd

	; Make a vector of 16 points, A[i] = 2pi/16:  
	; and thence to a symbol to be used if psym=8 or -8
	A = FINDGEN(17) * (!PI*2/16.)
	USERSYM, 0.5*COS(A), 0.5*SIN(A), /FILL
	ofx = ips.mapoffsetx	; offset?
	ofy = ips.mapoffsety	; offset?

	n = n_elements(label)
	for i=0,n-1 do begin
	    y = dec[i]
	    x = ra[i] ; if (x > 180) then x -= 360
	    ; 0..4 map colors are not available
	    if (color[i] lt 5) then clr=ips.fg[color[i]] else clr=color[i]
            if (color[i] eq 999) then clr=fsc_color(ips.fgcname) 
	    oplot,  [ x ], [ y ], psym=8, color=clr
	    xyouts, x+ofx, y+ofy, label[i], color=clr
	endfor

	; restore text size
	font_sizing_delta,ips,0
end

;
; Same thing, just connect the points.
; With a non-blank label, drop that on the end.
;
pro make_me_bin_overline,        $
	ips,                     $ ; IN: common isoc plotting structure
	label,                   $ ; IN: label
	ra,                      $ ; IN: array of ra values
	dec,                     $ ; IN: array of dec values
	clr                        ; IN; color index (0..4 are fg)

	if (clr lt 5) then clr=ips.fg[clr]

	if (label ne '') then begin
	    ofx = ips.mapoffsetx	; offset?
	    ofy = ips.mapoffsety	; offset?
	    font_sizing_delta,ips,ips.mapgridfsd
	    xyouts,ra[0]+ofx,dec[0]+ofy,label,color=clr
	    font_sizing_delta,ips,0
	endif

	plots, ra, dec, color=clr, $
	    thick=ips.mapgridllt,linestyle=ips.mapgridlls
end

;
; spawn ibex_rotate repeatedly on a list of ra dec pairs
; it is assumed there are as many dec's as there are ra's.
;
pro transform_ra_dec_arrays,     $
	ips,                     $ ; IN: common isoc plotting structure
	ra,                      $ ; IN/OUT: array of ra values
	dec                        ; IN/OUT: array of dec values

	n = n_elements(ra)

	if (ips.mapframe ne 'J2000') then begin
	  for i=0,n-1 do begin
	    args= ['ibex_rotate',			$
		'-r',string(ra[i]),'-d',string(dec[i]),	$
		'-f',ips.mapframe,'-t','+0s']
	    ; print,i,args
	    spawn,args,result,error,/noshell,/null_stdin
	    ; print,i,result
	    words=strsplit(result,' ',/extract)
	    ra[i] = double(words[0])
	    dec[i] = double(words[1])
	    ; print,''
	  endfor
	endif
end

;
; sometimes you want it at 360, sometimes 180
; ra is an array and we do a [min,max) at both ends, j.i.c.
;
pro branch_cut_ra,ra,min,max
	branch = where(ra ge max, count)
	if (count gt 0) then ra[branch] -= 360
	branch = where(ra lt min, count)
	if (count gt 0) then ra[branch] += 360
end

;
; round up the usual suspects for the heliosphere
;
pro make_me_bin_std_hs,          $
 	ips,                     $ ; IN: common isoc plotting structure
	label,                   $ ; OUT: array of labels
	ra,                      $ ; OUT: array of ra values
	dec,                     $ ; OUT: array of dec values
	color                      ; OUT; array of color indices 0..4

	label = strarr(4)
	ra    = dblarr(4)
	dec   = dblarr(4)
	color = intarr(4)	; zero by default
	color = replicate(0, 4)	; if we wanted other than zero

	label[0] = "Nose"
	label[1] = "V1"
	label[2] = "V2"
	label[3] = "Tail"

	ra[0] = +255.042495
	ra[1] = +257.888590
	ra[2] = +300.352598
	ra[3] = +75.042495

	dec[0] = -17.599851
	dec[1] = +12.168353
	dec[2] = -56.971462
	dec[3] = +17.599851

	; transform to requested SPICE frame using ibex_rotate and spawn
	if (ips.mapframe ne 'J2000') then begin
	  transform_ra_dec_arrays,ips,ra,dec
	endif
end


;
; round up the usual suspects for the heliosphere
;
pro make_me_bin_new_hs,          $
	ips,                     $ ; IN: common isoc plotting structure
	label,                   $ ; OUT: array of labels
	ra,                      $ ; OUT: array of ra values
	dec,                     $ ; OUT: array of dec values
	color                      ; OUT; array of color indices 0..4

	label = strarr(8)
	ra    = dblarr(8)
	dec   = dblarr(8)
	color = intarr(8)	; zero by default
	color = replicate(0, 8)	; if we wanted other than zero

	label[0] = "Upwind (HEL)"
	label[1] = "V1"
	label[2] = "V2"
	label[3] = "Downwind (HEL)"
	label[4] = "Upfield" ; field based on 221,39 (ECLIP COORDS) dir
	label[5] = "Downfield"
        label[6] = "Upwind (LSR)"
        label[7] = "Downwind (LSR)"
   
; Bzowski values .. 
	ra[0] = 258.69
;        ra[0] = 254.7
	ra[1] = +257.888590
	ra[2] = +300.352598
	ra[3] = 78.69
        ra[4] = 230.76
        ra[5] = 50.76
        ra[6] = 237.3
        ra[7] = 57.3 

	dec[0] = -17.9
	dec[1] = +12.168353
	dec[2] = -56.971462
	dec[3] = 17.9
        dec[4] = 22.0
        dec[5] = -22.0
        dec[6] = -62.5
        dec[7] = 62.5

	; transform to requested SPICE frame using ibex_rotate and spawn
	if (ips.mapframe ne 'J2000') then begin
	  transform_ra_dec_arrays,ips,ra,dec
	endif
end


;
; Something to generate a set of points that can be passed to
; make_me_bin_overline to draw a grid line from some other frame
; on our selected ips.mapframe.
;
; Modified 6/3/2010 by RD to allow for relocation of 
;      working file and to make the name more unique

pro altframe_gline,              $
	ips,                     $ ; IN: common isoc plotting structure
	ras,dra,                 $ ; IN: RA start, delta
	decs,ddec,               $ ; IN: Dec start, delta
	aframe,                  $ ; IN: alternate frame
	ra,                      $ ; OUT: array of ra values
	dec,                     $ ; OUT: array of dec values
	tmpfile=tmpfile           ; Name of temporary working file

	if (ddec le 0 and dra le 0) then return
        if not keyword_set(tmpfile) then $
          tmpfile='/tmp/IDLsuxReallyBadly_'+ $
               strcompress(string(long(systime(1))),/rem)

	if (ddec gt 0) then begin
	    n = round(360 / ddec)
	    ra = fltarr(n+1)
	    dec = fltarr(n+1)
	    for i=0,n do begin
		ra[i]  = ras
		dec[i] = decs + i*ddec
	    endfor
	endif
	if (dra gt 0) then begin
	    n = round(360 / dra);
	    ra = fltarr(n+1)
	    dec = fltarr(n+1)
	    for i=0,n do begin
		ra[i]  = ras + i*dra
		dec[i] = decs
	    endfor
	endif

	; spawn doesn't do i/o very well, apparently.
	; so we'll use a temporary file
        ; RD
        ; first make sure we have a fresh file, file names are ugly but 
        ; should be unique unless we have extreme pathology
        ; RD
        tfile=tmpfile
        finfo=file_info(tfile)
        ic=0
        while finfo.exists and ic lt 20 do begin
           tfile=tmpfile+'_'+string(ic++,format='(i2.2)')
           finfo=file_info(tfile)
       endwhile
       if finfo.exists then begin
           print,'altframe_gline: could not build temporary file'
           return
       endif


	openw,lun,tfile,/get
	for i=0,n do begin
	    printf,lun,ra[i],dec[i],0
	endfor
	free_lun,lun

	args= ['ibex_rotate', '-F',aframe, '-f',ips.mapframe, $
	       '-t','-+'+tfile]
	spawn,args,result,error,/noshell,/null_stdin
	file_delete,tfile

	nr = n_elements(result)
	for i=0,nr-1 do begin
	    words=strsplit(result[i],' ',/extract)
	    ra[i] = double(words[0])
	    dec[i] = double(words[1])
	    ; print,ra[i],dec[i]
	endfor
end

;
; eof
;
